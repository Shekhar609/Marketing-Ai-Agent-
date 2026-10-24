"""
Evaluation, Guardrails, and Cost Tracking Database Models
Corresponds to Master Specification Sections 39, 40, 41, 42.
"""

from datetime import datetime, timezone
import enum
from typing import Any, Dict, Optional
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantMixin, TimestampMixin


class GuardrailIncidentType(str, enum.Enum):
    PROMPT_INJECTION = "prompt_injection"
    PII_DETECTED = "pii_detected"
    HALLUCINATION = "hallucination"
    DATA_LEAKAGE = "data_leakage"
    BUDGET_EXCEEDED = "budget_exceeded"
    UNAUTHORIZED_TOOL = "unauthorized_tool"


class EvaluationRun(Base, TenantMixin, TimestampMixin):
    """
    Logs evaluation results for AI agents and RAG retrieval against quality dimensions.
    """
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    eval_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # RAG, AGENT, MARKETING
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    test_case_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class GuardrailIncident(Base, TenantMixin, TimestampMixin):
    """
    Records security, safety, and guardrail interception incidents.
    """
    __tablename__ = "guardrail_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    input_preview: Mapped[str] = mapped_column(String(500), nullable=False)
    action_taken: Mapped[str] = mapped_column(String(50), default="BLOCKED", nullable=False)  # BLOCKED, SANITIZED, FLAGGED
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class CostRecord(Base, TenantMixin, TimestampMixin):
    """
    Audit record for token consumption, LLM model routing, and compute expenses.
    """
    __tablename__ = "cost_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_inr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
