"""
Google Gemini LLM Client Implementation
Supports Gemini 1.5 Flash and Gemini 1.5 Pro via google-genai
"""

import time
from typing import List, Optional, Type, TypeVar
from google import genai
from pydantic import BaseModel

from app.core.config import settings
from app.core.llm.base import BaseLLMClient, LLMMessage, LLMResponse
from app.core.llm.structured import parse_and_validate

T = TypeVar("T", bound=BaseModel)


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
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
            raise ValueError("GOOGLE_API_KEY is not configured in settings or environment.")

        selected_model = model or settings.GEMINI_FLASH_MODEL
        prompt = "\n\n".join([f"[{m.role.upper()}]: {m.content}" for m in messages])
        
        start_time = time.time()
        response = self.client.models.generate_content(
            model=selected_model,
            contents=prompt,
        )
        latency_ms = (time.time() - start_time) * 1000

        text = response.text or ""
        # Approximate token count for cost tracking
        input_tokens = len(prompt.split()) * 2
        output_tokens = len(text.split()) * 2

        return LLMResponse(
            content=text,
            model=selected_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            estimated_cost=(input_tokens * 0.000000075) + (output_tokens * 0.0000003),
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
