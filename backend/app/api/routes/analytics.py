import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.db.models import User, Conversation, Message, CitationRecord, CorpusDocument
from app.models.schemas import AnalyticsResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get basic usage statistics for the current user.
    """
    try:
        # Total Conversations
        stmt_conv = select(func.count(Conversation.id)).where(Conversation.user_id == current_user.id)
        total_conversations = await db.scalar(stmt_conv)

        # Total Messages
        stmt_msg = select(func.count(Message.id)).join(Conversation).where(Conversation.user_id == current_user.id)
        total_messages = await db.scalar(stmt_msg)

        # Total Citations
        stmt_cit = select(func.count(CitationRecord.id)).join(Message).join(Conversation).where(Conversation.user_id == current_user.id)
        total_citations = await db.scalar(stmt_cit)

        # Total Documents Indexed (Global metric, not per user for this app)
        stmt_docs = select(func.count(CorpusDocument.id))
        documents_indexed = await db.scalar(stmt_docs)

        return AnalyticsResponse(
            total_conversations=total_conversations or 0,
            total_messages=total_messages or 0,
            total_citations=total_citations or 0,
            documents_indexed=documents_indexed or 0
        )
    except Exception as e:
        logger.error(f"Failed to fetch analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics data")
