"""
User, Role, and RBAC Models
"""

import enum
import uuid
from typing import List, Optional
from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MARKETER = "marketer"
    SALES = "sales"
    EXECUTIVE = "executive"
    VIEWER = "viewer"


class User(Base, TenantMixin, TimestampMixin):
    """User account belonging to an Organization."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.MARKETER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="users"
    )


class Role(Base, TenantMixin, TimestampMixin):
    """Custom RBAC roles defined per organization."""
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        back_populates="role",
        cascade="all, delete-orphan"
    )


class Permission(Base, TimestampMixin):
    """Permissions mapped to roles for granular access controls."""
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    resource: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'campaigns', 'budget', 'approvals'
    action: Mapped[str] = mapped_column(String(50), nullable=False)     # e.g., 'create', 'approve', 'execute', 'view'

    role: Mapped["Role"] = relationship("Role", back_populates="permissions")
