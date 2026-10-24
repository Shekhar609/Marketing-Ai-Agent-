"""
Market Research Agent — Industry Analysis, Trends, Opportunities, and Threat Assessment
Corresponds to Master Specification Section 5 (Agent 1).

Responsibilities:
- Industry research and market sizing
- Trend identification and opportunity mapping
- Threat assessment and risk analysis
- Actionable recommendations with grounded data
"""

import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentOutput, BaseAgent
from app.core.llm.router import TaskComplexity
from app.workflows.state import MarketResearchOutput


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class MarketResearchRequest(BaseModel):
    """Input parameters for market research analysis."""
    objective: str = Field(..., min_length=1, description="The business objective or market question")
    industry: Optional[str] = None
    geography: Optional[str] = "India"
    product: Optional[str] = None
    include_rag: bool = Field(default=True, description="Include RAG knowledge base context")


class MarketResearchResponse(BaseModel):
    """Structured market research output."""
    market_summary: str
    trends: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    market_size_estimate: Optional[str] = None
    growth_rate: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.85


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class MarketResearchAgent(BaseAgent):
    name = "market_research_agent"
    description = "Conducts industry research, trend analysis, and market intelligence"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = MarketResearchRequest(**params)

        # 1. Retrieve organizational context from RAG
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"market research {request.objective} {request.industry or ''} {request.product or ''}",
                top_k=5,
                document_type="marketing_report",
                product=request.product,
            )

        # 2. Build research prompt with grounded context
        system_prompt = (
            "You are the Market Research Agent for an autonomous marketing platform. "
            "Analyze markets, identify trends, and produce actionable intelligence. "
            "Be data-driven. Quantify impact when evidence allows. "
            "Clearly distinguish verified data from AI hypotheses. "
            "Never fabricate market data or statistics."
        )

        user_prompt = (
            f"Objective: {request.objective}\n"
            f"Industry: {request.industry or 'Not specified'}\n"
            f"Geography: {request.geography}\n"
            f"Product Focus: {request.product or 'General'}\n\n"
        )

        if rag_context["context_text"] and rag_context["context_text"] != "No relevant context found in the knowledge base.":
            user_prompt += (
                f"Organizational Knowledge Base Context:\n{rag_context['context_text']}\n\n"
            )

        user_prompt += (
            "Provide a comprehensive market research analysis including:\n"
            "1. Market summary with key findings\n"
            "2. Top industry trends\n"
            "3. Growth opportunities\n"
            "4. Threats and risks\n"
            "5. Recommended strategic actions"
        )

        # 3. Generate structured research output
        research = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=MarketResearchOutput,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 4. Build response with source citations
        response = MarketResearchResponse(
            market_summary=research.market_summary,
            trends=research.trends,
            opportunities=research.opportunities,
            threats=research.threats,
            recommended_actions=research.recommended_actions,
            sources=rag_context["sources"],
            confidence=0.85,
        )

        return AgentOutput(
            agent_name=self.name,
            task="market_research",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=research.recommended_actions,
            latency_ms=latency_ms,
        )


market_research_agent = MarketResearchAgent()
