"""
MCP-Compatible Tool Architecture & Risk Gate Interface
Corresponds to Master Specification Section 24 & 25.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field

from app.models.audit import RiskLevel


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    result: Any = None
    error: Optional[str] = None
    requires_approval: bool = False
    approval_request_id: Optional[str] = None
    execution_time_ms: float = 0.0


class BaseTool(ABC):
    """Abstract interface for all MCP-compatible marketing tools."""

    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    input_schema: Optional[Type[BaseModel]] = None

    @abstractmethod
    async def execute(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        """Executes the tool logic."""
        pass
