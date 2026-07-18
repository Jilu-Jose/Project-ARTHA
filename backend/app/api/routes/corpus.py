"""
ARTHA Corpus Routes
====================
Endpoints for browsing indexed legal documents and citation deep-dive.

- GET /corpus              — List all indexed documents
- GET /corpus/{id}/sections/{section} — Citation deep-dive
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import CorpusDocument
from app.api.routes.auth import get_current_user
from app.models.schemas import CorpusDocumentResponse, SectionDetailResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/corpus", tags=["Corpus"])


@router.get("", response_model=list[CorpusDocumentResponse])
async def list_corpus(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    db: AsyncSession = Depends(get_db),
):
    """List all indexed legal documents with metadata."""
    query = select(CorpusDocument)
    if domain:
        query = query.where(CorpusDocument.domain == domain)
    query = query.order_by(CorpusDocument.name)

    result = await db.execute(query)
    documents = result.scalars().all()
    return documents


@router.get("/{document_id}/sections/{section_id}")
async def get_section_detail(
    document_id: UUID,
    section_id: str,
    request=None,
    current_user=Depends(get_current_user),
):
    """
    Citation deep-dive endpoint.
    Returns the full section text for a given document and section identifier.
    Searches the in-memory BM25 index for the matching chunk.
    """
    retriever = getattr(request.app.state, "retriever", None) if request else None
    if not retriever:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search index not loaded.",
        )

    # Search for the section across all chunks
    for chunk in retriever.all_chunks:
        if section_id.lower() in chunk.section_number.lower():
            return SectionDetailResponse(
                section=chunk.section_number,
                act_name=chunk.act_name,
                source_file=chunk.source_file,
                chapter=chunk.chapter,
                domain=chunk.domain,
                text=chunk.text,
                page_number=chunk.page_number,
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Section '{section_id}' not found in the corpus.",
    )
