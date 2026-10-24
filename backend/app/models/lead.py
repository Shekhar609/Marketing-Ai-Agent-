"""
Lead Generation and Scoring Database Models
Corresponds to Master Specification Section 14 and Section 35 (leads, lead_scores, lead_events).
"""

import uuid
from typing import List, Optional
from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class Lead(Base, TenantMixin, TimestampMixin):
    """Captured leads with firmographic data, lifecycle classification, and scoring."""
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    job_title: Mapped[str] = mapped_column(String(150), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    geography: Mapped[str] = mapped_column(String(100), default="India")
    source: Mapped[str] = mapped_column(String(50), default="Website")  # Website, Forms, Ads, Events, etc.
    classification: Mapped[str] = mapped_column(
        String(50), default="Cold", index=True
    )  # Cold, Warm, Marketing Qualified, Sales Qualified, High Intent, Customer
    current_score: Mapped[float] = mapped_column(Float, default=0.0)
    intent_signals: Mapped[list] = mapped_column(JSON, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    score_history: Mapped[List["LeadScore"]] = relationship(
        "LeadScore",
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="desc(LeadScore.created_at)"
    )
    events: Mapped[List["LeadEvent"]] = relationship(
        "LeadEvent",
        back_populates="lead",
        cascade="all, delete-orphan"
    )


class LeadScore(Base, TimestampMixin):
    """Tracks historical score calculations using 5-factor breakdown."""
    __tablename__ = "lead_scores"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    lead_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    company_fit: Mapped[float] = mapped_column(Float, default=0.0)
    role_fit: Mapped[float] = mapped_column(Float, default=0.0)
    engagement: Mapped[float] = mapped_column(Float, default=0.0)
    intent: Mapped[float] = mapped_column(Float, default=0.0)
    behavior: Mapped[float] = mapped_column(Float, default=0.0)
    classification: Mapped[str] = mapped_column(String(50), nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="score_history")


class LeadEvent(Base, TimestampMixin):
    """Activity and engagement events for a lead."""
    __tablename__ = "lead_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    lead_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # page_view, form_submit, demo_request, email_open
    event_data: Mapped[dict] = mapped_column(JSON, default=dict)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="events")
