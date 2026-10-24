"""
Campaign Management Database Models
Corresponds to Master Specification Section 13 and Section 35 (campaigns, campaign_channels, campaign_metrics).
"""

import uuid
from typing import List, Optional
from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class Campaign(Base, TenantMixin, TimestampMixin):
    """Marketing campaigns with cross-channel budgeting, audience, and ROI projections."""
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)  # draft, active, paused, completed
    budget: Mapped[float] = mapped_column(Float, default=0.0)
    channels: Mapped[list] = mapped_column(JSON, default=list)  # Google Ads, LinkedIn, Meta, Email, etc.
    message: Mapped[str] = mapped_column(Text, nullable=False)
    creative_requirements: Mapped[list] = mapped_column(JSON, default=list)
    landing_page: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    kpis: Mapped[list] = mapped_column(JSON, default=list)
    target_cpl: Mapped[float] = mapped_column(Float, default=0.0)
    target_cac: Mapped[float] = mapped_column(Float, default=0.0)
    expected_pipeline: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    channel_details: Mapped[List["CampaignChannel"]] = relationship(
        "CampaignChannel",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    metrics: Mapped[List["CampaignMetric"]] = relationship(
        "CampaignMetric",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )


class CampaignChannel(Base, TimestampMixin):
    """Per-channel budget allocation and tracking within a campaign."""
    __tablename__ = "campaign_channels"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    channel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    allocated_budget: Mapped[float] = mapped_column(Float, default=0.0)
    spent_budget: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="active")

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="channel_details")


class CampaignMetric(Base, TimestampMixin):
    """Performance telemetry for a campaign."""
    __tablename__ = "campaign_metrics"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    impressions: Mapped[int] = mapped_column(default=0)
    clicks: Mapped[int] = mapped_column(default=0)
    leads_generated: Mapped[int] = mapped_column(default=0)
    conversions: Mapped[int] = mapped_column(default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_attributed: Mapped[float] = mapped_column(Float, default=0.0)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="metrics")
