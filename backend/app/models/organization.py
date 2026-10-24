"""
Organization Model - Multi-Tenant Root & Onboarding Configuration
"""

import uuid
from typing import List, Optional
from sqlalchemy import Boolean, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Organization(Base, TimestampMixin):
    """
    Enterprise Organization model representing the tenant and onboarding profile.
    Corresponds to Master Specification Section 3 & 35.
    """
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String(150), nullable=False, default="Technology / AI")
    website_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    geography: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="India")
    customer_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="B2B / B2G")
    sales_cycle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="30-90 days")
    
    # Financial & Operational Targets
    monthly_marketing_budget: Mapped[float] = mapped_column(Float, default=500000.0)
    monthly_lead_target: Mapped[int] = mapped_column(Integer, default=500)
    revenue_target: Mapped[float] = mapped_column(Float, default=10000000.0)
    
    # JSON-encoded onboarding properties
    products: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    services: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    target_markets: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    competitors: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    existing_channels: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    brand_guidelines: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    crm_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    social_accounts: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    analytics_platforms: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    products_rel: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    icps_rel: Mapped[List["ICP"]] = relationship(
        "ICP",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
