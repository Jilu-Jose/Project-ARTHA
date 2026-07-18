"""
ARTHA Context Builder & Query Rewriter
========================================
Transforms BM25 retrieval results into a structured context string
for injection into Kimi K2.6's 256K context window.

Also implements query rewriting — a lightweight LLM call that converts
conversational user queries into legal-terminology search queries
before BM25 retrieval. This improves recall for colloquial questions
like "do I need to pay GST?" → "GST registration threshold turnover".

Part of the Vectorless RAG pipeline:
    User Query → Query Rewriter → BM25 Retriever → Context Builder → LLM
"""

import logging
from typing import List, Optional, Tuple

from app.core.chunker import Chunk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------
# We use a simple character-based heuristic for token counting since
# we deliberately don't use tiktoken or any tokenizer library.
# Average English text: ~4 characters per token.
# Legal text tends to be slightly more verbose, so we use ~3.5 chars/token
# for a conservative estimate.
CHARS_PER_TOKEN = 3.5


def estimate_tokens(text: str) -> int:
    """Estimate token count from text length."""
    return int(len(text) / CHARS_PER_TOKEN)


def build_context(
    retrieved_chunks: List[Tuple[Chunk, float]],
    max_tokens: int = 200000,
    include_scores: bool = False,
) -> Tuple[str, List[Tuple[Chunk, float]]]:
    """
    Build a structured context string from retrieved BM25 chunks.

    Each chunk is formatted with a clear source label for citation grounding:
        [SOURCE 1] Section X, Act Name
        <chunk text>

    If the constructed context exceeds the token budget, chunks are
    dropped from the bottom (lowest BM25 score) until the budget is met.

    Args:
        retrieved_chunks: List of (chunk, bm25_score) tuples, pre-sorted by score
        max_tokens: Maximum tokens allowed for the context
        include_scores: Whether to include BM25 scores in source labels

    Returns:
        Tuple of (context_string, included_chunks)
    """
    if not retrieved_chunks:
        return "", []

    context_parts: List[str] = []
    included_chunks: List[Tuple[Chunk, float]] = []
    total_tokens = 0

    # Header
    header = (
        "The following are excerpts from Indian legal documents. "
        "Use ONLY these sources to answer the question. "
        "Cite every claim using the [Section X, Act Name] format.\n\n"
    )
    header_tokens = estimate_tokens(header)
    total_tokens += header_tokens

    for i, (chunk, score) in enumerate(retrieved_chunks):
        # Format source label
        source_label = f"[SOURCE {i + 1}] {chunk.source_label}"
        if include_scores:
            source_label += f" (relevance: {score:.3f})"

        chunk_block = f"{source_label}\n{chunk.text}\n"
        chunk_tokens = estimate_tokens(chunk_block)

        # Check token budget
        if total_tokens + chunk_tokens > max_tokens:
            logger.info(
                f"Context budget reached at chunk {i + 1}/{len(retrieved_chunks)}. "
                f"Used {total_tokens} tokens, budget {max_tokens}."
            )
            break

        context_parts.append(chunk_block)
        included_chunks.append((chunk, score))
        total_tokens += chunk_tokens

    # Separator between chunks
    context = header + "\n---\n\n".join(context_parts)

    logger.info(
        f"Built context: {len(included_chunks)}/{len(retrieved_chunks)} chunks, "
        f"~{total_tokens} tokens"
    )

    return context, included_chunks


def build_context_with_budget(
    retriever,
    query: str,
    max_tokens: int = 200000,
    initial_top_k: int = 15,
    domain_filters: Optional[List[str]] = None,
) -> Tuple[str, List[Tuple[Chunk, float]]]:
    """
    Higher-level context builder that handles token budget enforcement.

    If the initial retrieval exceeds the token budget, it automatically
    reduces top_k and rebuilds.

    Args:
        retriever: ARTHARetriever instance
        query: User's search query (already rewritten for legal terms)
        max_tokens: Maximum tokens for the context
        initial_top_k: Starting number of chunks to retrieve
        domain_filters: Optional list of domains to filter by

    Returns:
        Tuple of (context_string, included_chunks)
    """
    # First attempt with full top_k
    results = retriever.search(query, top_k=initial_top_k, domain_filters=domain_filters)

    if not results:
        return "", []

    context, included = build_context(results, max_tokens=max_tokens)

    # If we had to drop chunks, log it
    if len(included) < len(results):
        logger.info(
            f"Token budget enforcement: included {len(included)}/{len(results)} chunks"
        )

    return context, included


# ---------------------------------------------------------------------------
# Query Rewriting
# ---------------------------------------------------------------------------

REWRITE_SYSTEM_PROMPT = """You are a legal query rewriter for Indian law. 
Convert the user's conversational question into a precise legal search query.

Rules:
- Use specific legal terminology from Indian statutes
- Include relevant act names, section references, and legal concepts
- Keep the rewritten query concise (under 50 words)
- Do NOT answer the question, only rewrite it for search
- If the query already uses legal terminology, return it as-is

Examples:
- "should I make a pvt ltd or LLP?" → "private limited company vs LLP incorporation comparison Companies Act 2013 LLP Act 2008"
- "when do I need GST?" → "GST registration threshold aggregate turnover Section 22 CGST Act 2017"
- "can a foreigner invest in my startup?" → "foreign direct investment FDI FEMA regulations person resident outside India equity instruments"
- "what's angel tax?" → "angel tax Section 56(2)(viib) Income Tax Act share premium excess fair market value startup exemption"
"""


async def rewrite_query(
    query: str,
    llm_client=None,
    model: str = "moonshotai/kimi-k2.6",
) -> str:
    """
    Rewrite a conversational query into legal-terminology search terms.

    Uses a lightweight LLM call to convert natural language into
    the kind of legal terminology that BM25 will match well.

    If the LLM is unavailable, falls back to the original query.

    Args:
        query: User's original conversational question
        llm_client: OpenAI-compatible client (NVIDIA NIM)
        model: Model slug for the rewrite call

    Returns:
        Rewritten query optimized for BM25 retrieval
    """
    if not llm_client:
        logger.warning("No LLM client for query rewriting, using original query")
        return query

    try:
        response = await llm_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.1,
            max_tokens=100,
            stream=False,
        )
        rewritten = response.choices[0].message.content.strip()
        logger.info(f"Query rewritten: '{query}' → '{rewritten}'")
        return rewritten

    except Exception as e:
        logger.warning(f"Query rewrite failed, using original: {e}")
        return query


def format_conversation_context(
    messages: List[dict],
    max_messages: int = 10,
) -> str:
    """
    Format recent conversation history for inclusion in the LLM prompt.

    Args:
        messages: List of message dicts with 'role' and 'content'
        max_messages: Maximum number of recent messages to include

    Returns:
        Formatted conversation string
    """
    if not messages:
        return ""

    recent = messages[-max_messages:]
    parts = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "ARTHA"
        parts.append(f"{role}: {msg['content']}")

    return "\n".join(parts)
