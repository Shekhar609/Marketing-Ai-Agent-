"""
Hallucination Detection & Factual Grounding Guardrail
Corresponds to Master Specification Section 39 & Section 40.
"""

import re
from typing import List, Optional
from pydantic import BaseModel


class HallucinationCheckResult(BaseModel):
    is_grounded: bool
    groundedness_score: float  # 0.0 to 1.0
    unsupported_claims: List[str]
    detected_entities: List[str]
    verdict: str  # GROUNDED, PARTIAL_HALLUCINATION, HIGH_RISK_HALLUCINATION


class HallucinationDetector:
    """
    Evaluates factual alignment between retrieved knowledge context and model outputs.
    """

    @classmethod
    def check_grounding(
        cls,
        generated_text: str,
        context_passages: List[str],
        grounding_threshold: float = 0.65,
    ) -> HallucinationCheckResult:
        if not generated_text:
            return HallucinationCheckResult(
                is_grounded=True,
                groundedness_score=1.0,
                unsupported_claims=[],
                detected_entities=[],
                verdict="GROUNDED",
            )

        if not context_passages:
            # If no context is provided, consider it an unverified statement
            return HallucinationCheckResult(
                is_grounded=False,
                groundedness_score=0.0,
                unsupported_claims=[generated_text[:100] + "..."],
                detected_entities=[],
                verdict="UNVERIFIED_CONTEXT",
            )

        combined_context = " ".join(context_passages).lower()
        context_words = set(re.findall(r"\b\w{3,}\b", combined_context))

        # Break generated text into sentences/claims
        claims = [
            s.strip()
            for s in re.split(r"[.!?\n]+", generated_text)
            if len(s.strip()) > 15
        ]

        if not claims:
            return HallucinationCheckResult(
                is_grounded=True,
                groundedness_score=1.0,
                unsupported_claims=[],
                detected_entities=[],
                verdict="GROUNDED",
            )

        unsupported_claims = []
        claim_scores = []

        # Extract numerical & capitalized entities to verify high-stakes precision
        entities = list(set(re.findall(r"\b(?:[A-Z][a-z]+|\d+(?:\.\d+)?%?)\b", generated_text)))

        for claim in claims:
            words = set(re.findall(r"\b\w{3,}\b", claim.lower()))
            if not words:
                continue
            overlap = len(words.intersection(context_words)) / len(words)
            claim_scores.append(overlap)
            if overlap < 0.35:
                unsupported_claims.append(claim)

        avg_score = sum(claim_scores) / max(len(claim_scores), 1)
        is_grounded = avg_score >= grounding_threshold and len(unsupported_claims) == 0

        verdict = "GROUNDED"
        if not is_grounded:
            verdict = "PARTIAL_HALLUCINATION" if avg_score >= 0.4 else "HIGH_RISK_HALLUCINATION"

        return HallucinationCheckResult(
            is_grounded=is_grounded,
            groundedness_score=round(avg_score, 3),
            unsupported_claims=unsupported_claims,
            detected_entities=entities[:10],
            verdict=verdict,
        )
