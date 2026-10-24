"""
Agent Execution, Stateful Run, Communication, and Tool Call Models
Corresponds to Master Specification Section 35, 47, and 48.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class WorkflowStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REPLANNING = "REPLANNING"


class ToolCallStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED_AWAITING_APPROVAL = "BLOCKED_AWAITING_APPROVAL"


class AgentRun(Base, TenantMixin, TimestampMixin):
    """
    Tracks an end-to-end execution of the Autonomous Marketing Platform orchestrator.
    """
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    workflow_type: Mapped[str] = mapped_column(String(100), default="growth_plan_60_days")
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus),
        default=WorkflowStatus.PENDING,
        nullable=False,
        index=True
    )
    current_step: Mapped[str] = mapped_column(String(100), default="START")
    state_checkpoint: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    final_output: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Observability & Cost Tracking (Section 38 & 41)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AgentTask(Base, TenantMixin, TimestampMixin):
    """
    Tracks individual agent task execution within a multi-agent workflow.
    """
    __tablename__ = "agent_tasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    task_name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus),
        default=WorkflowStatus.RUNNING,
        nullable=False
    )
    input_state: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    output_state: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    prompt_version: Mapped[str] = mapped_column(String(50), default="v1.0")
    model_used: Mapped[str] = mapped_column(String(100), default="gemini-1.5-flash")
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)


class AgentMessage(Base, TenantMixin):
    """
    Inter-agent structured communication message log.
    Corresponds to Section 47: Agent Communication.
    """
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    from_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    to_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    task: Mapped[str] = mapped_column(String(150), nullable=False)
    findings: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    sources: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    recommendations: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class ToolCallRecord(Base, TenantMixin):
    """
    Audit log of all tool executions made by autonomous agents.
    Corresponds to Section 24, 25, 38.
    """
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW")
    requires_approval: Mapped[bool] = mapped_column(nullable=False, default=False)
    input_params: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    output_result: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    status: Mapped[ToolCallStatus] = mapped_column(
        Enum(ToolCallStatus),
        default=ToolCallStatus.SUCCESS,
        nullable=False
    )
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
