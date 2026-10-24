"""
Output Guardrail & Data Leakage Prevention
Corresponds to Master Specification Section 40 & Section 42.
"""

import re
from typing import List, Optional
from pydantic import BaseModel


class OutputValidationResult(BaseModel):
    is_valid: bool
    violations: List[str]
    has_leakage: bool
    sanitized_output: str


LEAKAGE_PATTERNS = [
    (r"(?i)(postgresql|mysql|sqlite|redis|mongodb)://[^\s]+", "DB_CONNECTION_STRING_LEAK"),
    (r"(?i)(BEGIN\s+RSA\s+PRIVATE\s+KEY|SECRET_KEY\s*=|JWT_SECRET\s*=)", "CRYPTO_KEY_LEAK"),
    (r"(?i)(Traceback\s*\(most\s+recent\s+call\s+last\):|File\s+\".*?\",\s+line\s+\d+)", "STACK_TRACE_LEAK"),
    (r"(?i)(Internal\s+System\s+Directive:|System\s+Prompt:\s*You\s+are\s+an\s+autonomous)", "SYSTEM_PROMPT_LEAK"),
]

INAPPROPRIATE_TONE_PATTERNS = [
    (r"(?i)\b(guaranteed\s+100%\s+roi|get\s+rich\s+quick|zero\s+risk\s+investment)\b", "UNREALISTIC_MARKETING_PROMISE"),
    (r"(?i)\b(hack\s+the\s+system|cheat\s+the\s+algorithm|bypass\s+ad\s+policies)\b", "ETHICAL_VIOLATION"),
]


class OutputGuard:
    """
    Validates agent outputs before they are persisted, dispatched to clients, or delivered via integrations.
    """

    @classmethod
    def validate(cls, text: str) -> OutputValidationResult:
        if not text:
            return OutputValidationResult(
                is_valid=True,
                violations=[],
                has_leakage=False,
                sanitized_output="",
            )

        violations = []
        has_leakage = False
        sanitized = text

        # Check for system/secrets data leakage
        for pattern, leak_type in LEAKAGE_PATTERNS:
            if re.search(pattern, sanitized):
                violations.append(leak_type)
                has_leakage = True
                sanitized = re.sub(pattern, "[DATA_EXPUNGED]", sanitized)

        # Check for inappropriate marketing promises/claims
        for pattern, tone_type in INAPPROPRIATE_TONE_PATTERNS:
            if re.search(pattern, sanitized):
                violations.append(tone_type)

        return OutputValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            has_leakage=has_leakage,
            sanitized_output=sanitized,
        )
