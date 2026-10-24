"""
Evaluation, Guardrails & Security Telemetry API Router
Corresponds to Master Specification Sections 39, 40, 41, 42.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.cost.cost_tracker import CostTracker
from app.core.evaluation.service import EvaluationService
from app.core.guardrails.service import GuardrailsService
from app.models.evaluation import EvaluationRun, GuardrailIncident
from app.models.user import User

router = APIRouter(prefix="/evaluation", tags=["AI Evaluation, Guardrails & Security"])


# --- Schemas ---

class CheckInputRequest(BaseModel):
    prompt: str = Field(..., description="Prompt or text to scan for injection and PII")
    redact_pii: bool = Field(default=True, description="Whether to mask detected PII")


class CheckOutputRequest(BaseModel):
    output_text: str = Field(..., description="Generated text to validate for leakage and hallucination")
    context_passages: Optional[List[str]] = Field(default=None, description="Factual context for grounding verification")


class EvaluateRAGRequest(BaseModel):
    query: str
    retrieved_contexts: List[str]
    generated_answer: str
    ground_truth: Optional[str] = None


class EvaluateAgentRequest(BaseModel):
    task_prompt: str
    output_text: str
    agent_name: str = "orchestrator_agent"
    expected_elements: Optional[List[str]] = None
    reference_context: Optional[str] = None


class CalculateCostRequest(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    model_name: str = "gemini-1.5-flash"


# --- Endpoints ---

@router.post("/guardrails/check-input", summary="Scan prompt for injection attacks and PII")
async def check_input_guardrail(
    payload: CheckInputRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GuardrailsService(db)
    result = await service.check_input(
        prompt=payload.prompt,
        organization_id=str(current_user.organization_id),
        redact_pii=payload.redact_pii,
    )
    return result


@router.post("/guardrails/check-output", summary="Scan output for system leaks and hallucination")
async def check_output_guardrail(
    payload: CheckOutputRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GuardrailsService(db)
    result = await service.check_output(
        generated_output=payload.output_text,
        context_passages=payload.context_passages,
        organization_id=str(current_user.organization_id),
    )
    return result


@router.get("/guardrails/incidents", summary="List security and guardrail incidents for organization")
async def list_guardrail_incidents(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(GuardrailIncident)
        .where(GuardrailIncident.organization_id == str(current_user.organization_id))
        .order_by(GuardrailIncident.id.desc())
        .limit(limit)
    )
    res = await db.execute(q)
    incidents = res.scalars().all()
    return {
        "incidents": [
            {
                "id": inc.id,
                "incident_type": inc.incident_type,
                "severity": inc.severity,
                "input_preview": inc.input_preview,
                "action_taken": inc.action_taken,
                "details": inc.details,
                "created_at": inc.created_at,
            }
            for inc in incidents
        ]
    }


@router.post("/rag/evaluate", summary="Evaluate RAG output with RAGAS metrics")
async def evaluate_rag_endpoint(
    payload: EvaluateRAGRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvaluationService(db)
    metrics = await service.evaluate_rag(
        query=payload.query,
        retrieved_contexts=payload.retrieved_contexts,
        generated_answer=payload.generated_answer,
        ground_truth=payload.ground_truth,
        organization_id=str(current_user.organization_id),
    )
    return metrics


@router.post("/agent/evaluate", summary="Evaluate agent quality (Correctness, Groundedness, etc.)")
async def evaluate_agent_endpoint(
    payload: EvaluateAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvaluationService(db)
    result = await service.evaluate_agent(
        task_prompt=payload.task_prompt,
        output_text=payload.output_text,
        agent_name=payload.agent_name,
        organization_id=str(current_user.organization_id),
        expected_elements=payload.expected_elements,
        reference_context=payload.reference_context,
    )
    return result


@router.get("/benchmarks/run", summary="Run golden benchmark regression test suite")
async def run_benchmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = EvaluationService(db)
    report = await service.run_benchmark_suite(organization_id=str(current_user.organization_id))
    return report


@router.get("/cost/summary", summary="Retrieve tenant token consumption and financial spend summary")
async def get_cost_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    summary = await CostTracker.get_organization_spend_summary(
        db=db,
        organization_id=str(current_user.organization_id),
    )
    return summary


@router.post("/cost/calculate", summary="Calculate estimated cost for token batch")
async def calculate_cost_endpoint(
    payload: CalculateCostRequest,
):
    calc = CostTracker.calculate_cost(
        prompt_tokens=payload.prompt_tokens,
        completion_tokens=payload.completion_tokens,
        model_name=payload.model_name,
    )
    return calc
