"""
PII Detection and Redaction Guardrail
Corresponds to Master Specification Section 40 & 42.
Protects Indian (Aadhaar, PAN) and Global (Emails, Phones, Cards, Secrets) PII.
"""

import re
from typing import Dict, List, Tuple
from pydantic import BaseModel


class PIIDetectionResult(BaseModel):
    has_pii: bool
    detected_types: List[str]
    pii_counts: Dict[str, int]
    redacted_text: str


class PIIDetector:
    """
    Scans, detects, and masks sensitive Personal Identifiable Information and Secrets.
    """

    PATTERNS: List[Tuple[str, str, str]] = [
        # Credit Card Number (13 to 19 digits) - check before Aadhaar to avoid partial 12-digit match
        (
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{15,16}\b",
            "CREDIT_CARD",
            "[REDACTED_CREDIT_CARD]",
        ),
        # Indian Aadhaar Number (12 digits, optional space/hyphen, exactly 12 digits)
        (
            r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}(?!\d|[-\s]\d)\b",
            "AADHAAR",
            "[REDACTED_AADHAAR]",
        ),
        # Indian PAN Card (5 letters, 4 numbers, 1 letter)
        (
            r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
            "PAN_CARD",
            "[REDACTED_PAN]",
        ),
        # API Keys & Secrets
        (
            r"(?i)\b(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|bearer\s+[a-zA-Z0-9_\-\.]{25,})\b",
            "API_SECRET",
            "[REDACTED_SECRET]",
        ),
        # Phone Numbers (International and Indian)
        (
            r"(?:\+91[\-\s]?)?[6789]\d{9}\b|\b\+?[1-9]\d{1,14}\b",
            "PHONE_NUMBER",
            "[REDACTED_PHONE]",
        ),
        # Email Addresses
        (
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "EMAIL_ADDRESS",
            "[REDACTED_EMAIL]",
        ),
    ]

    @classmethod
    def scan_and_redact(cls, text: str, redact_emails: bool = False) -> PIIDetectionResult:
        if not text:
            return PIIDetectionResult(
                has_pii=False,
                detected_types=[],
                pii_counts={},
                redacted_text="",
            )

        detected_types = []
        pii_counts: Dict[str, int] = {}
        redacted = text

        for pattern, pii_type, replacement in cls.PATTERNS:
            # In marketing context, we may want to keep emails intact if specifically requested
            if pii_type == "EMAIL_ADDRESS" and not redact_emails:
                continue

            matches = list(re.finditer(pattern, redacted))
            if matches:
                detected_types.append(pii_type)
                pii_counts[pii_type] = len(matches)
                redacted = re.sub(pattern, replacement, redacted)

        return PIIDetectionResult(
            has_pii=len(detected_types) > 0,
            detected_types=detected_types,
            pii_counts=pii_counts,
            redacted_text=redacted,
        )
