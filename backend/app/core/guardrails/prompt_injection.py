"""
Prompt Injection & Jailbreak Defense System
Corresponds to Master Specification Section 40.
"""

import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel


class InjectionDetectionResult(BaseModel):
    is_safe: bool
    confidence: float
    attack_type: Optional[str] = None
    matched_pattern: Optional[str] = None
    sanitized_input: str


# Comprehensive patterns targeting prompt injection, system overrides, and exfiltration
INJECTION_PATTERNS: List[Tuple[str, str, float]] = [
    (
        r"(?i)(ignore|disregard|forget|override|bypass)\s+(all\s+)?(previous|prior|above|system)\s+(instructions|prompts|rules|commands)",
        "INSTRUCTION_OVERRIDE",
        0.98,
    ),
    (
        r"(?i)(reveal|show|print|display|dump|repeat|output)\s+(your\s+)?(system\s+prompt|initial\s+instructions|hidden\s+rules|developer\s+mode)",
        "SYSTEM_PROMPT_LEAK",
        0.95,
    ),
    (
        r"(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be)\s+(DAN|jailbroken|unfiltered|an\s+evil\s+ai|free\s+of\s+rules)",
        "ROLEPLAY_JAILBREAK",
        0.92,
    ),
    (
        r"(?i)(developer\s+override|sudo\s+mode|administrative\s+override|debug\s+mode\s+enabled)",
        "DEVELOPER_OVERRIDE",
        0.90,
    ),
    (
        r"(?i)base64\s*(decode|string|payload)\s*:\s*[a-zA-Z0-9+/=]{20,}",
        "OBFUSCATED_PAYLOAD",
        0.85,
    ),
    (
        r"!\[.*?\]\(https?://[^\s)]+(\?|&)[^\s)]*=",
        "MARKDOWN_IMAGE_EXFILTRATION",
        0.95,
    ),
]


class PromptInjectionDetector:
    """
    Heuristic and regex-based prompt injection detection engine.
    """

    @classmethod
    def analyze(cls, text: str) -> InjectionDetectionResult:
        if not text:
            return InjectionDetectionResult(
                is_safe=True,
                confidence=1.0,
                sanitized_input="",
            )

        sanitized = text
        for pattern, attack_type, confidence in INJECTION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                # Strip or neutralize offending segment
                clean_version = re.sub(pattern, "[BLOCKED_INJECTION_ATTEMPT]", text).strip()
                return InjectionDetectionResult(
                    is_safe=False,
                    confidence=confidence,
                    attack_type=attack_type,
                    matched_pattern=match.group(0),
                    sanitized_input=clean_version,
                )

        return InjectionDetectionResult(
            is_safe=True,
            confidence=1.0,
            attack_type=None,
            matched_pattern=None,
            sanitized_input=sanitized,
        )
