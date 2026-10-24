"""
Unified Guardrails Service
Corresponds to Master Specification Section 40 & Section 42.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.guardrails.hallucination import HallucinationDetector
from app.core.guardrails.output_guard import OutputGuard
from app.core.guardrails.pii_detector import PIIDetector
from app.core.guardrails.prompt_injection import PromptInjectionDetector
from app.models.evaluation import GuardrailIncident, GuardrailIncidentType

logger = logging.getLogger(__name__)


class GuardrailsService:
    """
    Coordinates input and output safety guardrails, threat neutralization, and audit logging.
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def check_input(
        self,
        prompt: str,
        organization_id: Optional[str] = None,
        redact_pii: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate incoming user prompt or agent input against injection and PII leakage.
        """
        # 1. Prompt Injection Scan
        injection_res = PromptInjectionDetector.analyze(prompt)
        if not injection_res.is_safe:
            if self.db and organization_id:
                incident = GuardrailIncident(
                    organization_id=organization_id,
                    incident_type=GuardrailIncidentType.PROMPT_INJECTION.value,
                    severity="HIGH",
                    input_preview=prompt[:300],
                    action_taken="BLOCKED",
                    details={
                        "attack_type": injection_res.attack_type,
                        "matched_pattern": injection_res.matched_pattern,
                        "confidence": injection_res.confidence,
                    },
                )
                self.db.add(incident)
                await self.db.commit()

            return {
                "is_safe": False,
                "reason": f"Prompt injection attempt detected: {injection_res.attack_type}",
                "attack_type": injection_res.attack_type,
                "sanitized_prompt": injection_res.sanitized_input,
            }

        # 2. PII Scan & Redaction
        pii_res = PIIDetector.scan_and_redact(prompt, redact_emails=False)
        if pii_res.has_pii and self.db and organization_id:
            incident = GuardrailIncident(
                organization_id=organization_id,
                incident_type=GuardrailIncidentType.PII_DETECTED.value,
                severity="MEDIUM",
                input_preview=prompt[:300],
                action_taken="SANITIZED",
                details={"detected_types": pii_res.detected_types, "counts": pii_res.pii_counts},
            )
            self.db.add(incident)
            await self.db.commit()

        clean_text = pii_res.redacted_text if redact_pii else prompt
        return {
            "is_safe": True,
            "has_pii": pii_res.has_pii,
            "detected_pii": pii_res.detected_types,
            "sanitized_prompt": clean_text,
        }

    async def check_output(
        self,
        generated_output: str,
        context_passages: Optional[List[str]] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate LLM output for data leakage, inappropriate marketing promises, and hallucinations.
        """
        # 1. Output Guard (Data leakage, stack traces, system prompts)
        output_res = OutputGuard.validate(generated_output)
        if not output_res.is_valid:
            if self.db and organization_id:
                incident = GuardrailIncident(
                    organization_id=organization_id,
                    incident_type=GuardrailIncidentType.DATA_LEAKAGE.value,
                    severity="HIGH",
                    input_preview=generated_output[:300],
                    action_taken="SANITIZED",
                    details={"violations": output_res.violations},
                )
                self.db.add(incident)
                await self.db.commit()

        # 2. Hallucination Check against provided knowledge context
        hallucination_res = None
        if context_passages:
            hallucination_res = HallucinationDetector.check_grounding(
                generated_text=output_res.sanitized_output,
                context_passages=context_passages,
            )
            if not hallucination_res.is_grounded and self.db and organization_id:
                incident = GuardrailIncident(
                    organization_id=organization_id,
                    incident_type=GuardrailIncidentType.HALLUCINATION.value,
                    severity="MEDIUM",
                    input_preview=generated_output[:300],
                    action_taken="FLAGGED",
                    details={
                        "groundedness_score": hallucination_res.groundedness_score,
                        "unsupported_claims": hallucination_res.unsupported_claims,
                    },
                )
                self.db.add(incident)
                await self.db.commit()

        return {
            "is_valid": output_res.is_valid and (hallucination_res.is_grounded if hallucination_res else True),
            "sanitized_output": output_res.sanitized_output,
            "violations": output_res.violations,
            "has_leakage": output_res.has_leakage,
            "hallucination_eval": (
                {
                    "is_grounded": hallucination_res.is_grounded,
                    "groundedness_score": hallucination_res.groundedness_score,
                    "verdict": hallucination_res.verdict,
                    "unsupported_claims": hallucination_res.unsupported_claims,
                }
                if hallucination_res
                else None
            ),
        }
