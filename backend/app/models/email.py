"""
Email Marketing Database Models
Corresponds to Master Specification Section 12 and Section 35 (email_campaigns, email_events).
"""

import uuid
from typing import List, Optional
from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class EmailCampaign(Base, TenantMixin, TimestampMixin):
    """Email lifecycle campaigns with personalized sequence templates."""
    __tablename__ = "email_campaigns"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # welcome, lead_nurturing, product_education, demo_followup, sales_followup, reengagement, retention, upsell, cross_sell, win_back
    subject_line: Mapped[str] = mapped_column(String(255), nullable=False)
    preview_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    target_segment: Mapped[str] = mapped_column(String(100), default="All Leads")
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)  # draft, active, scheduled, sent
    personalization_fields: Mapped[list] = mapped_column(JSON, default=list)  # company, industry, job_role, pain_point, etc.
    open_rate: Mapped[float] = mapped_column(Float, default=0.0)
    click_rate: Mapped[float] = mapped_column(Float, default=0.0)

    events: Mapped[List["EmailEvent"]] = relationship(
        "EmailEvent",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )


class EmailEvent(Base, TimestampMixin):
    """Email delivery and engagement events."""
    __tablename__ = "email_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("email_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # sent, delivered, opened, clicked, bounced, unsubscribed
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    campaign: Mapped["EmailCampaign"] = relationship("EmailCampaign", back_populates="events")
