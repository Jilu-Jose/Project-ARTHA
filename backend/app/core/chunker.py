"""
ARTHA Section-Aware Chunker
============================
Splits Indian legal documents into semantically meaningful chunks based on
structural markers (Section, Chapter, Sub-section, Clause, Rule, Schedule).

This is a key component of the Vectorless RAG architecture. Unlike semantic
chunking that relies on embeddings, this chunker uses regex patterns tailored
to Indian legal document conventions. BM25 then scores these chunks using
exact term frequency — critical for legal text where "Sub-section 3 as
defined under clause 4(b)" has no semantic neighbor but needs exact keyword match.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------------------
# Domain classification mapping
# ---------------------------------------------------------------------------
DOMAIN_MAPPING: Dict[str, str] = {
    "companies act": "corporate",
    "companies_act": "corporate",
    "llp act": "corporate",
    "limited liability partnership": "corporate",
    "partnership act": "corporate",
    "indian_partnership_act": "corporate",
    "gst": "tax",
    "goods and services tax": "tax",
    "cgst": "tax",
    "sgst": "tax",
    "igst": "tax",
    "income tax": "tax",
    "gst_act": "tax",
    "fema": "securities",
    "foreign exchange": "securities",
    "fema_act": "securities",
    "sebi": "securities",
    "securities": "securities",
    "icdr": "securities",
    "sebi_icdr": "securities",
    "startup india": "startup_schemes",
    "startup_india": "startup_schemes",
    "dpiit": "startup_schemes",
    "msme": "startup_schemes",
    "startup_india_scheme": "startup_schemes",
}

# ---------------------------------------------------------------------------
# Section boundary patterns for Indian legal documents
# ---------------------------------------------------------------------------
# These regex patterns detect structural markers commonly found in:
# - Companies Act, 2013
# - GST (CGST/SGST/IGST) Act, 2017
# - SEBI (ICDR) Regulations
# - FEMA, 1999
# - Indian Partnership Act, 1932
# - Various Government scheme notifications

SECTION_PATTERNS = [
    # "CHAPTER I", "CHAPTER XIV", "Chapter 3"
    re.compile(
        r"^(?:CHAPTER|Chapter)\s+([IVXLCDM]+|\d+)[\.\s\-—:]*(.*)$",
        re.MULTILINE,
    ),
    # "PART I", "Part II"
    re.compile(
        r"^(?:PART|Part)\s+([IVXLCDM]+|\d+)[\.\s\-—:]*(.*)$",
        re.MULTILINE,
    ),
    # "Section 2.", "SECTION 135", "Section 2(68)"
    re.compile(
        r"^(?:Section|SECTION|Sec\.?)\s*(\d+[A-Za-z]*)[\.\s\(\)]*(.*)$",
        re.MULTILINE,
    ),
    # "Rule 3", "RULE 46A"
    re.compile(
        r"^(?:Rule|RULE)\s*(\d+[A-Za-z]*)[\.\s\-—:]*(.*)$",
        re.MULTILINE,
    ),
    # "Regulation 3", "REGULATION 163"
    re.compile(
        r"^(?:Regulation|REGULATION)\s*(\d+[A-Za-z]*)[\.\s\-—:]*(.*)$",
        re.MULTILINE,
    ),
    # "Schedule I", "SCHEDULE VII"
    re.compile(
        r"^(?:SCHEDULE|Schedule)\s+([IVXLCDM]+|\d+)[\.\s\-—:]*(.*)$",
        re.MULTILINE,
    ),
    # "Article 12", "ARTICLE 19(1)(a)"
    re.compile(
        r"^(?:Article|ARTICLE)\s*(\d+[A-Za-z]*)[\.\s\(\)]*(.*)$",
        re.MULTILINE,
    ),
]

# Sub-section / clause patterns (used for finer-grained metadata, not splitting)
SUB_SECTION_PATTERN = re.compile(
    r"\((\d+)\)\s",  # "(1) The Board shall..."
)
CLAUSE_PATTERN = re.compile(
    r"\(([a-z])\)\s",  # "(a) every company..."
)


@dataclass
class Chunk:
    """A single chunk of legal text with full metadata."""
    text: str
    act_name: str
    section_number: str
    chapter: str
    page_number: int
    source_file: str
    domain: str
    chunk_index: int = 0
    sub_sections: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def source_label(self) -> str:
        """Human-readable source label for context injection."""
        parts = []
        if self.chapter:
            parts.append(f"Chapter {self.chapter}")
        if self.section_number:
            parts.append(f"Section {self.section_number}")
        parts.append(self.act_name)
        return ", ".join(parts)


def detect_domain(filename: str, text_sample: str = "") -> str:
    """
    Classify a document into a legal domain based on filename and content.
    Domains: corporate, tax, securities, startup_schemes
    """
    combined = f"{filename.lower()} {text_sample[:500].lower()}"
    for keyword, domain in DOMAIN_MAPPING.items():
        if keyword in combined:
            return domain
    return "corporate"  # default fallback


def _find_section_boundaries(text: str) -> List[Tuple[int, str, str, str]]:
    """
    Find all section boundaries in the text.
    Returns list of (position, marker_type, number, title).
    """
    boundaries = []

    for pattern in SECTION_PATTERNS:
        for match in pattern.finditer(text):
            start = match.start()
            number = match.group(1).strip()
            title = match.group(2).strip() if match.lastindex >= 2 else ""
            # Determine marker type from pattern
            match_text = match.group(0).upper()
            if "CHAPTER" in match_text:
                marker_type = "chapter"
            elif "PART" in match_text:
                marker_type = "part"
            elif "SECTION" in match_text or "SEC" in match_text:
                marker_type = "section"
            elif "RULE" in match_text:
                marker_type = "rule"
            elif "REGULATION" in match_text:
                marker_type = "regulation"
            elif "SCHEDULE" in match_text:
                marker_type = "schedule"
            elif "ARTICLE" in match_text:
                marker_type = "article"
            else:
                marker_type = "section"

            boundaries.append((start, marker_type, number, title))

    # Sort by position in text
    boundaries.sort(key=lambda x: x[0])
    return boundaries


def _extract_sub_sections(text: str) -> List[str]:
    """Extract sub-section numbers referenced in a chunk."""
    return SUB_SECTION_PATTERN.findall(text)


def chunk_document(
    text: str,
    act_name: str,
    source_file: str,
    page_numbers: Optional[Dict[int, int]] = None,
    max_chunk_size: int = 2000,
    overlap: int = 200,
    domain: Optional[str] = None,
) -> List[Chunk]:
    """
    Split a legal document into section-aware chunks.

    Strategy:
    1. Detect all section/chapter/rule boundaries via regex
    2. Split text at these boundaries
    3. If a section exceeds max_chunk_size, split further with overlap
    4. Each chunk carries full metadata for BM25 retrieval and citation

    Args:
        text: Full document text
        act_name: Name of the legal act (e.g., "Companies Act, 2013")
        source_file: Source filename
        page_numbers: Optional mapping of character positions to page numbers
        max_chunk_size: Max characters per chunk (default ~2000 chars ≈ ~500 tokens)
        overlap: Character overlap between sub-chunks when splitting large sections
        domain: Legal domain override (auto-detected if None)

    Returns:
        List of Chunk objects with full metadata
    """
    if domain is None:
        domain = detect_domain(source_file, text)

    boundaries = _find_section_boundaries(text)
    chunks: List[Chunk] = []
    current_chapter = ""
    chunk_index = 0

    if not boundaries:
        # No structural markers found — fall back to paragraph-based splitting
        return _chunk_by_paragraphs(
            text, act_name, source_file, domain, max_chunk_size, overlap
        )

    # Create segments between boundaries
    segments: List[Tuple[str, str, str, str]] = []  # (text, marker_type, number, chapter)
    for i, (pos, marker_type, number, title) in enumerate(boundaries):
        end_pos = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
        segment_text = text[pos:end_pos].strip()

        if marker_type == "chapter" or marker_type == "part":
            current_chapter = number
            # Include chapter header as its own segment if it has content
            if len(segment_text) > 50:
                segments.append((segment_text, marker_type, number, current_chapter))
        else:
            segments.append((segment_text, marker_type, number, current_chapter))

    for segment_text, marker_type, number, chapter in segments:
        # Determine page number from character position if available
        page_num = 1
        if page_numbers:
            for char_pos, pg in sorted(page_numbers.items()):
                if char_pos <= text.find(segment_text[:50]):
                    page_num = pg

        # Build section identifier
        if marker_type in ("section", "rule", "regulation", "article"):
            section_id = number
        elif marker_type == "schedule":
            section_id = f"Schedule {number}"
        else:
            section_id = f"{marker_type.title()} {number}"

        if len(segment_text) <= max_chunk_size:
            # Fits in one chunk
            chunks.append(Chunk(
                text=segment_text,
                act_name=act_name,
                section_number=section_id,
                chapter=chapter,
                page_number=page_num,
                source_file=source_file,
                domain=domain,
                chunk_index=chunk_index,
                sub_sections=_extract_sub_sections(segment_text),
            ))
            chunk_index += 1
        else:
            # Split large section into overlapping sub-chunks
            sub_chunks = _split_with_overlap(segment_text, max_chunk_size, overlap)
            for j, sub_text in enumerate(sub_chunks):
                chunks.append(Chunk(
                    text=sub_text,
                    act_name=act_name,
                    section_number=f"{section_id} (part {j + 1})",
                    chapter=chapter,
                    page_number=page_num,
                    source_file=source_file,
                    domain=domain,
                    chunk_index=chunk_index,
                    sub_sections=_extract_sub_sections(sub_text),
                ))
                chunk_index += 1

    return chunks


def _chunk_by_paragraphs(
    text: str,
    act_name: str,
    source_file: str,
    domain: str,
    max_chunk_size: int,
    overlap: int,
) -> List[Chunk]:
    """Fallback chunking by paragraph when no section markers are found."""
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: List[Chunk] = []
    current_text = ""
    chunk_index = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_text) + len(para) + 1 <= max_chunk_size:
            current_text += ("\n\n" + para) if current_text else para
        else:
            if current_text:
                chunks.append(Chunk(
                    text=current_text,
                    act_name=act_name,
                    section_number="",
                    chapter="",
                    page_number=1,
                    source_file=source_file,
                    domain=domain,
                    chunk_index=chunk_index,
                    sub_sections=_extract_sub_sections(current_text),
                ))
                chunk_index += 1
            current_text = para

    # Final chunk
    if current_text:
        chunks.append(Chunk(
            text=current_text,
            act_name=act_name,
            section_number="",
            chapter="",
            page_number=1,
            source_file=source_file,
            domain=domain,
            chunk_index=chunk_index,
            sub_sections=_extract_sub_sections(current_text),
        ))

    return chunks


def _split_with_overlap(text: str, max_size: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks, preferring sentence boundaries."""
    if len(text) <= max_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_size

        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        # Try to break at a sentence boundary (period followed by space/newline)
        search_zone = text[max(start + max_size - 300, start):end]
        last_period = search_zone.rfind(". ")
        if last_period == -1:
            last_period = search_zone.rfind(".\n")

        if last_period != -1:
            end = max(start + max_size - 300, start) + last_period + 1

        chunks.append(text[start:end].strip())
        start = end - overlap

    return chunks
