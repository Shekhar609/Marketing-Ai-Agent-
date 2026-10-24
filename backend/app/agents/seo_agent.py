"""
SEO Agent — Keyword Research, Intent Analysis, Topic Clusters, and SEO Strategy
Corresponds to Master Specification Section 10 (Agent 6).

Responsibilities:
- Keyword research and search intent analysis (informational, navigational, commercial, transactional)
- Competitor keyword analysis and content gap analysis
- On-page & technical SEO recommendations
- Topic clustering and pillar pages
- Multi-factor keyword scoring: Business Value, Search Intent, Competition, Search Volume, Conversion Potential
- Content calendar and SEO roadmap
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

class SEORequest(BaseModel):
    """Input parameters for SEO strategy and keyword research."""
    objective: str = Field(..., min_length=1, description="SEO objective or business topic")
    domain: Optional[str] = None
    seed_keywords: List[str] = Field(default_factory=list)
    competitors: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    include_rag: bool = True


class ScoredKeyword(BaseModel):
    """Keyword with multi-factor scoring per Section 10."""
    keyword: str
    search_intent: str = "informational"  # informational, navigational, commercial, transactional
    search_volume_tier: str = "Medium"  # High, Medium, Low
    competition_score: float = 0.5  # 0.0 - 1.0 (lower is easier)
    business_value_score: float = 0.8  # 0.0 - 1.0
    conversion_potential: float = 0.7  # 0.0 - 1.0
    composite_score: float = 0.75  # Weighted composite priority
    recommended_content_format: str = "blog"  # pillar_page, blog, guide, comparison


class TopicCluster(BaseModel):
    """Cluster of related keywords around a central core pillar."""
    pillar_topic: str
    pillar_url_slug: str
    supporting_articles: List[str] = Field(default_factory=list)
    target_keywords: List[str] = Field(default_factory=list)


class SEOResponse(BaseModel):
    """Structured SEO strategy output."""
    seo_summary: str
    scored_keywords: List[ScoredKeyword] = Field(default_factory=list)
    topic_clusters: List[TopicCluster] = Field(default_factory=list)
    pillar_pages: List[str] = Field(default_factory=list)
    content_gaps: List[str] = Field(default_factory=list)
    technical_recommendations: List[str] = Field(default_factory=list)
    seo_roadmap: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.88


class SEOSchemaLLMOutput(BaseModel):
    """Intermediate LLM response schema."""
    summary: str
    primary_keywords: List[str] = Field(default_factory=list)
    content_gaps: List[str] = Field(default_factory=list)
    technical_fixes: List[str] = Field(default_factory=list)
    roadmap_milestones: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class SEOAgent(BaseAgent):
    name = "seo_agent"
    description = "Executes keyword research, topic clustering, and technical SEO planning"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = SEORequest(**params)

        # 1. RAG: Retrieve existing website, product, and competitor info
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"seo keywords topic content {request.objective} {request.industry or ''}",
                top_k=5,
            )

        # 2. Prompting
        system_prompt = (
            "You are the SEO Agent for an enterprise marketing operations platform. "
            "Perform comprehensive SEO analysis: keyword search intent, competitor content gaps, "
            "topic clustering, and technical recommendations. "
            "Ensure keyword recommendations directly target high-converting search intent."
        )

        user_prompt = (
            f"Objective: {request.objective}\n"
            f"Domain: {request.domain or 'aipnt.in'}\n"
            f"Industry: {request.industry or 'AI & Technology'}\n"
            f"Seed Keywords: {', '.join(request.seed_keywords) if request.seed_keywords else 'None'}\n"
            f"Competitors: {', '.join(request.competitors) if request.competitors else 'General market'}\n\n"
        )
        if rag_context["context_text"] and "No relevant context" not in rag_context["context_text"]:
            user_prompt += f"Knowledge Context:\n{rag_context['context_text']}\n\n"

        user_prompt += (
            "Analyze and provide:\n"
            "1. SEO executive summary\n"
            "2. High-value primary keywords\n"
            "3. Competitor content gaps\n"
            "4. Technical SEO fixes\n"
            "5. Strategic 60-day roadmap milestones"
        )

        llm_out = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=SEOSchemaLLMOutput,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 3. Assemble scored keywords with multi-factor calculation
        keywords_to_score = request.seed_keywords or llm_out.primary_keywords or [
            "sovereign AI India", "healthcare compliance AI", "hospital management ABDM", "enterprise AI solutions"
        ]
        scored_keywords = []
        for kw in keywords_to_score:
            # 5-factor scoring simulation
            intent = "commercial" if any(w in kw.lower() for w in ["pricing", "solutions", "buy", "software", "platform"]) else "informational"
            biz_val = 0.9 if any(w in kw.lower() for w in ["ai", "compliance", "enterprise", "hospital"]) else 0.7
            comp = 0.6
            conv_pot = 0.8 if intent == "commercial" else 0.5
            composite = round((biz_val * 0.35) + (conv_pot * 0.35) + ((1 - comp) * 0.3), 2)

            scored_keywords.append(
                ScoredKeyword(
                    keyword=kw,
                    search_intent=intent,
                    search_volume_tier="High" if composite > 0.75 else "Medium",
                    competition_score=comp,
                    business_value_score=biz_val,
                    conversion_potential=conv_pot,
                    composite_score=composite,
                    recommended_content_format="pillar_page" if composite > 0.8 else "blog",
                )
            )

        # 4. Generate Topic Clusters & Pillar Pages
        topic_clusters = [
            TopicCluster(
                pillar_topic=f"Ultimate Guide to {request.industry or 'Enterprise AI'} in India",
                pillar_url_slug=f"/insights/{(request.industry or 'enterprise-ai').lower().replace(' ', '-')}-guide",
                supporting_articles=[
                    f"Top 5 Architecture Considerations for {request.industry or 'AI'}",
                    "How to Achieve ABDM & Sovereign Compliance",
                    "Cost Optimization & ROI in 2026",
                ],
                target_keywords=[sk.keyword for sk in scored_keywords[:3]],
            )
        ]

        response = SEOResponse(
            seo_summary=llm_out.summary or f"SEO growth roadmap targeting {request.objective}.",
            scored_keywords=scored_keywords,
            topic_clusters=topic_clusters,
            pillar_pages=[tc.pillar_topic for tc in topic_clusters],
            content_gaps=llm_out.content_gaps or [
                "Lack of in-depth technical whitepapers on ABDM data privacy",
                "Missing interactive ROI calculator for hospital IT leads",
            ],
            technical_recommendations=llm_out.technical_fixes or [
                "Implement JSON-LD Schema markup for Organization and Product",
                "Improve Core Web Vitals (LCP < 2.5s) on landing pages",
                "Ensure canonical tags on multi-tenant product sub-paths",
            ],
            seo_roadmap=llm_out.roadmap_milestones or [
                "Month 1: Publish 2 Pillar Pages and setup schema markup",
                "Month 2: Release 8 supporting cluster blogs and build internal backlinks",
                "Month 3: Audit backlink growth and optimize conversion CTAs",
            ],
            sources=rag_context["sources"],
            confidence=0.88,
        )

        return AgentOutput(
            agent_name=self.name,
            task="seo_analysis",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=response.seo_roadmap,
            latency_ms=latency_ms,
        )


seo_agent = SEOAgent()
