"""
Product and Service Catalog Models
"""

import uuid
from typing import Optional
from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class Product(Base, TenantMixin, TimestampMixin):
    """Catalog of products marketed and sold by the organization."""
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)  # EduTech, MedTech, DigiTech, Enterprise AI
    description: Mapped[str] = mapped_column(Text, nullable=False)
    features: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    pricing_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_icp: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="products_rel"
    )


class Service(Base, TenantMixin, TimestampMixin):
    """Catalog of services and bespoke solutions offered."""
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    deliverables: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
