"""
ARTHA BM25 Retriever
=====================
The heart of the Vectorless RAG architecture.

Uses BM25Okapi (a classical TF-IDF variant) for sparse retrieval over
section-chunked Indian legal documents. BM25 scores documents by term
frequency and inverse document frequency — excelling at legal text where
exact statutory phrasing is the signal.

Architecture choice rationale:
- Semantic embeddings MISS exact statutory phrasing ("Sub-section 3 as
  defined under clause 4(b)" has no semantic neighbor)
- BM25 directly matches the exact legal terminology founders search for
- No embedding model API costs or GPU overhead
- No vector database to maintain or re-index
- Simpler, faster, and more precise for the legal domain

Explicitly excluded: FAISS, ChromaDB, Pinecone, sentence-transformers,
LangChain, LangGraph, HuggingFace transformers. This is deliberate.
"""

import os
import json
import pickle
import logging
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.core.chunker import Chunk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stopwords for Indian legal text preprocessing
# ---------------------------------------------------------------------------
LEGAL_STOPWORDS = {
    "the", "of", "and", "to", "in", "a", "is", "that", "for", "it",
    "with", "as", "on", "at", "by", "an", "be", "this", "which",
    "or", "from", "are", "was", "were", "been", "being", "have",
    "has", "had", "do", "does", "did", "but", "not", "no", "nor",
    "so", "if", "than", "too", "very", "can", "will", "just",
    "shall", "should", "may", "its", "he", "she", "they", "them",
    "their", "his", "her", "who", "whom", "what", "where", "when",
    "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "only", "own", "same", "into", "over",
    "after", "before", "between", "under", "above", "below",
    "up", "down", "out", "off", "then", "once", "here", "there",
    "any", "about", "through", "during", "also", "would", "could",
}


def preprocess_query(text: str) -> List[str]:
    """
    Preprocess text for BM25 scoring.
    - Lowercase
    - Remove punctuation (but keep hyphens and legal markers)
    - Tokenize by whitespace
    - Remove stopwords

    Note: rank_bm25 does NOT do any preprocessing itself — this is
    critical because BM25 performs exact token matching.
    """
    text = text.lower()
    # Keep alphanumeric, hyphens, and parentheses (for legal references like "4(b)")
    text = re.sub(r"[^\w\s\-\(\)]", " ", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in LEGAL_STOPWORDS and len(t) > 1]
    return tokens


class DomainIndex:
    """
    A BM25 index for a single legal domain (e.g., corporate, tax).
    Holds the BM25Okapi instance and the corresponding chunk metadata.
    """

    def __init__(self, domain: str, chunks: List[Chunk]):
        self.domain = domain
        self.chunks = chunks

        # Tokenize all chunks for BM25
        self.tokenized_corpus = [
            preprocess_query(chunk.text) for chunk in chunks
        ]

        # Build BM25 index
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.bm25 = None

        logger.info(
            f"Built BM25 index for domain '{domain}': "
            f"{len(chunks)} chunks indexed"
        )

    def search(
        self,
        query_tokens: List[str],
        top_k: int = 15,
    ) -> List[Tuple[Chunk, float]]:
        """
        Search this domain's index for relevant chunks.

        Returns list of (chunk, bm25_score) tuples, sorted by score descending.
        """
        if not self.bm25 or not self.chunks:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Pair chunks with scores and sort
        scored = list(zip(self.chunks, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        # Return top_k with non-zero scores
        return [(chunk, score) for chunk, score in scored[:top_k] if score > 0]


class ARTHARetriever:
    """
    Multi-domain BM25 retriever for the ARTHA platform.

    Maintains separate BM25 indexes per legal domain (corporate, tax,
    securities, startup_schemes), enabling both cross-domain and
    domain-filtered search.

    This is the core retrieval component of the Vectorless RAG architecture.
    """

    def __init__(self):
        self.domain_indexes: Dict[str, DomainIndex] = {}
        self.all_chunks: List[Chunk] = []
        self._global_index: Optional[DomainIndex] = None

    def build_from_chunks(self, domain_chunks: Dict[str, List[Chunk]]) -> None:
        """
        Build domain-sharded BM25 indexes from grouped chunks.

        Args:
            domain_chunks: Dict mapping domain name to list of chunks
        """
        self.all_chunks = []

        for domain, chunks in domain_chunks.items():
            self.domain_indexes[domain] = DomainIndex(domain, chunks)
            self.all_chunks.extend(chunks)

        # Also build a global index for unfiltered search
        if self.all_chunks:
            self._global_index = DomainIndex("_global", self.all_chunks)

        total = sum(len(idx.chunks) for idx in self.domain_indexes.values())
        logger.info(
            f"ARTHARetriever ready: {total} total chunks across "
            f"{len(self.domain_indexes)} domains"
        )

    def search(
        self,
        query: str,
        top_k: int = 15,
        domain_filters: Optional[List[str]] = None,
    ) -> List[Tuple[Chunk, float]]:
        """
        Search the corpus for chunks relevant to the query.

        Args:
            query: User's search query
            top_k: Number of chunks to retrieve
            domain_filters: Optional list of domains to restrict search
                           (e.g., ["corporate", "tax"])

        Returns:
            List of (chunk, bm25_score) tuples, sorted by score descending
        """
        query_tokens = preprocess_query(query)

        if not query_tokens:
            logger.warning(f"Empty query after preprocessing: '{query}'")
            return []

        if domain_filters:
            # Search only specified domains
            results: List[Tuple[Chunk, float]] = []
            for domain in domain_filters:
                if domain in self.domain_indexes:
                    results.extend(
                        self.domain_indexes[domain].search(query_tokens, top_k)
                    )
                else:
                    logger.warning(f"Unknown domain filter: '{domain}'")

            # Re-sort combined results and take top_k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        else:
            # Search global index
            if self._global_index:
                return self._global_index.search(query_tokens, top_k)
            return []

    def get_chunk_by_index(self, chunk_index: int) -> Optional[Chunk]:
        """Retrieve a specific chunk by its global index."""
        for chunk in self.all_chunks:
            if chunk.chunk_index == chunk_index:
                return chunk
        return None

    def get_available_domains(self) -> List[str]:
        """List all indexed domains."""
        return list(self.domain_indexes.keys())

    def get_stats(self) -> Dict:
        """Get retriever statistics."""
        return {
            "total_chunks": len(self.all_chunks),
            "domains": {
                domain: len(idx.chunks)
                for domain, idx in self.domain_indexes.items()
            },
            "acts": list({
                chunk.act_name for chunk in self.all_chunks
            }),
        }

    # --- Serialization ---

    def save(self, index_dir: str) -> None:
        """
        Serialize the retriever to disk.
        Saves chunk data as JSON and BM25 indexes as pickle.
        """
        os.makedirs(index_dir, exist_ok=True)

        # Save chunk data per domain
        for domain, index in self.domain_indexes.items():
            chunk_path = os.path.join(index_dir, f"{domain}_chunks.json")
            chunk_data = [chunk.to_dict() for chunk in index.chunks]
            with open(chunk_path, "w", encoding="utf-8") as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)

            # Save BM25 index as pickle (includes IDF weights, etc.)
            if index.bm25:
                bm25_path = os.path.join(index_dir, f"{domain}_bm25.pkl")
                with open(bm25_path, "wb") as f:
                    pickle.dump(index.bm25, f)

        # Save metadata
        meta = {
            "domains": list(self.domain_indexes.keys()),
            "total_chunks": len(self.all_chunks),
            "stats": self.get_stats(),
        }
        meta_path = os.path.join(index_dir, "index_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        logger.info(f"Saved retriever indexes to {index_dir}")

    @classmethod
    def load(cls, index_dir: str) -> "ARTHARetriever":
        """
        Load a serialized retriever from disk.
        """
        retriever = cls()
        index_path = Path(index_dir)

        if not index_path.exists():
            raise FileNotFoundError(f"Index directory not found: {index_dir}")

        # Load metadata
        meta_path = index_path / "index_meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Index metadata not found: {meta_path}")

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        domain_chunks: Dict[str, List[Chunk]] = {}

        for domain in meta["domains"]:
            chunk_path = index_path / f"{domain}_chunks.json"
            if not chunk_path.exists():
                logger.warning(f"Chunk file not found for domain '{domain}'")
                continue

            with open(chunk_path, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)

            chunks = []
            for item in chunk_data:
                sub_secs = item.pop("sub_sections", [])
                chunk = Chunk(**item)
                chunk.sub_sections = sub_secs
                chunks.append(chunk)

            domain_chunks[domain] = chunks

            # Try to load pre-built BM25 index for faster startup
            bm25_path = index_path / f"{domain}_bm25.pkl"
            if bm25_path.exists():
                try:
                    with open(bm25_path, "rb") as f:
                        bm25 = pickle.load(f)
                    # Build DomainIndex with pre-loaded BM25
                    idx = DomainIndex.__new__(DomainIndex)
                    idx.domain = domain
                    idx.chunks = chunks
                    idx.tokenized_corpus = [
                        preprocess_query(c.text) for c in chunks
                    ]
                    idx.bm25 = bm25
                    retriever.domain_indexes[domain] = idx
                    retriever.all_chunks.extend(chunks)
                    logger.info(f"Loaded pre-built BM25 index for '{domain}'")
                    continue
                except Exception as e:
                    logger.warning(
                        f"Failed to load BM25 pickle for '{domain}', rebuilding: {e}"
                    )

            domain_chunks[domain] = chunks

        # Build indexes for any domains that didn't have cached BM25
        remaining = {
            d: c for d, c in domain_chunks.items()
            if d not in retriever.domain_indexes
        }
        if remaining:
            retriever.build_from_chunks(remaining)

        # Rebuild global index
        retriever.all_chunks = []
        for idx in retriever.domain_indexes.values():
            retriever.all_chunks.extend(idx.chunks)
        if retriever.all_chunks:
            retriever._global_index = DomainIndex("_global", retriever.all_chunks)

        logger.info(
            f"Loaded retriever from {index_dir}: "
            f"{len(retriever.all_chunks)} chunks, "
            f"{len(retriever.domain_indexes)} domains"
        )
        return retriever
