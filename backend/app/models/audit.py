"""
Audit Logging, Security Tracking, and Human Approval Models
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Enum, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AuditLog(Base, TenantMixin):
    """Immutable audit trail for compliance, security, and tenant isolation."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class ApprovalRequest(Base, TenantMixin, TimestampMixin):
    """
    Human-in-the-Loop approval gate for high-impact agent actions.
    Corresponds to Master Specification Section 25 & 26.
    """
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel),
        default=RiskLevel.HIGH,
        nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False,
        index=True
    )
    decided_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
