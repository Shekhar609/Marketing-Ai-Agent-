"""
Agent Execution, Approval, and Tool Schemas
Corresponds to Master Specification Section 36, 37, 38.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.agent import WorkflowStatus
from app.models.audit import ApprovalStatus, RiskLevel


class AgentRunRequest(BaseModel):
    objective: str = Field(
        ...,
        examples=["Generate 500 qualified leads for our AI customer-support SaaS in India within 60 days with a ₹5 lakh marketing budget."],
    )
    workflow_type: str = Field(default="growth_plan_60_days")


class AgentRunResponse(BaseModel):
    id: str
    organization_id: str
    objective: str
    workflow_type: str
    status: WorkflowStatus
    current_step: str
    total_tokens: int
    total_cost: float
    latency_ms: float
    state_checkpoint: Optional[Dict[str, Any]] = None
    final_output: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalResponse(BaseModel):
    id: str
    organization_id: str
    agent_name: str
    action_type: str
    risk_level: RiskLevel
    payload: Dict[str, Any]
    reason: Optional[str] = None
    status: ApprovalStatus
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_comments: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecisionRequest(BaseModel):
    comments: Optional[str] = None


class ToolInfoResponse(BaseModel):
    name: str
    description: str
    risk_level: str
    requires_approval: bool
