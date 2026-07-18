"""
ARTHA Query Route — POST /ask
==============================
The main query endpoint. Orchestrates the full Vectorless RAG pipeline:

    User Question
        → Query Rewriting (LLM)
        → BM25 Retrieval (rank_bm25)
        → Context Building
        → LLM Generation (NVIDIA NIM / Kimi K2.6)
        → Citation Extraction
        → Response (streamed or full)

This is the critical path that demonstrates the Vectorless RAG architecture.
"""

import json
import logging
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.db.models import User, Conversation, Message, CitationRecord
from app.api.routes.auth import get_current_user
from app.models.schemas import AskRequest, AskResponse, CitationResponse
from app.core.llm import get_llm_client
from app.core.context import build_context, rewrite_query, format_conversation_context
from app.core.citations import extract_citations
from app.core.cache import (
    get_cached_response,
    set_cached_response,
    check_rate_limit,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Query"])

# The retriever is loaded at app startup and stored in app.state
# It's accessed via request.app.state.retriever in the route handler


def _get_retriever(request):
    """Get the BM25 retriever from app state."""
    retriever = getattr(request.app.state, "retriever", None)
    if not retriever:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search index not loaded. Please wait for initialization.",
        )
    return retriever


@router.post("/ask")
async def ask(
    body: AskRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Main query endpoint — the heart of the Vectorless RAG pipeline.

    Accepts a question, retrieves relevant legal sections via BM25,
    generates a cited answer via NVIDIA NIM, and returns the response
    with structured citations.
    """
    # Inject request from FastAPI
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest

    if current_user.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has not been approved for access yet. Please complete verification."
        )

    # Rate limiting
    allowed, remaining = await check_rate_limit(str(current_user.id), current_user.plan)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a moment before trying again.",
        )

    # Check cache (non-streaming only)
    if not body.stream:
        cached = await get_cached_response(body.question, body.domain_filters)
        if cached:
            return AskResponse(
                answer=cached["answer"],
                citations=[CitationResponse(**c) for c in cached.get("citations", [])],
                conversation_id=uuid.UUID(cached["conversation_id"]),
                message_id=uuid.UUID(cached["message_id"]),
                cached=True,
            )

    # Get or create conversation
    conversation = await _get_or_create_conversation(
        db, current_user.id, body.conversation_id, body.question
    )

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=body.question,
    )
    db.add(user_message)
    await db.flush()

    # Get retriever from app state
    retriever = request.app.state.retriever if request else None
    if not retriever:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search index not loaded.",
        )

    # Get LLM client
    llm_client = get_llm_client()

    # Step 1: Query rewriting
    try:
        rewritten_query = await rewrite_query(
            body.question,
            llm_client=llm_client.client,
            model=settings.NVIDIA_MODEL,
        )
    except Exception:
        rewritten_query = body.question

    # Step 2: BM25 retrieval
    results = retriever.search(
        rewritten_query,
        top_k=settings.BM25_TOP_K,
        domain_filters=body.domain_filters,
    )

    if not results:
        # No relevant chunks found
        no_result_answer = (
            "I couldn't find relevant legal provisions in the indexed corpus for your question. "
            "This could mean:\n"
            "1. The relevant act is not yet indexed in ARTHA's corpus\n"
            "2. Try rephrasing your question with specific legal terms\n"
            "3. Try broadening your domain filters\n\n"
            "---\n"
            "⚖️ *Disclaimer: This is legal information, not legal advice.*"
        )
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=no_result_answer,
        )
        db.add(assistant_message)
        await db.flush()

        return AskResponse(
            answer=no_result_answer,
            citations=[],
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            cached=False,
        )

    # Step 3: Build context
    context, included_chunks = build_context(
        results,
        max_tokens=settings.MAX_CONTEXT_TOKENS,
    )

    # Step 4: Get conversation history for context
    conv_history = await _get_conversation_history(db, conversation.id)

    # Step 5: Generate response
    if body.stream:
        return StreamingResponse(
            _stream_response(
                llm_client=llm_client,
                query=body.question,
                context=context,
                conversation_history=conv_history,
                conversation_id=conversation.id,
                included_chunks=included_chunks,
                db=db,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        return await _full_response(
            llm_client=llm_client,
            query=body.question,
            context=context,
            conversation_history=conv_history,
            conversation=conversation,
            included_chunks=included_chunks,
            domain_filters=body.domain_filters,
            db=db,
        )


async def _stream_response(
    llm_client,
    query: str,
    context: str,
    conversation_history: str,
    conversation_id,
    included_chunks,
    db: AsyncSession,
):
    """Generator for streaming SSE response."""
    full_response = ""

    try:
        # Stream opening
        yield f"data: {json.dumps({'type': 'start', 'conversation_id': str(conversation_id)})}\n\n"

        # Stream content chunks
        async for chunk in llm_client.generate_stream(
            query=query,
            context=context,
            conversation_history=conversation_history,
        ):
            full_response += chunk
            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

        # Extract citations from complete response
        citations = extract_citations(full_response, included_chunks)

        # Save assistant message and citations to database
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response,
        )
        db.add(assistant_message)
        await db.flush()

        for citation in citations:
            db.add(CitationRecord(
                message_id=assistant_message.id,
                section=citation.section,
                act_name=citation.act_name,
                source_file=citation.source_file,
                chunk_text=citation.chunk_text[:1000],  # Truncate for storage
                confidence=citation.confidence,
            ))
        await db.commit()

        # Stream citations
        citation_data = [
            {
                "section": c.section,
                "act_name": c.act_name,
                "source_file": c.source_file,
                "chunk_text": c.chunk_text[:500],
                "confidence": c.confidence,
            }
            for c in citations
        ]
        yield f"data: {json.dumps({'type': 'citations', 'citations': citation_data})}\n\n"

        # Stream end
        yield f"data: {json.dumps({'type': 'end', 'message_id': str(assistant_message.id)})}\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


async def _full_response(
    llm_client,
    query: str,
    context: str,
    conversation_history: str,
    conversation,
    included_chunks,
    domain_filters,
    db: AsyncSession,
) -> AskResponse:
    """Generate a complete (non-streamed) response."""
    # Generate full response
    answer = await llm_client.generate(
        query=query,
        context=context,
        conversation_history=conversation_history,
    )

    # Extract citations
    citations = extract_citations(answer, included_chunks)

    # Save to database
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
    )
    db.add(assistant_message)
    await db.flush()

    for citation in citations:
        db.add(CitationRecord(
            message_id=assistant_message.id,
            section=citation.section,
            act_name=citation.act_name,
            source_file=citation.source_file,
            chunk_text=citation.chunk_text[:1000],
            confidence=citation.confidence,
        ))

    # Cache the response
    cache_data = {
        "answer": answer,
        "citations": [c.to_dict() for c in citations],
        "conversation_id": str(conversation.id),
        "message_id": str(assistant_message.id),
    }
    await set_cached_response(query, cache_data, domain_filters)

    return AskResponse(
        answer=answer,
        citations=[
            CitationResponse(
                section=c.section,
                act_name=c.act_name,
                source_file=c.source_file,
                chunk_text=c.chunk_text[:500],
                confidence=c.confidence,
            )
            for c in citations
        ],
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        cached=False,
    )


async def _get_or_create_conversation(
    db: AsyncSession,
    user_id,
    conversation_id: Optional[uuid.UUID],
    question: str,
) -> Conversation:
    """Get existing conversation or create a new one."""
    from sqlalchemy import select

    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            return conversation

    # Create new conversation with question as title
    title = question[:100] + ("..." if len(question) > 100 else "")
    conversation = Conversation(
        user_id=user_id,
        title=title,
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def _get_conversation_history(
    db: AsyncSession,
    conversation_id,
    max_messages: int = 10,
) -> str:
    """Get recent conversation history for context."""
    from sqlalchemy import select

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(max_messages)
    )
    messages = result.scalars().all()

    if len(messages) <= 1:  # Only the current user message
        return ""

    # Reverse to chronological order (skip the current message)
    history = list(reversed(messages[1:]))
    return format_conversation_context(
        [{"role": m.role, "content": m.content} for m in history]
    )
