"""
Base Connector Interface for External Integrations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseConnector(ABC):
    """
    Abstract base class for all third-party external connectors.
    """

    def __init__(self, credentials: Optional[Dict[str, Any]] = None, settings: Optional[Dict[str, Any]] = None):
        self.credentials = credentials or {}
        self.settings = settings or {}

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. hubspot, slack, google_analytics)"""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Validate authentication credentials and connectivity.
        Returns a dictionary with status (bool), message, and provider metadata.
        """
        pass

    @abstractmethod
    async def sync(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute bi-directional or inbound sync of external data.
        Returns metrics and results of sync operation.
        """
        pass

    async def disconnect(self) -> bool:
        """
        Revoke tokens or clean up connection state if supported.
        """
        return True
