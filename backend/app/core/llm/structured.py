"""
Structured Output Extraction and Validation Engine
"""

import json
import re
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def extract_json_from_text(text: str) -> str:
    """Extract clean JSON string from raw LLM output even if surrounded by markdown fences."""
    cleaned = text.strip()
    
    # Check for markdown code fences
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, cleaned)
    if match:
        return match.group(1).strip()
    
    # Find outer curly or square brackets
    start_brace = cleaned.find("{")
    end_brace = cleaned.rfind("}")
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        return cleaned[start_brace : end_brace + 1].strip()
        
    start_bracket = cleaned.find("[")
    end_bracket = cleaned.rfind("]")
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        return cleaned[start_bracket : end_bracket + 1].strip()
        
    return cleaned


def parse_and_validate(raw_text: str, schema: Type[T]) -> T:
    """Parse JSON and validate against target Pydantic schema."""
    json_str = extract_json_from_text(raw_text)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON from model output: {e}\nRaw output: {raw_text[:200]}")
    
    try:
        return schema.model_validate(data)
    except ValidationError as ve:
        raise ValueError(f"Validation failed for schema {schema.__name__}: {ve}")
