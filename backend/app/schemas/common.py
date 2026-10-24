"""
Common Schemas & API Envelopes
"""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None


class HealthResponse(BaseModel):
    """System health telemetry status."""
    status: str
    environment: str
    version: str
    database: str
