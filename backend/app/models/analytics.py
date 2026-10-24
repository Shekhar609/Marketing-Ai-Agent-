"""
Analytics, Attribution, Reports, Alerts, and Opportunities Database Models
Corresponds to Master Specification Sections 16, 29, 30, 31, 33, 34, and 35.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class Opportunity(Base, TenantMixin, TimestampMixin):
    """Pipeline deal tracking linked to marketing leads and revenue attribution."""
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lead_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    stage: Mapped[str] = mapped_column(
        String(50), default="qualification", index=True
    )  # qualification, proposal, negotiation, closed_won, closed_lost
    probability: Mapped[float] = mapped_column(Float, default=0.2)
    expected_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AnalyticsEvent(Base, TenantMixin, TimestampMixin):
    """Raw marketing telemetry and conversion events across the entire funnel."""
    __tablename__ = "analytics_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    event_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # page_view, lead_captured, mql_converted, sql_converted, opportunity_created, deal_won
    funnel_stage: Mapped[str] = mapped_column(
        String(50), default="visitor", index=True
    )  # visitor, lead, mql, sql, opportunity, customer, retention, expansion
    channel: Mapped[str] = mapped_column(String(50), default="Direct")
    source: Mapped[str] = mapped_column(String(100), default="Organic")
    campaign_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    lead_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)


class Report(Base, TenantMixin, TimestampMixin):
    """Automated periodic executive intelligence reports."""
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    report_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # daily, weekly, monthly, quarterly
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metrics_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    key_findings: Mapped[list] = mapped_column(JSON, default=list)
    strategic_recommendations: Mapped[list] = mapped_column(JSON, default=list)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)


class Alert(Base, TenantMixin, TimestampMixin):
    """Proactive anomalies, drop-offs, and critical business threshold alerts."""
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    alert_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # lead_drop, conversion_drop, cac_increase, budget_overspend, churn_risk, high_intent_lead, revenue_opportunity
    severity: Mapped[str] = mapped_column(String(20), default="WARNING")  # INFO, WARNING, CRITICAL
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", index=True)  # ACTIVE, ACKNOWLEDGED, RESOLVED


class Recommendation(Base, TenantMixin, TimestampMixin):
    """AI-generated strategic marketing optimizations."""
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    category: Mapped[str] = mapped_column(
        String(50), default="budget"
    )  # budget, channel, content, conversion, retention
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_impact: Mapped[str] = mapped_column(String(100), default="Medium")
    effort: Mapped[str] = mapped_column(String(50), default="Low")
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)  # pending, approved, rejected, implemented
