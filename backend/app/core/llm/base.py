"""
Base LLM Provider Abstraction & Telemetry Models
Corresponds to Master Specification Section 4 & 41.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class LLMMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    estimated_cost: float = 0.0
    structured_data: Optional[Any] = None


class BaseLLMClient(ABC):
    """Abstract interface for all LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate unstructured text response."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        """Generate verified structured output matching Pydantic schema."""
        pass
