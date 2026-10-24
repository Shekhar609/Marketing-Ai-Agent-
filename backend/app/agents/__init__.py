"""
Base Agent Framework — Shared Infrastructure for All Specialized Agents
Provides structured execution, RAG integration, tool access, observability,
and inter-agent communication.
Corresponds to Master Specification Sections 20, 47, 48, 51.
"""

import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm.base import LLMMessage, LLMResponse
from app.core.llm.router import TaskComplexity, llm_router
from app.models.agent import AgentTask, WorkflowStatus
from app.services.rag_service import rag_service

T = TypeVar("T", bound=BaseModel)


class AgentOutput(BaseModel):
    """Standardized output envelope from every agent execution."""
    agent_name: str
    task: str
    status: str = "completed"
    result: Any = None
    confidence: float = 1.0
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    token_usage: int = 0
    latency_ms: float = 0.0
    model_used: str = ""
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all specialized marketing agents.

    Every agent has:
    - A name and description for identification
    - Task complexity routing for intelligent LLM selection
    - RAG integration for grounded organizational knowledge
    - Structured output via Pydantic schemas
    - Observability with telemetry logging
    - Inter-agent communication via structured messages
    """

    name: str = "base_agent"
    description: str = "Base marketing agent"
    complexity: TaskComplexity = TaskComplexity.STRATEGY

    # ------------------------------------------------------------------
    # Core Execution
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        """Execute the agent's core logic and return structured results."""
        pass

    # ------------------------------------------------------------------
    # LLM Helpers
    # ------------------------------------------------------------------

    async def llm_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        complexity: Optional[TaskComplexity] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate unstructured text from the LLM."""
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]
        return await llm_router.generate(
            messages=messages,
            complexity=complexity or self.complexity,
            temperature=temperature,
        )

    async def llm_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        complexity: Optional[TaskComplexity] = None,
        temperature: float = 0.2,
    ) -> T:
        """Generate structured output matching a Pydantic schema."""
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]
        return await llm_router.generate_structured(
            messages=messages,
            schema=schema,
            complexity=complexity or self.complexity,
            temperature=temperature,
        )

    # ------------------------------------------------------------------
    # RAG Integration
    # ------------------------------------------------------------------

    async def retrieve_context(
        self,
        db: AsyncSession,
        organization_id: str,
        query: str,
        top_k: int = 5,
        document_type: Optional[str] = None,
        product: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve grounded context from the RAG knowledge base."""
        context = await rag_service.get_rag_context(
            db=db,
            organization_id=organization_id,
            query=query,
            top_k=top_k,
            document_type=document_type,
            product=product,
        )
        return {
            "context_text": context.context_text,
            "sources": context.sources,
            "total_tokens": context.total_tokens,
        }

    # ------------------------------------------------------------------
    # Inter-Agent Communication (Section 47)
    # ------------------------------------------------------------------

    def create_message(
        self,
        to_agent: str,
        task: str,
        findings: List[Any],
        confidence: float = 0.9,
        recommendations: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a structured inter-agent message."""
        return {
            "from_agent": self.name,
            "to_agent": to_agent,
            "task": task,
            "findings": findings,
            "confidence": confidence,
            "sources": [],
            "recommendations": recommendations or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Observability (Section 38)
    # ------------------------------------------------------------------

    async def log_task(
        self,
        db: AsyncSession,
        organization_id: str,
        run_id: str,
        task_name: str,
        input_state: Optional[Dict] = None,
        output_state: Optional[Dict] = None,
        model_used: str = "",
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        status: WorkflowStatus = WorkflowStatus.COMPLETED,
    ) -> AgentTask:
        """Persist agent task execution telemetry."""
        task = AgentTask(
            organization_id=organization_id,
            run_id=run_id,
            agent_name=self.name,
            task_name=task_name,
            status=status,
            input_state=input_state or {},
            output_state=output_state or {},
            model_used=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
        db.add(task)
        await db.flush()
        return task
