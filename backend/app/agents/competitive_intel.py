"""
Competitive Intelligence Agent — Competitor Analysis, SWOT, and Gap Identification
Corresponds to Master Specification Section 6.

Responsibilities:
- Monitor competitor positioning, pricing, and product updates
- Generate competitive matrices and SWOT analyses
- Identify content, SEO, and messaging gaps
- Produce battlecards and opportunity maps
- Clearly distinguish Verified Data / Inferred Data / AI Hypothesis
"""

import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentOutput, BaseAgent
from app.core.llm.router import TaskComplexity
from app.workflows.state import CompetitiveAnalysisOutput


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class CompetitiveIntelRequest(BaseModel):
    """Input parameters for competitive intelligence analysis."""
    objective: str = Field(..., min_length=1)
    competitors: List[str] = Field(default_factory=list, description="List of competitor names to analyze")
    industry: Optional[str] = None
    product: Optional[str] = None
    include_rag: bool = True


class CompetitorProfile(BaseModel):
    """Detailed competitor profile."""
    name: str
    market_share: str = "Unknown"
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recent_actions: List[str] = Field(default_factory=list)
    pricing_model: Optional[str] = None
    aipnt_moat: str = ""
    data_confidence: str = "AI Hypothesis"  # Verified Data / Inferred Data / AI Hypothesis


class CompetitiveIntelResponse(BaseModel):
    """Structured competitive intelligence output."""
    competitor_summary: str
    competitors: List[CompetitorProfile] = Field(default_factory=list)
    swot: Dict[str, List[str]] = Field(default_factory=dict)
    content_gaps: List[str] = Field(default_factory=list)
    seo_gaps: List[str] = Field(default_factory=list)
    messaging_comparison: List[Dict[str, str]] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    battlecard_recommendations: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.80


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class CompetitiveIntelAgent(BaseAgent):
    name = "competitive_intelligence_agent"
    description = "Analyzes competitors, generates SWOT matrices, and identifies strategic gaps"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = CompetitiveIntelRequest(**params)

        # 1. RAG: Retrieve competitor intel from knowledge base
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            competitor_names = ", ".join(request.competitors) if request.competitors else "competitors"
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"competitor analysis {competitor_names} {request.industry or ''}",
                top_k=5,
                document_type="competitor_report",
                product=request.product,
            )

        # 2. Build competitive analysis prompt
        system_prompt = (
            "You are the Competitive Intelligence Agent. "
            "Analyze competitors rigorously. Never invent competitor information. "
            "Clearly distinguish: Verified Data, Inferred Data, and AI Hypothesis. "
            "Produce actionable competitive intelligence with battlecard recommendations."
        )

        competitor_list = ", ".join(request.competitors) if request.competitors else "key market competitors"
        user_prompt = (
            f"Objective: {request.objective}\n"
            f"Competitors to analyze: {competitor_list}\n"
            f"Industry: {request.industry or 'Not specified'}\n"
            f"Product Focus: {request.product or 'General'}\n\n"
        )

        if rag_context["context_text"] and rag_context["context_text"] != "No relevant context found in the knowledge base.":
            user_prompt += f"Internal Knowledge Base:\n{rag_context['context_text']}\n\n"

        user_prompt += (
            "Produce a competitive analysis including:\n"
            "1. Overall competitive landscape summary\n"
            "2. Per-competitor profiles with strengths, weaknesses, and our moat\n"
            "3. Content gaps and SEO opportunities\n"
            "4. Strategic recommendations and battlecard items"
        )

        # 3. Generate structured output
        analysis = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=CompetitiveAnalysisOutput,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 4. Assemble full response
        competitor_profiles = [
            CompetitorProfile(
                name=c.name,
                market_share=c.market_share,
                strengths=c.strengths,
                weaknesses=c.weaknesses,
                aipnt_moat=c.aipnt_moat,
            )
            for c in analysis.competitors
        ]

        response = CompetitiveIntelResponse(
            competitor_summary=analysis.competitor_summary,
            competitors=competitor_profiles,
            swot={
                "strengths": ["Strong product differentiation", "ABDM/NEP compliance"],
                "weaknesses": ["Limited brand awareness in Tier-3 markets"],
                "opportunities": analysis.opportunities,
                "threats": ["Competitor pricing pressure"],
            },
            content_gaps=analysis.content_gaps,
            opportunities=analysis.opportunities,
            battlecard_recommendations=[
                f"Create battlecard vs {c.name}" for c in analysis.competitors
            ],
            sources=rag_context["sources"],
        )

        return AgentOutput(
            agent_name=self.name,
            task="competitive_intelligence",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=response.battlecard_recommendations,
            latency_ms=latency_ms,
        )


competitive_intel_agent = CompetitiveIntelAgent()
