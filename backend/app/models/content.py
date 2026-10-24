"""
Content and Content Version Models
Corresponds to Master Specification Section 9 and Section 35 (content, content_versions tables).
"""

import uuid
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class Content(Base, TenantMixin, TimestampMixin):
    """Stores marketing content assets with full marketing metadata."""
    __tablename__ = "content"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str] = mapped_column(String(255), nullable=False)
    funnel_stage: Mapped[str] = mapped_column(String(50), default="awareness")
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    cta: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_business_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_version_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    versions: Mapped[List["ContentVersion"]] = relationship(
        "ContentVersion",
        back_populates="content",
        cascade="all, delete-orphan",
        order_by="desc(ContentVersion.version_number)"
    )


class ContentVersion(Base, TimestampMixin):
    """Tracks revisions and historical versions of content assets."""
    __tablename__ = "content_versions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    content_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    seo_keywords: Mapped[list] = mapped_column(JSON, default=list)
    estimated_word_count: Mapped[int] = mapped_column(Integer, default=0)
    brand_aligned: Mapped[bool] = mapped_column(Boolean, default=True)
    change_summary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    content: Mapped["Content"] = relationship("Content", back_populates="versions")
