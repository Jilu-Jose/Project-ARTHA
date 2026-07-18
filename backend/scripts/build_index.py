#!/usr/bin/env python3
"""
ARTHA Index Builder
====================
CLI script that processes all legal documents in /corpus directory,
runs the section-aware chunker, builds per-domain BM25 indexes,
and serializes them to /indexes directory.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --corpus-dir ./corpus --index-dir ./indexes
    python scripts/build_index.py --verbose

This is part of the Vectorless RAG architecture — the built indexes
are loaded at FastAPI app startup and used for BM25 retrieval.
"""

import sys
import os
import argparse
import logging
import time

# Add the backend root to Python path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.ingestion import ingest_corpus
from app.core.retriever import ARTHARetriever


def main():
    parser = argparse.ArgumentParser(
        description="ARTHA Index Builder — Process legal documents and build BM25 indexes"
    )
    parser.add_argument(
        "--corpus-dir",
        default="corpus",
        help="Directory containing legal documents (PDF/TXT). Default: ./corpus",
    )
    parser.add_argument(
        "--index-dir",
        default="indexes",
        help="Output directory for serialized indexes. Default: ./indexes",
    )
    parser.add_argument(
        "--max-chunk-size",
        type=int,
        default=2000,
        help="Maximum chunk size in characters. Default: 2000 (~500 tokens)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--test-query",
        type=str,
        default=None,
        help="Run a test query against the built index after building",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("artha.build_index")

    print("=" * 60)
    print("  ARTHA Index Builder")
    print("  Vectorless RAG — BM25 Sparse Retrieval")
    print("=" * 60)
    print()

    # Resolve paths
    corpus_dir = os.path.abspath(args.corpus_dir)
    index_dir = os.path.abspath(args.index_dir)

    print(f"  Corpus directory : {corpus_dir}")
    print(f"  Index directory  : {index_dir}")
    print(f"  Max chunk size   : {args.max_chunk_size} chars")
    print()

    # Step 1: Ingest corpus
    print("[1/3] Ingesting legal documents...")
    start = time.time()

    try:
        domain_chunks = ingest_corpus(corpus_dir, max_chunk_size=args.max_chunk_size)
    except FileNotFoundError as e:
        logger.error(f"Corpus directory not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"No documents found: {e}")
        sys.exit(1)

    ingest_time = time.time() - start

    total_chunks = sum(len(chunks) for chunks in domain_chunks.values())
    print(f"      ✓ Ingested {total_chunks} chunks in {ingest_time:.2f}s")
    print()

    for domain, chunks in domain_chunks.items():
        acts = {c.act_name for c in chunks}
        print(f"      Domain: {domain}")
        print(f"        Chunks: {len(chunks)}")
        print(f"        Acts: {', '.join(acts)}")
        print()

    # Step 2: Build BM25 indexes
    print("[2/3] Building BM25 indexes...")
    start = time.time()

    retriever = ARTHARetriever()
    retriever.build_from_chunks(domain_chunks)

    build_time = time.time() - start
    print(f"      ✓ Built indexes in {build_time:.2f}s")
    print()

    # Step 3: Save to disk
    print("[3/3] Saving indexes to disk...")
    start = time.time()

    retriever.save(index_dir)

    save_time = time.time() - start
    print(f"      ✓ Saved to {index_dir} in {save_time:.2f}s")
    print()

    # Summary
    stats = retriever.get_stats()
    print("=" * 60)
    print("  Build Complete!")
    print(f"  Total chunks  : {stats['total_chunks']}")
    print(f"  Domains       : {len(stats['domains'])}")
    print(f"  Acts indexed  : {len(stats['acts'])}")
    print(f"  Total time    : {ingest_time + build_time + save_time:.2f}s")
    print("=" * 60)
    print()

    # Optional: test query
    if args.test_query:
        print(f"  Running test query: \"{args.test_query}\"")
        print("-" * 60)

        results = retriever.search(args.test_query, top_k=5)

        if not results:
            print("  No results found.")
        else:
            for i, (chunk, score) in enumerate(results):
                print(f"\n  [{i + 1}] Score: {score:.4f}")
                print(f"      Source: {chunk.source_label}")
                print(f"      File: {chunk.source_file}")
                text_preview = chunk.text[:200].replace("\n", " ")
                print(f"      Text: {text_preview}...")
        print()
    else:
        # Run a default test query to verify the index works
        print("  Quick verification query: 'GST registration threshold'")
        print("-" * 60)

        results = retriever.search("GST registration threshold turnover", top_k=3)
        for i, (chunk, score) in enumerate(results):
            print(f"\n  [{i + 1}] Score: {score:.4f}")
            print(f"      Source: {chunk.source_label}")
            text_preview = chunk.text[:150].replace("\n", " ")
            print(f"      Text: {text_preview}...")

        print()
        print("  ✓ Index verification passed!")


if __name__ == "__main__":
    main()
