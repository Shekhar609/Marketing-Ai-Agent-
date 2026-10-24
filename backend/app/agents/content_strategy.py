"""
Content Strategy Agent — Content Generation, Planning, and Asset Management
Corresponds to Master Specification Section 9.

Responsibilities:
- Generate blogs, LinkedIn posts, whitepapers, case studies, ad copy
- Every content asset includes objective, audience, funnel stage, CTA, and expected impact
- Retrieve brand guidelines from RAG before generating content
- Maintain content calendar and topic clustering
- Evaluate content quality and brand alignment
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

class ContentRequest(BaseModel):
    """Input parameters for content generation."""
    objective: str = Field(..., min_length=1)
    content_type: str = Field(
        default="blog",
        description="Type: blog, linkedin_post, whitepaper, case_study, email, ad_copy, landing_page, newsletter"
    )
    topic: Optional[str] = None
    target_audience: Optional[str] = None
    funnel_stage: str = Field(default="awareness", description="awareness, consideration, evaluation, decision, retention")
    product: Optional[str] = None
    tone: Optional[str] = None
    include_rag: bool = True


class ContentAssetOutput(BaseModel):
    """Structured content asset with full marketing metadata."""
    title: str
    content_type: str
    body: str
    objective: str
    audience: str
    funnel_stage: str
    topic: str
    cta: str
    expected_business_impact: str
    seo_keywords: List[str] = Field(default_factory=list)
    estimated_word_count: int = 0
    brand_aligned: bool = True


class ContentPlanItem(BaseModel):
    """A single item in a content calendar."""
    week: int
    content_type: str
    topic: str
    channel: str
    funnel_stage: str
    target_persona: str = ""


class ContentStrategyLLMOutput(BaseModel):
    """Schema for LLM structured output."""
    title: str = ""
    body: str = ""
    cta: str = ""
    seo_keywords: List[str] = Field(default_factory=list)
    expected_impact: str = ""


class ContentStrategyResponse(BaseModel):
    """Full content strategy output."""
    content_asset: ContentAssetOutput
    content_plan: List[ContentPlanItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.85


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class ContentStrategyAgent(BaseAgent):
    name = "content_strategy_agent"
    description = "Generates marketing content and maintains content strategy"
    complexity = TaskComplexity.STRATEGY

    # Content type templates for prompt engineering
    CONTENT_TEMPLATES = {
        "blog": "Write a professional blog post (800-1200 words)",
        "linkedin_post": "Write a compelling LinkedIn post (200-300 words)",
        "whitepaper": "Write an executive whitepaper summary (500-800 words)",
        "case_study": "Write a customer success case study",
        "email": "Write a personalized email sequence",
        "ad_copy": "Write compelling ad copy variants",
        "landing_page": "Write landing page copy with hero, benefits, social proof, and CTA",
        "newsletter": "Write a newsletter edition with key insights",
    }

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = ContentRequest(**params)

        # 1. RAG: Retrieve brand guidelines + relevant product info
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            # First retrieve brand guidelines
            brand_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"brand guidelines voice messaging tone",
                top_k=3,
                document_type="brand_guidelines",
            )
            # Then retrieve product-specific context
            product_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"{request.topic or request.objective} {request.product or ''}",
                top_k=3,
                product=request.product,
            )
            # Merge contexts
            rag_context = {
                "context_text": f"{brand_context['context_text']}\n\n{product_context['context_text']}",
                "sources": brand_context["sources"] + product_context["sources"],
                "total_tokens": brand_context["total_tokens"] + product_context["total_tokens"],
            }

        # 2. Build content generation prompt
        content_instruction = self.CONTENT_TEMPLATES.get(
            request.content_type, "Write marketing content"
        )

        system_prompt = (
            "You are the Content Strategy Agent for an enterprise AI marketing platform. "
            "Generate high-quality, brand-aligned marketing content. "
            "Every piece of content must be: specific (not generic), data-backed where possible, "
            "action-oriented with clear CTAs, and optimized for the target funnel stage. "
            "Always follow brand guidelines when provided."
        )

        user_prompt = (
            f"Task: {content_instruction}\n"
            f"Objective: {request.objective}\n"
            f"Topic: {request.topic or request.objective}\n"
            f"Target Audience: {request.target_audience or 'B2B Decision Makers'}\n"
            f"Funnel Stage: {request.funnel_stage}\n"
            f"Product: {request.product or 'Platform'}\n"
            f"Tone: {request.tone or 'Professional, authoritative, data-driven'}\n\n"
        )

        if rag_context["context_text"] and "No relevant context" not in rag_context["context_text"]:
            user_prompt += f"Brand Guidelines & Product Context:\n{rag_context['context_text']}\n\n"

        user_prompt += (
            "Generate:\n"
            "1. Title for the content\n"
            "2. Full body content\n"
            "3. Call-to-action (CTA)\n"
            "4. SEO keywords (5-8)\n"
            "5. Expected business impact"
        )

        # 3. Generate structured content
        content = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=ContentStrategyLLMOutput,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 4. Assemble content asset with marketing metadata
        asset = ContentAssetOutput(
            title=content.title,
            content_type=request.content_type,
            body=content.body,
            objective=request.objective,
            audience=request.target_audience or "B2B Decision Makers",
            funnel_stage=request.funnel_stage,
            topic=request.topic or request.objective,
            cta=content.cta,
            expected_business_impact=content.expected_impact,
            seo_keywords=content.seo_keywords,
            estimated_word_count=len(content.body.split()) if content.body else 0,
            brand_aligned=True,
        )

        # 5. Generate a mini content plan
        content_plan = [
            ContentPlanItem(
                week=i + 1,
                content_type=ct,
                topic=f"{request.topic or request.objective} — Part {i + 1}",
                channel=ch,
                funnel_stage=fs,
            )
            for i, (ct, ch, fs) in enumerate([
                ("blog", "Website", "awareness"),
                ("linkedin_post", "LinkedIn", "awareness"),
                ("whitepaper", "Email", "consideration"),
                ("case_study", "Website", "evaluation"),
            ])
        ]

        response = ContentStrategyResponse(
            content_asset=asset,
            content_plan=content_plan,
            recommendations=[
                f"Publish {request.content_type} on primary channel",
                "Repurpose content into LinkedIn carousel and email snippet",
                f"A/B test CTA: '{content.cta}' vs alternative",
                "Track conversion rate and engagement metrics post-publish",
            ],
            sources=rag_context["sources"],
        )

        return AgentOutput(
            agent_name=self.name,
            task="content_strategy",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=response.recommendations,
            latency_ms=latency_ms,
        )


content_strategy_agent = ContentStrategyAgent()
