"""
OpenAI LLM Client Implementation
Supports GPT-4o and GPT-4o-mini
"""

import time
from typing import List, Optional, Type, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.core.llm.base import BaseLLMClient, LLMMessage, LLMResponse
from app.core.llm.structured import parse_and_validate

T = TypeVar("T", bound=BaseModel)


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None

    async def generate(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if not self.client:
            raise ValueError("OPENAI_API_KEY is not configured in settings or environment.")

        selected_model = model or settings.CHEAP_LLM_MODEL
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]

        start_time = time.time()
        response = await self.client.chat.completions.create(
            model=selected_model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = (time.time() - start_time) * 1000

        choice = response.choices[0]
        text = choice.message.content or ""
        in_tok = response.usage.prompt_tokens if response.usage else 0
        out_tok = response.usage.completion_tokens if response.usage else 0

        return LLMResponse(
            content=text,
            model=selected_model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_ms=latency_ms,
            estimated_cost=(in_tok * 0.00000015) + (out_tok * 0.0000006),
        )

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        schema_json = schema.model_json_schema()
        system_instruction = (
            f"You are an enterprise AI agent. Return ONLY a valid JSON object matching this schema:\n"
            f"{schema_json}\nDo NOT include markdown formatting or explanations."
        )
        extended_messages = [LLMMessage(role="system", content=system_instruction)] + messages
        res = await self.generate(extended_messages, model=model, temperature=temperature)
        return parse_and_validate(res.content, schema)
