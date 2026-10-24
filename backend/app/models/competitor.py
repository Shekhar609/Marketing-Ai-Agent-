"""
Competitor Model — Competitive Intelligence Agent Profile & Matrix Storage
Corresponds to Master Specification Section 6 and Section 35 (competitors table).
"""

import uuid
from typing import Optional
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class Competitor(Base, TenantMixin, TimestampMixin):
    """Stores competitor profiles, SWOT matrices, and battlecards."""
    __tablename__ = "competitors"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    market_share: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pricing_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    recent_actions: Mapped[list] = mapped_column(JSON, default=list)
    aipnt_moat: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_confidence: Mapped[str] = mapped_column(String(50), default="AI Hypothesis")
    swot: Mapped[dict] = mapped_column(JSON, default=dict)
    content_gaps: Mapped[list] = mapped_column(JSON, default=list)
    seo_gaps: Mapped[list] = mapped_column(JSON, default=list)
