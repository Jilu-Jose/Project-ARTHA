"""
ARTHA Database Models
======================
SQLAlchemy 2.0 ORM models matching the database schema.

Tables: users, conversations, messages, citations, corpus_documents
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)
    plan = Column(String(20), default="free")
    status = Column(String(20), default="unverified")  # unverified, pending_approval, approved
    institution = Column(String(200), nullable=True)
    role = Column(String(100), nullable=True)
    id_document_path = Column(String(500), nullable=True)
    verification_requested_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(Text, default="New Conversation")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(
        String(10),
        CheckConstraint("role IN ('user', 'assistant')"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("CitationRecord", back_populates="message", cascade="all, delete-orphan")


class CitationRecord(Base):
    """
    Stored citations extracted from assistant responses.
    Named CitationRecord to avoid collision with the Citation dataclass
    in app/core/citations.py.
    """
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    section = Column(String(100))
    act_name = Column(String(200))
    source_file = Column(String(200))
    chunk_text = Column(Text)
    confidence = Column(Float, default=0.0)

    # Relationships
    message = relationship("Message", back_populates="citations")


class CorpusDocument(Base):
    __tablename__ = "corpus_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200))
    filename = Column(String(200))
    domain = Column(String(50))
    total_chunks = Column(Integer, default=0)
    indexed_at = Column(DateTime(timezone=True), default=_utcnow)
    status = Column(String(20), default="indexed")
