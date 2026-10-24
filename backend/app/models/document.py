"""
Document, Chunk, and Embedding Models for Enterprise RAG System
Corresponds to Master Specification Section 22 & 35.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class DocumentType(str, enum.Enum):
    """Classification of enterprise document types."""
    COMPANY_DOCUMENT = "company_document"
    PRODUCT_DOCUMENTATION = "product_documentation"
    BRAND_GUIDELINES = "brand_guidelines"
    PRICING = "pricing"
    CASE_STUDY = "case_study"
    SALES_DECK = "sales_deck"
    CUSTOMER_REVIEW = "customer_review"
    COMPETITOR_REPORT = "competitor_report"
    MARKETING_REPORT = "marketing_report"
    PREVIOUS_CAMPAIGN = "previous_campaign"
    FAQ = "faq"
    WEBSITE_CONTENT = "website_content"
    WHITEPAPER = "whitepaper"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    """Processing status of a document through the RAG pipeline."""
    PENDING = "PENDING"
    PARSING = "PARSING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class Document(Base, TenantMixin, TimestampMixin):
    """
    Top-level document record in the enterprise knowledge base.
    Corresponds to the RAG pipeline input in Section 22.
    """
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="text/plain")
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType),
        default=DocumentType.OTHER,
        nullable=False,
        index=True,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Metadata for RAG filtering (Section 22)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    product: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Raw content (stored for re-processing)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Processing telemetry
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processing_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base, TenantMixin):
    """
    A semantic chunk of a parsed document with its vector embedding.
    Implements the Document → Parser → Chunking → Embedding pipeline.
    """
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata preserved for each chunk (Section 22)
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Embedding vector stored as JSON list of floats
    # (For production pgvector, this would use a Vector column type)
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )
