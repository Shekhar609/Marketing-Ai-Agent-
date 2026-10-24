"""
ICP (Ideal Customer Profile) and Buyer Persona Models
"""

import uuid
from typing import List, Optional
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class ICP(Base, TenantMixin, TimestampMixin):
    """Ideal Customer Profile configuration."""
    __tablename__ = "icps"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    company_size: Mapped[str] = mapped_column(String(100), nullable=False)
    revenue_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    geography: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    tech_stack: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    buying_capacity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    business_problems: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="icps_rel"
    )
    personas: Mapped[List["BuyerPersona"]] = relationship(
        "BuyerPersona",
        back_populates="icp",
        cascade="all, delete-orphan"
    )


class BuyerPersona(Base, TenantMixin, TimestampMixin):
    """Specific buyer persona within an ICP."""
    __tablename__ = "buyer_personas"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    icp_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("icps.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(150), nullable=False)
    goals: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    pain_points: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    buying_triggers: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    objections: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    decision_criteria: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    preferred_channels: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    icp: Mapped["ICP"] = relationship("ICP", back_populates="personas")
