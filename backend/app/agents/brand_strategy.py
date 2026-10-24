"""
Brand Strategy Agent — Positioning, Value Proposition, and Messaging Framework
Corresponds to Master Specification Section 8.

Responsibilities:
- Establish brand positioning and differentiation
- Define value propositions per product and audience
- Create messaging frameworks with voice and personality
- Maintain a centralized Brand Knowledge Base
- All content agents retrieve brand guidelines before generating public-facing content
"""

import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentOutput, BaseAgent
from app.core.llm.router import TaskComplexity


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class BrandStrategyRequest(BaseModel):
    """Input parameters for brand strategy generation."""
    objective: str = Field(..., min_length=1)
    product: Optional[str] = None
    target_audience: Optional[str] = None
    industry: Optional[str] = None
    include_rag: bool = True


class BrandPositioning(BaseModel):
    """Brand positioning framework."""
    positioning_statement: str
    target_audience: str
    category: str
    key_differentiators: List[str] = Field(default_factory=list)
    competitive_frame: str = ""
    reason_to_believe: str = ""


class ValueProposition(BaseModel):
    """Value proposition for a specific product or audience."""
    product: str
    headline: str
    subheadline: str
    key_benefits: List[str] = Field(default_factory=list)
    proof_points: List[str] = Field(default_factory=list)
    target_persona: str = ""


class MessagingFramework(BaseModel):
    """Brand messaging framework."""
    brand_voice: str
    brand_personality: List[str] = Field(default_factory=list)
    elevator_pitch: str = ""
    tagline: str = ""
    key_messages: List[str] = Field(default_factory=list)
    tone_guidelines: List[str] = Field(default_factory=list)
    words_to_use: List[str] = Field(default_factory=list)
    words_to_avoid: List[str] = Field(default_factory=list)


class BrandStrategyOutput(BaseModel):
    """Structured brand strategy schema for LLM output."""
    positioning_statement: str
    differentiators: List[str] = Field(default_factory=list)
    brand_voice: str = ""
    key_messages: List[str] = Field(default_factory=list)
    elevator_pitch: str = ""


class BrandStrategyResponse(BaseModel):
    """Full brand strategy output."""
    positioning: BrandPositioning
    value_propositions: List[ValueProposition] = Field(default_factory=list)
    messaging: MessagingFramework
    website_messaging: Dict[str, str] = Field(default_factory=dict)
    sales_messaging: Dict[str, str] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.85


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class BrandStrategyAgent(BaseAgent):
    name = "brand_strategy_agent"
    description = "Creates brand positioning, value propositions, and messaging frameworks"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = BrandStrategyRequest(**params)

        # 1. RAG: Retrieve brand guidelines and existing positioning
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"brand guidelines positioning messaging {request.product or ''}",
                top_k=5,
                document_type="brand_guidelines",
                product=request.product,
            )

        # 2. Build brand strategy prompt
        system_prompt = (
            "You are the Brand Strategy Agent. "
            "Create compelling brand positioning, value propositions, and messaging. "
            "Ensure brand consistency across all communications. "
            "The messaging must be specific, differentiated, and revenue-focused. "
            "Avoid generic statements. Every message should convey competitive advantage."
        )

        user_prompt = (
            f"Objective: {request.objective}\n"
            f"Product Focus: {request.product or 'All products'}\n"
            f"Target Audience: {request.target_audience or 'Decision makers'}\n"
            f"Industry: {request.industry or 'Technology / AI'}\n\n"
        )

        if rag_context["context_text"] and rag_context["context_text"] != "No relevant context found in the knowledge base.":
            user_prompt += f"Existing Brand Context:\n{rag_context['context_text']}\n\n"

        user_prompt += (
            "Generate:\n"
            "1. Brand positioning statement with differentiators\n"
            "2. Brand voice and personality traits\n"
            "3. Key messages (3-5) for the target audience\n"
            "4. Elevator pitch (30 seconds)"
        )

        # 3. Generate structured brand strategy
        brand_output = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=BrandStrategyOutput,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 4. Assemble full brand strategy
        positioning = BrandPositioning(
            positioning_statement=brand_output.positioning_statement,
            target_audience=request.target_audience or "B2B Decision Makers",
            category=request.industry or "AI Technology",
            key_differentiators=brand_output.differentiators,
            competitive_frame="The only end-to-end AI platform",
            reason_to_believe="Proven deployments across education and healthcare",
        )

        messaging = MessagingFramework(
            brand_voice=brand_output.brand_voice,
            brand_personality=["Innovative", "Trustworthy", "Data-Driven", "Sovereign"],
            elevator_pitch=brand_output.elevator_pitch,
            tagline="Intelligence. Autonomy. Growth.",
            key_messages=brand_output.key_messages,
            tone_guidelines=[
                "Professional but accessible",
                "Data-backed claims only",
                "Focus on business outcomes",
                "Highlight compliance and sovereignty",
            ],
            words_to_use=["sovereign", "certified", "autonomous", "compliance", "ROI"],
            words_to_avoid=["cheap", "basic", "simple", "just"],
        )

        value_props = [
            ValueProposition(
                product=request.product or "Platform",
                headline=brand_output.positioning_statement[:100],
                subheadline="Driving measurable growth through AI-powered marketing",
                key_benefits=brand_output.differentiators[:3],
                proof_points=["ABDM Certified", "NEP 2020 Aligned", "100+ Deployments"],
                target_persona=request.target_audience or "Decision Makers",
            )
        ]

        response = BrandStrategyResponse(
            positioning=positioning,
            value_propositions=value_props,
            messaging=messaging,
            website_messaging={
                "hero_headline": brand_output.positioning_statement[:80],
                "hero_subheadline": brand_output.elevator_pitch[:150] if brand_output.elevator_pitch else "",
                "cta_primary": "Schedule a Demo",
                "cta_secondary": "Download Whitepaper",
            },
            sales_messaging={
                "opening": brand_output.elevator_pitch or "",
                "key_benefit": brand_output.key_messages[0] if brand_output.key_messages else "",
                "closing_cta": "Let us show you a live pilot",
            },
            recommendations=[
                "Ensure all content agents retrieve these guidelines before generating copy",
                "Update website messaging to match positioning statement",
                "Create sales enablement materials aligned with messaging framework",
            ],
            sources=rag_context["sources"],
        )

        return AgentOutput(
            agent_name=self.name,
            task="brand_strategy",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=response.recommendations,
            latency_ms=latency_ms,
        )


brand_strategy_agent = BrandStrategyAgent()
