"""
Autonomous Decision Engine — Multi-Factor Scoring and Risk-Gated Evaluation
Corresponds to Master Specification Section 27 and Sections 25-26.

Evaluates 8 Decision Factors:
1. Revenue Impact
2. Cost
3. Strategic Alignment
4. Customer Value
5. Competitive Advantage
6. Scalability
7. Risk
8. Confidence
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DecisionFactors(BaseModel):
    """Underlying 8-factor evaluation matrix per Section 27."""
    revenue_impact_score: float = Field(..., ge=0, le=10, description="Projected pipeline yield (0-10)")
    cost_score: float = Field(..., ge=0, le=10, description="Capital efficiency; higher means lower cost (0-10)")
    strategic_alignment: float = Field(..., ge=0, le=10, description="Alignment with quarterly objectives (0-10)")
    customer_value: float = Field(..., ge=0, le=10, description="Customer utility and experience (0-10)")
    competitive_advantage: float = Field(..., ge=0, le=10, description="Moat enhancement (0-10)")
    scalability: float = Field(..., ge=0, le=10, description="Ease of automated scaling (0-10)")
    risk_score: float = Field(..., ge=0, le=10, description="Risk profile; lower is safer (0-10)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Evidence certainty (0.0-1.0)")


class AutonomousDecision(BaseModel):
    """Exact Master Spec Section 27 output schema with transparent factor explanation."""
    recommendation: str
    reason: str
    expected_pipeline_impact: float
    estimated_cost: float
    confidence: float
    composite_decision_score: float
    factors: DecisionFactors
    risks: List[str] = Field(default_factory=list)
    approval_required: bool = True
    suggested_action: str = "PROCEED"


class DecisionEngine:
    """Evaluates marketing recommendations and determines autonomous execution vs human signoff."""

    # Configurable approval threshold in INR
    APPROVAL_COST_THRESHOLD = 100000.0  # ₹1 Lakh requires human approval per Section 26

    def evaluate_recommendation(
        self,
        recommendation: str,
        reason: str,
        expected_pipeline_impact: float,
        estimated_cost: float,
        confidence: float = 0.85,
        risks: Optional[List[str]] = None,
        strategic_alignment: float = 8.5,
        customer_value: float = 8.0,
        competitive_advantage: float = 8.0,
        scalability: float = 7.5,
    ) -> AutonomousDecision:
        """
        Calculates composite decision score and determines Human-in-the-Loop gating.
        """
        # Calculate normalized factors
        rev_impact_score = min(10.0, (expected_pipeline_impact / max(1.0, estimated_cost * 2.0)) * 2.5)
        cost_score = max(1.0, 10.0 - min(9.0, (estimated_cost / 50000.0) * 1.5))
        risk_penalty = min(9.0, len(risks or []) * 2.0)
        risk_score = risk_penalty

        factors = DecisionFactors(
            revenue_impact_score=round(rev_impact_score, 1),
            cost_score=round(cost_score, 1),
            strategic_alignment=strategic_alignment,
            customer_value=customer_value,
            competitive_advantage=competitive_advantage,
            scalability=scalability,
            risk_score=round(risk_score, 1),
            confidence=confidence,
        )

        # Weighted calculation: (Benefits - Risks) * Confidence
        positive_weight = (
            factors.revenue_impact_score * 0.25 +
            factors.cost_score * 0.15 +
            factors.strategic_alignment * 0.20 +
            factors.customer_value * 0.15 +
            factors.competitive_advantage * 0.15 +
            factors.scalability * 0.10
        )
        composite_score = round(max(0.0, (positive_weight - (factors.risk_score * 0.3)) * confidence), 2)

        # Determine human approval requirement (Section 25 & 26)
        approval_required = (
            estimated_cost >= self.APPROVAL_COST_THRESHOLD or
            len(risks or []) >= 2 or
            confidence < 0.70 or
            "budget" in recommendation.lower() or
            "paid ad" in recommendation.lower()
        )

        return AutonomousDecision(
            recommendation=recommendation,
            reason=reason,
            expected_pipeline_impact=expected_pipeline_impact,
            estimated_cost=estimated_cost,
            confidence=confidence,
            composite_decision_score=composite_score,
            factors=factors,
            risks=risks or [],
            approval_required=approval_required,
            suggested_action="REQUEST_APPROVAL" if approval_required else "AUTONOMOUS_EXECUTE",
        )


decision_engine = DecisionEngine()
