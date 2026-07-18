"""
ARTHA Pydantic Schemas
=======================
Request/response models for all API endpoints.
Uses Pydantic v2 for validation and serialization.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    plan: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Query schemas
# ---------------------------------------------------------------------------
class AskRequest(BaseModel):
    """Request to the /ask endpoint."""
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: Optional[UUID] = None
    domain_filters: Optional[List[str]] = Field(
        default=None,
        description="Filter by legal domains: corporate, tax, securities, startup_schemes",
    )
    stream: bool = Field(default=True, description="Whether to stream the response")


class CitationResponse(BaseModel):
    """A single citation in the response."""
    section: str
    act_name: str
    source_file: str
    chunk_text: str
    confidence: float

    model_config = {"from_attributes": True}


class AskResponse(BaseModel):
    """Full (non-streamed) response from /ask."""
    answer: str
    citations: List[CitationResponse] = []
    conversation_id: UUID
    message_id: UUID
    cached: bool = False


# ---------------------------------------------------------------------------
# Conversation schemas
# ---------------------------------------------------------------------------
class ConversationSummary(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int = 0

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    citations: List[CitationResponse] = []

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    messages: List[MessageResponse] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Corpus schemas
# ---------------------------------------------------------------------------
class CorpusDocumentResponse(BaseModel):
    id: UUID
    name: str
    filename: str
    domain: str
    total_chunks: int
    indexed_at: datetime
    status: str

    model_config = {"from_attributes": True}


class SectionDetailResponse(BaseModel):
    """Citation deep-dive: full section text."""
    section: str
    act_name: str
    source_file: str
    chapter: str
    domain: str
    text: str
    page_number: int


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    database: bool
    redis: bool
    llm: bool
    retriever_loaded: bool
    total_chunks: int
    version: str


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
class AnalyticsResponse(BaseModel):
    total_conversations: int
    total_messages: int
    total_citations: int
    documents_indexed: int
