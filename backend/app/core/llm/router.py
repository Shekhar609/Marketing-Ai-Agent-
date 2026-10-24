"""
Intelligent Model Router & Cost Optimizer
Corresponds to Master Specification Section 41.
"""

import enum
from typing import List, Optional, Type, TypeVar
from pydantic import BaseModel

from app.core.config import settings
from app.core.llm.base import BaseLLMClient, LLMMessage, LLMResponse
from app.core.llm.gemini_client import GeminiClient
from app.core.llm.mock_client import MockLLMClient
from app.core.llm.openai_client import OpenAIClient

T = TypeVar("T", bound=BaseModel)


class TaskComplexity(str, enum.Enum):
    CLASSIFICATION = "classification"    # Fast & cheap (intent, sentiment, routing)
    SUMMARIZATION = "summarization"      # Balanced (meeting briefs, digests, social posts)
    STRATEGY = "strategy"                # High-reasoning (60-day growth plans, battlecards)


class LLMRouter:
    def __init__(self):
        self._gemini = GeminiClient()
        self._openai = OpenAIClient()
        self._mock = MockLLMClient()

    def get_client_and_model(
        self, complexity: TaskComplexity = TaskComplexity.SUMMARIZATION
    ) -> tuple[BaseLLMClient, str]:
        """
        Route request to the most cost-effective and capable provider available.
        """
        # 1. Prefer Gemini if Google API key is provided
        if settings.GOOGLE_API_KEY:
            if complexity == TaskComplexity.STRATEGY:
                return self._gemini, settings.GEMINI_PRO_MODEL
            else:
                return self._gemini, settings.GEMINI_FLASH_MODEL

        # 2. Prefer OpenAI if OpenAI API key is provided
        if settings.OPENAI_API_KEY:
            if complexity == TaskComplexity.STRATEGY:
                return self._openai, settings.REASONING_LLM_MODEL
            else:
                return self._openai, settings.CHEAP_LLM_MODEL

        # 3. Fallback to offline mock client
        return self._mock, "mock-offline-engine"

    async def generate(
        self,
        messages: List[LLMMessage],
        complexity: TaskComplexity = TaskComplexity.SUMMARIZATION,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        client, model = self.get_client_and_model(complexity)
        return await client.generate(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Type[T],
        complexity: TaskComplexity = TaskComplexity.STRATEGY,
        temperature: float = 0.2,
    ) -> T:
        client, model = self.get_client_and_model(complexity)
        return await client.generate_structured(
            messages=messages,
            schema=schema,
            model=model,
            temperature=temperature,
        )


llm_router = LLMRouter()
