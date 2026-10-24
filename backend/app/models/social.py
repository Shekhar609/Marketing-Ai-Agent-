"""
Social Media Database Models
Corresponds to Master Specification Section 11 and Section 35 (social_posts, social_metrics).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class SocialPost(Base, TenantMixin, TimestampMixin):
    """Social media posts generated across LinkedIn, X, Instagram, YouTube, and Facebook."""
    __tablename__ = "social_posts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # linkedin, twitter, instagram, youtube, facebook
    post_type: Mapped[str] = mapped_column(String(50), default="text")  # post, carousel, video_script, thought_leadership
    content: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    media_urls: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)  # draft, scheduled, published, failed
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    external_post_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    metrics: Mapped[List["SocialMetric"]] = relationship(
        "SocialMetric",
        back_populates="post",
        cascade="all, delete-orphan"
    )


class SocialMetric(Base, TimestampMixin):
    """Telemetry and engagement tracking for social posts."""
    __tablename__ = "social_metrics"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    post_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("social_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)

    post: Mapped["SocialPost"] = relationship("SocialPost", back_populates="metrics")
