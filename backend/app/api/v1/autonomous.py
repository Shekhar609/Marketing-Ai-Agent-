"""
Autonomous Agents, Memory, Experiments, and Optimization API Router
Corresponds to Master Specification Sections 20, 23, 27, 28, 46, and 36.

Provides endpoints for:
- POST /api/v1/orchestrator/plan       — Multi-agent goal decomposition & growth plan synthesis (Section 20)
- POST /api/v1/decisions/evaluate      — 8-factor autonomous decision evaluation & approval gating (Section 27)
- POST /api/v1/experiments/create      — Create A/B or multivariate marketing experiment (Section 28)
- POST /api/v1/experiments/{id}/eval   — Statistical experiment winner evaluation & memory promotion (Section 28)
- GET  /api/v1/memory/items            — Query persistent long-term organizational memory (Section 23)
- GET  /api/v1/memory/episodes         — Query past action and learning episodes (Section 23)
- POST /api/v1/optimization/cycle      — Trigger 12-stage autonomous self-improvement loop (Section 46)
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_current_user, get_db
from app.models.organization import Organization
from app.models.user import User

from app.agents.orchestrator import OrchestratorPlanRequest, marketing_orchestrator
from app.services.decision_engine import decision_engine
from app.services.experiment_service import experiment_service
from app.services.memory_service import memory_service
from app.services.optimization_loop import optimization_loop_service

router = APIRouter()


# --------------------------------------------------------------------------
# 1. Marketing Orchestrator Agent (Section 20)
# --------------------------------------------------------------------------

@router.post("/orchestrator/plan")
async def plan_growth_campaign(
    request: OrchestratorPlanRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Decompose high-level business objective into multi-agent task sequence,
    inter-agent communications, and a 60-day enterprise growth plan.
    """
    try:
        result = await marketing_orchestrator.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Marketing Orchestrator failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# 2. Autonomous Decision Engine (Section 27)
# --------------------------------------------------------------------------

class DecisionEvaluationRequest(BaseModel):
    recommendation: str
    reason: str
    expected_pipeline_impact: float
    estimated_cost: float
    confidence: float = 0.85
    risks: List[str] = Field(default_factory=list)


@router.post("/decisions/evaluate")
async def evaluate_decision(
    request: DecisionEvaluationRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
):
    """
    Evaluate marketing recommendation across 8 strategic dimensions and determine
    if Human-in-the-Loop approval is required.
    """
    try:
        decision = decision_engine.evaluate_recommendation(
            recommendation=request.recommendation,
            reason=request.reason,
            expected_pipeline_impact=request.expected_pipeline_impact,
            estimated_cost=request.estimated_cost,
            confidence=request.confidence,
            risks=request.risks,
        )
        return decision.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decision evaluation failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# 3. Experimentation Engine (Section 28)
# --------------------------------------------------------------------------

class ExperimentCreateRequest(BaseModel):
    name: str
    experiment_type: str = "email_subject"
    hypothesis: str
    control: str
    variants: List[str]
    target_metric: str = "conversion_rate"


@router.post("/experiments/create")
async def create_marketing_experiment(
    request: ExperimentCreateRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new A/B or multivariate marketing experiment."""
    try:
        exp = await experiment_service.create_experiment(
            db=db,
            organization_id=tenant.id,
            name=request.name,
            experiment_type=request.experiment_type,
            hypothesis=request.hypothesis,
            control=request.control,
            variants=request.variants,
            target_metric=request.target_metric,
        )
        return {
            "id": exp.id,
            "name": exp.name,
            "experiment_type": exp.experiment_type,
            "status": exp.status,
            "control": exp.control,
            "variants": exp.variants,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Experiment creation failed: {str(e)}",
        )


@router.post("/experiments/{experiment_id}/eval")
async def evaluate_marketing_experiment(
    experiment_id: str,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Statistically evaluate experiment results, determine if a variant reached
    95% significance, and promote winner to long-term memory.
    """
    try:
        return await experiment_service.evaluate_experiment(
            db=db,
            organization_id=tenant.id,
            experiment_id=experiment_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Experiment evaluation failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# 4. Memory System (Section 23)
# --------------------------------------------------------------------------

@router.get("/memory/items")
async def list_long_term_memories(
    memory_type: Optional[str] = None,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query persistent organizational long-term memory items."""
    try:
        items = await memory_service.get_long_term(
            db=db,
            organization_id=tenant.id,
            memory_type=memory_type,
        )
        return [
            {
                "id": m.id,
                "memory_type": m.memory_type,
                "key": m.key,
                "value": m.value,
                "confidence": m.confidence,
                "context": m.context,
                "created_at": m.created_at.isoformat(),
            }
            for m in items
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query memory: {str(e)}",
        )


@router.get("/memory/episodes")
async def list_episodic_memories(
    limit: int = Query(default=10, ge=1, le=50),
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve historical action episodes and learnings."""
    try:
        episodes = await memory_service.retrieve_episodes(
            db=db,
            organization_id=tenant.id,
            limit=limit,
        )
        return [
            {
                "id": ep.id,
                "task_name": ep.task_name,
                "action_taken": ep.action_taken,
                "reason": ep.reason,
                "outcome": ep.outcome,
                "what_worked": ep.what_worked,
                "what_failed": ep.what_failed,
                "impact_score": ep.impact_score,
                "created_at": ep.created_at.isoformat(),
            }
            for ep in episodes
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query episodic memories: {str(e)}",
        )


# --------------------------------------------------------------------------
# 5. Autonomous Optimization Loop (Section 46)
# --------------------------------------------------------------------------

class OptimizationCycleRequest(BaseModel):
    focus_area: Optional[str] = "Funnel Conversion & CAC Compression"


@router.post("/optimization/cycle")
async def trigger_optimization_cycle(
    request: OptimizationCycleRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a full 12-step autonomous optimization loop cycle:
    Observe -> Analyze -> Identify Problem -> Generate Options -> Predict Impact ->
    Select Action -> Approval -> Execute -> Measure -> Learn -> Update Memory -> Repeat
    """
    try:
        return await optimization_loop_service.run_optimization_cycle(
            db=db,
            organization_id=tenant.id,
            focus_area=request.focus_area,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization cycle failed: {str(e)}",
        )
