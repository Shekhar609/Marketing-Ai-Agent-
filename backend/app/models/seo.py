"""
SEO Management Database Models
Corresponds to Master Specification Section 10 and Section 35 (keywords, seo_reports).
"""

import uuid
from typing import Optional
from sqlalchemy import Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class Keyword(Base, TenantMixin, TimestampMixin):
    """Stores SEO keywords with search intent, volume, and multi-factor scoring."""
    __tablename__ = "keywords"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic_cluster: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    search_intent: Mapped[str] = mapped_column(String(50), default="informational")  # informational, navigational, commercial, transactional
    search_volume: Mapped[int] = mapped_column(Integer, default=0)
    competition: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 - 1.0
    business_value: Mapped[float] = mapped_column(Float, default=0.5)
    conversion_potential: Mapped[float] = mapped_column(Float, default=0.5)
    composite_score: Mapped[float] = mapped_column(Float, default=0.0)
    current_ranking: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class SEOReport(Base, TenantMixin, TimestampMixin):
    """Audit and strategy reports produced by the SEO Agent."""
    __tablename__ = "seo_reports"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content_gaps: Mapped[list] = mapped_column(JSON, default=list)
    topic_clusters: Mapped[list] = mapped_column(JSON, default=list)
    pillar_pages: Mapped[list] = mapped_column(JSON, default=list)
    technical_recommendations: Mapped[list] = mapped_column(JSON, default=list)
    roadmap: Mapped[list] = mapped_column(JSON, default=list)
