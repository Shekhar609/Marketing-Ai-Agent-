"""
Customer Persona Agent — ICP Profiling, Buyer Persona Generation, and Journey Mapping
Corresponds to Master Specification Section 7.

Responsibilities:
- Build Ideal Customer Profile (ICP) with firmographic data
- Generate detailed buyer personas with pain points, triggers, and criteria
- Map the full customer journey from Awareness → Expansion
- Identify preferred channels and messaging strategies per persona
"""

import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentOutput, BaseAgent
from app.core.llm.router import TaskComplexity
from app.workflows.state import PersonaAnalysisOutput


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class PersonaRequest(BaseModel):
    """Input parameters for persona analysis."""
    objective: str = Field(..., min_length=1)
    industry: Optional[str] = None
    product: Optional[str] = None
    geography: Optional[str] = "India"
    customer_type: Optional[str] = "B2B"
    include_rag: bool = True


class ICPProfile(BaseModel):
    """Ideal Customer Profile."""
    title: str
    industry: str
    company_size: str
    revenue_range: Optional[str] = None
    geography: str = "India"
    technology_stack: List[str] = Field(default_factory=list)
    buying_capacity: Optional[str] = None
    business_problems: List[str] = Field(default_factory=list)


class BuyerPersonaProfile(BaseModel):
    """Detailed buyer persona."""
    name: str
    role: str
    goals: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    buying_triggers: List[str] = Field(default_factory=list)
    objections: List[str] = Field(default_factory=list)
    decision_criteria: List[str] = Field(default_factory=list)
    preferred_channels: List[str] = Field(default_factory=list)
    content_preferences: List[str] = Field(default_factory=list)


class CustomerJourneyStage(BaseModel):
    """A stage in the customer journey."""
    stage: str
    description: str
    touchpoints: List[str] = Field(default_factory=list)
    content_types: List[str] = Field(default_factory=list)
    key_actions: List[str] = Field(default_factory=list)


class PersonaResponse(BaseModel):
    """Structured persona analysis output."""
    icp_summary: str
    icps: List[ICPProfile] = Field(default_factory=list)
    personas: List[BuyerPersonaProfile] = Field(default_factory=list)
    customer_journey: List[CustomerJourneyStage] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.85


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class CustomerPersonaAgent(BaseAgent):
    name = "customer_persona_agent"
    description = "Builds ICPs, buyer personas, and customer journey maps"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = PersonaRequest(**params)

        # 1. RAG: Retrieve customer and persona data from knowledge base
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"customer persona ICP buyer {request.product or ''} {request.industry or ''}",
                top_k=5,
                product=request.product,
            )

        # 2. Build persona analysis prompt
        system_prompt = (
            "You are the Customer Persona Agent. "
            "Build data-driven ICPs and buyer personas based on market signals. "
            "Map the complete customer journey from Awareness through Expansion. "
            "Every persona must include specific pain points, buying triggers, "
            "and decision criteria relevant to the target industry."
        )

        user_prompt = (
            f"Objective: {request.objective}\n"
            f"Industry: {request.industry or 'Not specified'}\n"
            f"Product Focus: {request.product or 'General'}\n"
            f"Geography: {request.geography}\n"
            f"Customer Type: {request.customer_type}\n\n"
        )

        if rag_context["context_text"] and rag_context["context_text"] != "No relevant context found in the knowledge base.":
            user_prompt += f"Organizational Context:\n{rag_context['context_text']}\n\n"

        user_prompt += (
            "Generate:\n"
            "1. ICP summary and profile(s)\n"
            "2. Detailed buyer personas with pain points, triggers, and criteria\n"
            "3. Customer journey stages with touchpoints\n"
            "4. Recommendations for persona-based marketing"
        )

        # 3. Generate structured personas
        persona_analysis = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=PersonaAnalysisOutput,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 4. Build full persona profiles
        personas = [
            BuyerPersonaProfile(
                name=f"Persona: {p.role}",
                role=p.role,
                pain_points=p.pain_points,
                buying_triggers=p.buying_triggers,
                decision_criteria=p.decision_criteria,
            )
            for p in persona_analysis.personas
        ]

        # 5. Generate customer journey stages
        journey = [
            CustomerJourneyStage(
                stage=stage,
                description=f"{stage} stage for {request.product or 'the product'}",
                touchpoints=["Website", "LinkedIn", "Email"],
                content_types=["Blog", "Whitepaper", "Case Study"],
                key_actions=[f"Engage {stage.lower()} prospects"],
            )
            for stage in [
                "Awareness", "Problem Recognition", "Research",
                "Evaluation", "Decision", "Purchase",
                "Onboarding", "Retention", "Expansion",
            ]
        ]

        response = PersonaResponse(
            icp_summary=persona_analysis.icp_summary,
            personas=personas,
            customer_journey=journey,
            recommendations=[
                f"Create targeted content for {p.role}" for p in persona_analysis.personas
            ],
            sources=rag_context["sources"],
        )

        return AgentOutput(
            agent_name=self.name,
            task="persona_analysis",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=response.recommendations,
            latency_ms=latency_ms,
        )


customer_persona_agent = CustomerPersonaAgent()
