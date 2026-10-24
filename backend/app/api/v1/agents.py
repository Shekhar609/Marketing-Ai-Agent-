"""
Agent Execution, Approvals, and Tool Orchestration Router
Corresponds to Master Specification Section 36 & 37.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_current_user, get_db, require_admin
from app.models.audit import ApprovalStatus
from app.models.organization import Organization
from app.models.user import User
from app.schemas.agent import (
    AgentRunRequest,
    AgentRunResponse,
    ApprovalDecisionRequest,
    ApprovalResponse,
    ToolInfoResponse,
)
from app.services.agent_service import agent_service
from app.tools.registry import tool_registry

router = APIRouter()


@router.post("/run", response_model=AgentRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_agent_workflow(
    request: AgentRunRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers an end-to-end multi-agent LangGraph workflow for an enterprise objective.
    Maintains tenant isolation, logs inter-agent messages, and persists execution telemetry.
    """
    run_response = await agent_service.trigger_run(
        db=db,
        organization_id=tenant.id,
        user_id=user.id,
        request=request,
    )
    return run_response


@router.get("/runs/{id}", response_model=AgentRunResponse)
async def get_agent_run(
    id: str,
    tenant: Organization = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves execution status, state checkpoints, and telemetry for an agent run."""
    return await agent_service.get_run(db, id, tenant.id)


@router.get("/approvals", response_model=List[ApprovalResponse])
async def list_pending_approvals(
    tenant: Organization = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Lists all pending Human-in-the-Loop action requests requiring review."""
    return await agent_service.list_pending_approvals(db, tenant.id)


@router.post("/approvals/{id}/approve", response_model=ApprovalResponse)
async def approve_action(
    id: str,
    decision_data: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    tenant: Organization = Depends(get_current_tenant),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin approval gate allowing a high-impact agent action to execute."""
    return await agent_service.decide_approval(
        db=db,
        approval_id=id,
        organization_id=tenant.id,
        user_id=admin_user.id,
        decision=ApprovalStatus.APPROVED,
        comments=decision_data.comments,
    )


@router.post("/approvals/{id}/reject", response_model=ApprovalResponse)
async def reject_action(
    id: str,
    decision_data: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    tenant: Organization = Depends(get_current_tenant),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin rejection of high-impact agent action, halting tool execution."""
    return await agent_service.decide_approval(
        db=db,
        approval_id=id,
        organization_id=tenant.id,
        user_id=admin_user.id,
        decision=ApprovalStatus.REJECTED,
        comments=decision_data.comments,
    )


@router.get("/tools", response_model=List[ToolInfoResponse])
async def list_mcp_tools():
    """Lists all registered MCP-compatible marketing tools and risk classifications."""
    tools = tool_registry.list_tools()
    return [ToolInfoResponse(**t) for t in tools]
