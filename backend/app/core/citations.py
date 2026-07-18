"""
ARTHA Citation Extractor
=========================
Parses the LLM's response to extract structured citation objects
and cross-references them against the original retrieved chunks.

The system prompt forces the LLM to cite as [Section X, Act Name].
This module extracts those citations, maps them back to source chunks,
and produces structured objects for the "Citation Deep-Dive" feature.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

from app.core.chunker import Chunk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Citation patterns
# ---------------------------------------------------------------------------
# Matches patterns like:
#   [Section 22, CGST Act, 2017]
#   [Section 2(68), Companies Act, 2013]
#   [Regulation 6, SEBI ICDR]
#   [Section 56(2)(viib), Income Tax Act]
#   [Rule 3, FEMA 20R]
CITATION_PATTERN = re.compile(
    r"\["
    r"((?:Section|Sec\.?|Regulation|Rule|Article|Schedule|Chapter)\s*"
    r"[\d]+[A-Za-z]*(?:\([^)]*\))*(?:\([^)]*\))*)"  # Section/Regulation + number + optional sub-sections
    r",?\s*"
    r"([^\]]+?)"  # Act name
    r"\]",
    re.IGNORECASE,
)

# Also match simpler patterns like [Section 22, GST Act]
SIMPLE_CITATION_PATTERN = re.compile(
    r"\["
    r"((?:Section|Sec\.?|Regulation|Rule|Article)\s*[\d]+[A-Za-z]*)"
    r",?\s*"
    r"([^\]]+?)"
    r"\]",
    re.IGNORECASE,
)


@dataclass
class Citation:
    """A structured citation extracted from the LLM response."""
    section: str          # e.g., "Section 22"
    act_name: str         # e.g., "CGST Act, 2017"
    source_file: str      # e.g., "gst_act.txt"
    chunk_text: str       # Full text of the matched chunk
    confidence: float     # Match confidence (0-1)
    chunk_index: int      # Index of the matched chunk

    def to_dict(self) -> Dict:
        return asdict(self)


def extract_citations(
    response_text: str,
    retrieved_chunks: Optional[List[Tuple[Chunk, float]]] = None,
) -> List[Citation]:
    """
    Extract citations from the LLM response and cross-reference
    against retrieved chunks.

    Args:
        response_text: The LLM's full response text
        retrieved_chunks: Original retrieved chunks for cross-referencing

    Returns:
        List of structured Citation objects
    """
    # Find all citation patterns
    raw_citations = _find_citation_patterns(response_text)

    if not raw_citations:
        logger.info("No citations found in response")
        return []

    logger.info(f"Found {len(raw_citations)} raw citations in response")

    # Deduplicate
    seen = set()
    unique_citations = []
    for section, act in raw_citations:
        key = (section.lower().strip(), act.lower().strip())
        if key not in seen:
            seen.add(key)
            unique_citations.append((section.strip(), act.strip()))

    # Cross-reference with retrieved chunks
    citations = []
    for section, act in unique_citations:
        matched_chunk, confidence = _match_citation_to_chunk(
            section, act, retrieved_chunks or []
        )

        citation = Citation(
            section=section,
            act_name=act,
            source_file=matched_chunk.source_file if matched_chunk else "",
            chunk_text=matched_chunk.text if matched_chunk else "",
            confidence=confidence,
            chunk_index=matched_chunk.chunk_index if matched_chunk else -1,
        )
        citations.append(citation)

    logger.info(
        f"Extracted {len(citations)} unique citations, "
        f"{sum(1 for c in citations if c.confidence > 0.5)} matched to chunks"
    )
    return citations


def _find_citation_patterns(text: str) -> List[Tuple[str, str]]:
    """Find all [Section X, Act Name] patterns in the text."""
    citations = []

    # Try detailed pattern first
    for match in CITATION_PATTERN.finditer(text):
        section = match.group(1).strip()
        act = match.group(2).strip()
        citations.append((section, act))

    # If no matches, try simpler pattern
    if not citations:
        for match in SIMPLE_CITATION_PATTERN.finditer(text):
            section = match.group(1).strip()
            act = match.group(2).strip()
            citations.append((section, act))

    return citations


def _match_citation_to_chunk(
    section: str,
    act_name: str,
    retrieved_chunks: List[Tuple[Chunk, float]],
) -> Tuple[Optional[Chunk], float]:
    """
    Match a citation to its source chunk from the retrieved set.

    Uses fuzzy matching on section number and act name to find
    the best matching chunk.

    Returns:
        Tuple of (matched_chunk, confidence_score)
    """
    if not retrieved_chunks:
        return None, 0.0

    # Extract section number from the citation
    section_num = _extract_section_number(section)
    act_lower = act_name.lower()

    best_match: Optional[Chunk] = None
    best_score = 0.0

    for chunk, bm25_score in retrieved_chunks:
        score = 0.0

        # Check act name match
        chunk_act_lower = chunk.act_name.lower()
        if _acts_match(act_lower, chunk_act_lower):
            score += 0.5

        # Check section number match
        if section_num and section_num in chunk.section_number:
            score += 0.4

        # Check if section text appears in chunk content
        if section.lower() in chunk.text.lower():
            score += 0.1

        if score > best_score:
            best_score = score
            best_match = chunk

    return best_match, best_score


def _extract_section_number(section_str: str) -> str:
    """Extract the numeric part from a section reference."""
    match = re.search(r"(\d+[A-Za-z]*(?:\([^)]*\))*)", section_str)
    return match.group(1) if match else ""


def _acts_match(citation_act: str, chunk_act: str) -> bool:
    """Check if two act name references refer to the same act."""
    # Normalize common abbreviations
    normalizations = {
        "cgst": "goods and services tax",
        "gst": "goods and services tax",
        "sgst": "goods and services tax",
        "igst": "goods and services tax",
        "fema": "foreign exchange management",
        "sebi icdr": "issue of capital and disclosure",
        "sebi": "securities and exchange board",
        "companies act": "companies act",
        "partnership act": "partnership act",
        "income tax": "income tax",
        "startup india": "startup india",
        "dpiit": "startup india",
    }

    for abbrev, full in normalizations.items():
        if abbrev in citation_act and (abbrev in chunk_act or full in chunk_act):
            return True
        if abbrev in chunk_act and (abbrev in citation_act or full in citation_act):
            return True

    # Direct substring match
    if citation_act in chunk_act or chunk_act in citation_act:
        return True

    # Check for significant word overlap
    citation_words = set(citation_act.split())
    chunk_words = set(chunk_act.split())
    common = citation_words & chunk_words
    if len(common) >= 2:
        return True

    return False


def format_citations_for_response(citations: List[Citation]) -> str:
    """
    Format citations as a readable section for API response.
    """
    if not citations:
        return ""

    parts = ["\n\n📚 **Sources Referenced:**\n"]
    for i, citation in enumerate(citations, 1):
        parts.append(
            f"{i}. **{citation.section}**, {citation.act_name}"
        )
        if citation.source_file:
            parts.append(f"   📄 Source: {citation.source_file}")

    return "\n".join(parts)
