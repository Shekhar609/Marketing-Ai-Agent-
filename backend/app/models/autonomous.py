"""
Memory, Experiments, and Autonomous Optimization Database Models
Corresponds to Master Specification Sections 23, 27, 28, 46, and 35.
"""

import uuid
from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class MemoryItem(Base, TenantMixin, TimestampMixin):
    """Long-term and persistent organization memory store per Section 23."""
    __tablename__ = "memory"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    memory_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # preference, past_campaign, successful_messaging, customer_insight, brand_rule, decision
    key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class EpisodicMemory(Base, TenantMixin, TimestampMixin):
    """Episodic memory recording actions, outcomes, successes, and failures per Section 23."""
    __tablename__ = "episodic_memory"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    task_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    action_taken: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    what_worked: Mapped[list] = mapped_column(JSON, default=list)
    what_failed: Mapped[list] = mapped_column(JSON, default=list)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)


class Experiment(Base, TenantMixin, TimestampMixin):
    """A/B and multivariate marketing experiments per Section 28."""
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    experiment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # email_subject, cta, landing_page, ad_creative, messaging
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    control: Mapped[str] = mapped_column(Text, nullable=False)
    variants: Mapped[list] = mapped_column(JSON, default=list)
    target_metric: Mapped[str] = mapped_column(String(100), default="conversion_rate")
    status: Mapped[str] = mapped_column(
        String(50), default="running", index=True
    )  # draft, running, completed, cancelled
    winner_variant: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    decision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    results: Mapped[List["ExperimentResult"]] = relationship(
        "ExperimentResult",
        back_populates="experiment",
        cascade="all, delete-orphan"
    )


class ExperimentResult(Base, TimestampMixin):
    """Statistical measurement of each variant in an experiment."""
    __tablename__ = "experiment_results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    experiment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    variant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    uplift: Mapped[float] = mapped_column(Float, default=0.0)
    statistical_significance: Mapped[float] = mapped_column(Float, default=0.0)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="results")
