"""
ARTHA Ingestion Pipeline
=========================
Parses PDF legal documents using PyMuPDF, preserving page numbers,
then feeds text through the section-aware chunker.

Also handles plain text (.txt) files for development/testing with
sample legal content.

Part of the Vectorless RAG architecture — this pipeline produces
structured chunks that go directly into BM25 indexing. No embeddings,
no vector representations, no HuggingFace models.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from app.core.chunker import Chunk, chunk_document, detect_domain

logger = logging.getLogger(__name__)

# Map of known filenames to act names
KNOWN_ACTS: Dict[str, str] = {
    "companies_act": "Companies Act, 2013",
    "gst_act": "GST (CGST) Act, 2017",
    "fema_act": "Foreign Exchange Management Act, 1999",
    "sebi_icdr": "SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018",
    "indian_partnership_act": "Indian Partnership Act, 1932",
    "startup_india_scheme": "Startup India Action Plan & DPIIT Notifications",
}


def _detect_act_name(filename: str, text_sample: str = "") -> str:
    """Detect the act name from filename or content."""
    name_lower = filename.lower().replace(".pdf", "").replace(".txt", "")

    for key, act_name in KNOWN_ACTS.items():
        if key in name_lower:
            return act_name

    # Fallback: try to extract from first few lines
    first_lines = text_sample[:500].strip()
    for line in first_lines.split("\n"):
        line = line.strip()
        if len(line) > 10 and line.upper() == line:
            # Looks like a title line
            return line.title()

    return filename.replace("_", " ").replace(".pdf", "").replace(".txt", "").title()


def parse_pdf(filepath: str) -> Tuple[str, Dict[int, int]]:
    """
    Extract text from a PDF using PyMuPDF, preserving page numbers.

    Returns:
        Tuple of (full_text, page_number_mapping)
        where page_number_mapping maps character positions to page numbers.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for PDF parsing. Install it with: pip install PyMuPDF"
        )

    doc = fitz.open(filepath)
    full_text = ""
    page_numbers: Dict[int, int] = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        # sort=True ensures natural reading order (top-left to bottom-right)
        page_text = page.get_text("text", sort=True)

        if page_text.strip():
            char_pos = len(full_text)
            page_numbers[char_pos] = page_num + 1  # 1-indexed
            full_text += page_text + "\n\n"

    doc.close()
    logger.info(f"Parsed PDF: {filepath} — {len(doc)} pages, {len(full_text)} characters")
    return full_text, page_numbers


def parse_text_file(filepath: str) -> Tuple[str, Dict[int, int]]:
    """
    Read a plain text file (for development/testing with sample corpus).

    Returns:
        Tuple of (full_text, empty_page_mapping)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Simple page mapping: every ~3000 chars = 1 "page"
    page_numbers: Dict[int, int] = {}
    page_size = 3000
    for i in range(0, len(text), page_size):
        page_numbers[i] = (i // page_size) + 1

    logger.info(f"Parsed text file: {filepath} — {len(text)} characters")
    return text, page_numbers


def ingest_document(
    filepath: str,
    act_name: Optional[str] = None,
    domain: Optional[str] = None,
    max_chunk_size: int = 2000,
) -> List[Chunk]:
    """
    Ingest a single legal document (PDF or text file) into chunks.

    Args:
        filepath: Path to the document file
        act_name: Override act name (auto-detected if None)
        domain: Override domain (auto-detected if None)
        max_chunk_size: Maximum chunk size in characters

    Returns:
        List of Chunk objects with full metadata
    """
    filepath = str(filepath)
    filename = os.path.basename(filepath)

    # Parse based on file type
    if filepath.lower().endswith(".pdf"):
        text, page_numbers = parse_pdf(filepath)
    elif filepath.lower().endswith((".txt", ".md")):
        text, page_numbers = parse_text_file(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}. Use .pdf or .txt")

    if not text.strip():
        logger.warning(f"Empty document: {filepath}")
        return []

    # Detect act name if not provided
    if act_name is None:
        act_name = _detect_act_name(filename, text)

    # Chunk the document
    chunks = chunk_document(
        text=text,
        act_name=act_name,
        source_file=filename,
        page_numbers=page_numbers,
        max_chunk_size=max_chunk_size,
        domain=domain,
    )

    logger.info(
        f"Ingested {filename}: {len(chunks)} chunks, "
        f"act='{act_name}', domain='{chunks[0].domain if chunks else 'unknown'}'"
    )
    return chunks


def ingest_corpus(
    corpus_dir: str,
    max_chunk_size: int = 2000,
) -> Dict[str, List[Chunk]]:
    """
    Ingest all documents from a corpus directory, grouped by domain.

    Args:
        corpus_dir: Path to directory containing legal documents
        max_chunk_size: Maximum chunk size in characters

    Returns:
        Dict mapping domain name to list of chunks
    """
    corpus_path = Path(corpus_dir)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    # Collect all document files
    doc_files = []
    for ext in ("*.pdf", "*.txt", "*.md"):
        doc_files.extend(corpus_path.glob(ext))

    if not doc_files:
        raise ValueError(f"No documents found in {corpus_dir}")

    logger.info(f"Found {len(doc_files)} documents in {corpus_dir}")

    # Ingest and group by domain
    domain_chunks: Dict[str, List[Chunk]] = {}

    for doc_file in sorted(doc_files):
        try:
            chunks = ingest_document(str(doc_file), max_chunk_size=max_chunk_size)
            for chunk in chunks:
                if chunk.domain not in domain_chunks:
                    domain_chunks[chunk.domain] = []
                domain_chunks[chunk.domain].append(chunk)
        except Exception as e:
            logger.error(f"Failed to ingest {doc_file}: {e}")
            continue

    total_chunks = sum(len(c) for c in domain_chunks.values())
    logger.info(
        f"Corpus ingestion complete: {total_chunks} total chunks across "
        f"{len(domain_chunks)} domains: {list(domain_chunks.keys())}"
    )
    return domain_chunks


def save_chunks_to_json(chunks: List[Chunk], output_path: str) -> None:
    """Serialize chunks to a JSON file for index building."""
    data = [chunk.to_dict() for chunk in chunks]
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(chunks)} chunks to {output_path}")


def load_chunks_from_json(input_path: str) -> List[Chunk]:
    """Deserialize chunks from a JSON file."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    chunks = []
    for item in data:
        # Handle sub_sections field
        sub_secs = item.pop("sub_sections", [])
        chunk = Chunk(**item)
        chunk.sub_sections = sub_secs
        chunks.append(chunk)
    return chunks
