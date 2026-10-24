"""
Agent & Marketing Quality Evaluator
Corresponds to Master Specification Section 39:
Evaluates Correctness, Relevance, Groundedness, Completeness, Consistency,
and Marketing Quality (Content, Campaign Projections, Lead Fit).
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AgentEvaluationResult(BaseModel):
    correctness: float
    relevance: float
    groundedness: float
    completeness: float
    consistency: float
    overall_agent_quality: float
    marketing_quality_score: float
    passed: bool
    feedback: List[str]


class AgentEvaluator:
    """
    Evaluates autonomous agent outputs across the 5 core AI dimensions and marketing domain criteria.
    """

    @classmethod
    def evaluate_output(
        cls,
        task_prompt: str,
        output_text: str,
        expected_elements: Optional[List[str]] = None,
        reference_context: Optional[str] = None,
        threshold: float = 0.70,
    ) -> AgentEvaluationResult:
        feedback = []

        # 1. Completeness: Does the output contain essential elements?
        # (e.g. CTA, Target Audience, Value Prop, Channels)
        standard_elements = expected_elements or [
            "target",
            "strategy",
            "channel",
            "metric",
            "action",
        ]
        found_elements = sum(
            1 for el in standard_elements if el.lower() in output_text.lower()
        )
        completeness = found_elements / max(len(standard_elements), 1)
        if completeness < 0.6:
            feedback.append("Output lacks key strategic components (e.g. target, channel, action)")

        # 2. Relevance: Overlap with task prompt keywords (allowing prefix/stem matches)
        prompt_words = set(re.findall(r"\b\w{3,}\b", task_prompt.lower()))
        output_words = set(re.findall(r"\b\w{3,}\b", output_text.lower()))
        matched_prompt_words = sum(
            1 for pw in prompt_words if any(pw in ow or ow in pw for ow in output_words)
        )
        relevance = min((matched_prompt_words + 2) / (len(prompt_words) + 1), 1.0)
        if relevance < 0.5:
            feedback.append("Output diverged from user task objective")

        # 3. Groundedness: Absence of vague assertions, high presence of concrete nouns/metrics
        concrete_metrics = len(re.findall(r"\b(?:\d+%?|\$\d+|ROI|CAC|CPL|CTR)\b", output_text))
        groundedness = min(0.6 + (concrete_metrics * 0.08), 1.0)
        if concrete_metrics == 0:
            feedback.append("Output lacks quantifiable marketing benchmarks or concrete KPIs")

        # 4. Consistency: Formatting, brand tone, clear headers
        has_structure = "#" in output_text or "•" in output_text or "-" in output_text or ":" in output_text
        has_professional_length = 50 <= len(output_text.split()) <= 2000
        consistency = 0.9 if (has_structure and has_professional_length) else 0.65
        if not has_structure:
            feedback.append("Output lacks structured formatting or executive headers")

        # 5. Correctness: Alignment with reference context if supplied
        if reference_context:
            ref_words = set(re.findall(r"\b\w{3,}\b", reference_context.lower()))
            correctness = min(len(output_words.intersection(ref_words)) / max(len(ref_words), 1) + 0.3, 1.0)
        else:
            correctness = 0.88  # Default baseline for syntactically sound output

        overall_agent_quality = (
            correctness * 0.25
            + relevance * 0.25
            + groundedness * 0.20
            + completeness * 0.20
            + consistency * 0.10
        )

        # Domain Marketing Quality Score
        marketing_quality = (groundedness * 0.40) + (completeness * 0.40) + (relevance * 0.20)

        passed = overall_agent_quality >= threshold and marketing_quality >= 0.60

        return AgentEvaluationResult(
            correctness=round(correctness, 3),
            relevance=round(relevance, 3),
            groundedness=round(groundedness, 3),
            completeness=round(completeness, 3),
            consistency=round(consistency, 3),
            overall_agent_quality=round(overall_agent_quality, 3),
            marketing_quality_score=round(marketing_quality, 3),
            passed=passed,
            feedback=feedback,
        )
