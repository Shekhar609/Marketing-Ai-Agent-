"""
Integration Database Models for External Connectors
"""

from datetime import datetime, timezone
import enum
from typing import Any, Dict, Optional
from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class IntegrationProvider(str, enum.Enum):
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    MOCK_CRM = "mock_crm"
    GOOGLE_ANALYTICS = "google_analytics"
    GOOGLE_ADS = "google_ads"
    LINKEDIN = "linkedin"
    META = "meta"
    SENDGRID = "sendgrid"
    SMTP = "smtp"
    SLACK = "slack"
    CALENDAR = "calendar"
    WEBSITE = "website"


class IntegrationStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    SYNCING = "syncing"
    PENDING_AUTH = "pending_auth"


class IntegrationCredential(Base, TenantMixin, TimestampMixin):
    """
    Stores connection credentials, tokens, and settings for 3rd-party connectors.
    """
    __tablename__ = "integration_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus), default=IntegrationStatus.CONNECTED, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Credentials & configs (e.g. api_key, access_token, refresh_token, client_id, webhook_url)
    credentials: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Provider settings (e.g. sync_frequency_minutes, default_channel, property_id)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    sync_logs: Mapped[list["IntegrationSyncLog"]] = relationship(
        "IntegrationSyncLog", back_populates="credential", cascade="all, delete-orphan"
    )


class IntegrationSyncLog(Base, TenantMixin, TimestampMixin):
    """
    Audit log of synchronization runs for external connectors.
    """
    __tablename__ = "integration_sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    credential_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("integration_credentials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False)  # LEADS_SYNC, GA4_IMPORT, ADS_SYNC, etc.
    status: Mapped[str] = mapped_column(String(30), default="SUCCESS", nullable=False)  # SUCCESS, FAILED, PARTIAL
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    credential: Mapped[IntegrationCredential] = relationship("IntegrationCredential", back_populates="sync_logs")


class WebhookEvent(Base, TenantMixin, TimestampMixin):
    """
    Incoming raw webhook events captured from website, CRM, or external tools.
    """
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
