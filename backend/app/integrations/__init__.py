"""
External Integrations Package & Factory
"""

from typing import Any, Dict, Optional, Type

from app.integrations.base import BaseConnector
from app.integrations.crm import HubSpotConnector, MockCRMConnector, SalesforceConnector
from app.integrations.analytics import GoogleAnalyticsConnector
from app.integrations.ads import GoogleAdsConnector, LinkedInAdsConnector, MetaAdsConnector
from app.integrations.email import SendGridConnector, SMTPConnector
from app.integrations.slack import SlackConnector
from app.integrations.calendar import CalendarConnector
from app.integrations.website import WebsiteConnector
from app.models.integration import IntegrationProvider

CONNECTOR_MAP: Dict[str, Type[BaseConnector]] = {
    IntegrationProvider.HUBSPOT.value: HubSpotConnector,
    IntegrationProvider.SALESFORCE.value: SalesforceConnector,
    IntegrationProvider.MOCK_CRM.value: MockCRMConnector,
    IntegrationProvider.GOOGLE_ANALYTICS.value: GoogleAnalyticsConnector,
    IntegrationProvider.GOOGLE_ADS.value: GoogleAdsConnector,
    IntegrationProvider.LINKEDIN.value: LinkedInAdsConnector,
    IntegrationProvider.META.value: MetaAdsConnector,
    IntegrationProvider.SENDGRID.value: SendGridConnector,
    IntegrationProvider.SMTP.value: SMTPConnector,
    IntegrationProvider.SLACK.value: SlackConnector,
    IntegrationProvider.CALENDAR.value: CalendarConnector,
    IntegrationProvider.WEBSITE.value: WebsiteConnector,
}


def get_connector(
    provider: str,
    credentials: Optional[Dict[str, Any]] = None,
    settings: Optional[Dict[str, Any]] = None
) -> BaseConnector:
    """
    Factory to retrieve an instantiated connector for any given provider.
    """
    provider_key = provider.lower()
    connector_cls = CONNECTOR_MAP.get(provider_key)
    if not connector_cls:
        raise ValueError(f"Unsupported integration provider: {provider}")
    return connector_cls(credentials=credentials or {}, settings=settings or {})


__all__ = [
    "BaseConnector",
    "HubSpotConnector",
    "SalesforceConnector",
    "MockCRMConnector",
    "GoogleAnalyticsConnector",
    "GoogleAdsConnector",
    "LinkedInAdsConnector",
    "MetaAdsConnector",
    "SendGridConnector",
    "SMTPConnector",
    "SlackConnector",
    "CalendarConnector",
    "WebsiteConnector",
    "get_connector",
    "CONNECTOR_MAP",
]
