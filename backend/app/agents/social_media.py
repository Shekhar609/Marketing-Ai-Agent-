"""
Social Media Agent — Multi-Platform Strategy, Content Calendars, and Engagement Generation
Corresponds to Master Specification Section 11 (Agent 7).

Responsibilities:
- Platform support: LinkedIn, Instagram, Facebook, YouTube, X
- Post formats: Single posts, multi-slide carousels, short video scripts, thought leadership
- Content calendar generation with optimal scheduling times
- Viral hooks, hashtags, and engagement CTA recommendations
- Analytics tracking guidelines (reach, CTR, shares, leads)
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

class SocialMediaRequest(BaseModel):
    """Input parameters for social media generation."""
    objective: str = Field(..., min_length=1)
    platforms: List[str] = Field(default_factory=lambda: ["linkedin", "twitter"])
    topic: Optional[str] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = "Professional, authoritative, engaging"
    post_types: List[str] = Field(default_factory=lambda: ["post", "carousel", "video_script"])
    include_rag: bool = True


class SocialPostDraft(BaseModel):
    """Detailed drafted post for a specific platform."""
    platform: str
    post_type: str  # post, carousel, video_script, thought_leadership
    content: str
    hook: str
    call_to_action: str
    hashtags: List[str] = Field(default_factory=list)
    carousel_slides: Optional[List[str]] = None
    video_script_notes: Optional[str] = None
    recommended_time_utc: str = "08:00 AM"


class ContentCalendarSlot(BaseModel):
    """Scheduled calendar entry for social distribution."""
    day: str
    platform: str
    theme: str
    format: str


class SocialMediaResponse(BaseModel):
    """Structured social media agent output."""
    campaign_summary: str
    posts: List[SocialPostDraft] = Field(default_factory=list)
    calendar: List[ContentCalendarSlot] = Field(default_factory=list)
    growth_tactics: List[str] = Field(default_factory=list)
    kpis_to_track: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.88


class SocialLLMIntermediate(BaseModel):
    """Structured output from LLM for social generation."""
    summary: str
    linkedin_text: str = ""
    twitter_text: str = ""
    hook: str = ""
    cta: str = ""
    hashtags: List[str] = Field(default_factory=list)
    carousel_points: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class SocialMediaAgent(BaseAgent):
    name = "social_media_agent"
    description = "Generates multi-platform social content, carousels, video scripts, and calendars"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = SocialMediaRequest(**params)

        # 1. RAG: Retrieve brand voice & content guidelines
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"brand guidelines voice social {request.topic or request.objective}",
                top_k=3,
                document_type="brand_guidelines",
            )

        # 2. Prompting
        system_prompt = (
            "You are the Social Media Agent for an enterprise AI platform. "
            "Craft compelling, high-converting social media posts designed for virality, authority, and B2B engagement. "
            "Write distinct content tailored specifically for each platform (e.g. insightful thought-leadership for LinkedIn, punchy takeaways for X). "
            "Always include high-impact hooks and clear calls to action."
        )

        user_prompt = (
            f"Objective: {request.objective}\n"
            f"Topic: {request.topic or request.objective}\n"
            f"Platforms: {', '.join(request.platforms)}\n"
            f"Target Audience: {request.target_audience or 'Decision Makers & Tech Leaders'}\n"
            f"Tone: {request.tone}\n\n"
        )
        if rag_context["context_text"] and "No relevant context" not in rag_context["context_text"]:
            user_prompt += f"Brand Voice Context:\n{rag_context['context_text']}\n\n"

        user_prompt += (
            "Generate:\n"
            "1. Social campaign summary\n"
            "2. LinkedIn post copy with strong opening hook\n"
            "3. X / Twitter post copy\n"
            "4. 5-step carousel slide points\n"
            "5. Relevant hashtags and CTA"
        )

        llm_out = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=SocialLLMIntermediate,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 3. Assemble platform posts
        posts = []
        if "linkedin" in [p.lower() for p in request.platforms]:
            posts.append(
                SocialPostDraft(
                    platform="linkedin",
                    post_type="thought_leadership",
                    content=llm_out.linkedin_text or f"🚀 {llm_out.hook}\n\n{request.objective}\n\nKey takeaways:\n1. Sovereign AI architecture is non-negotiable\n2. Compliance creates competitive advantage\n\n{llm_out.cta}",
                    hook=llm_out.hook or "Most enterprises fail their AI deployments for one simple reason:",
                    call_to_action=llm_out.cta or "Drop a comment or DM us to see our live benchmark.",
                    hashtags=llm_out.hashtags or ["#EnterpriseAI", "#HealthcareTech", "#EdTechIndia", "#AIStrategy"],
                    recommended_time_utc="08:30 AM",
                )
            )

        if any(p.lower() in ["twitter", "x"] for p in request.platforms):
            posts.append(
                SocialPostDraft(
                    platform="twitter",
                    post_type="post",
                    content=llm_out.twitter_text or f"Here's why sovereign AI is revolutionizing healthcare in India:\n\n1. ABDM compliance\n2. Zero data leakage\n3. 10x ROI\n\nFull breakdown below 👇",
                    hook=llm_out.hook or "Sovereign AI is revolutionizing Indian tech.",
                    call_to_action="Read the full thread below 👇",
                    hashtags=["#SovereignAI", "#TechIndia", "#HealthTech"],
                    recommended_time_utc="01:00 PM",
                )
            )

        # Multi-slide carousel draft
        posts.append(
            SocialPostDraft(
                platform="linkedin",
                post_type="carousel",
                content=f"Carousel Guide: {request.topic or request.objective}",
                hook="Swipe through the 5-step framework ➡️",
                call_to_action="Save this carousel for your next executive strategy review.",
                hashtags=["#TechLeadership", "#AIArchitecture"],
                carousel_slides=(
                    llm_out.carousel_points
                    if llm_out.carousel_points and len(llm_out.carousel_points) >= 4
                    else [
                        "Slide 1: The Enterprise Challenge",
                        "Slide 2: Compliance as a Growth Engine",
                        "Slide 3: Real-time Multi-Agent Workflows",
                        "Slide 4: Measurable Business ROI",
                        "Slide 5: Action Plan & Next Steps",
                    ]
                ),
                recommended_time_utc="03:00 PM",
            )
        )

        # 4. Weekly Content Calendar
        calendar = [
            ContentCalendarSlot(day="Monday", platform="LinkedIn", theme="Industry Insight / Thought Leadership", format="Single Image Post"),
            ContentCalendarSlot(day="Tuesday", platform="X", theme="Actionable Framework / Tweet Thread", format="Thread"),
            ContentCalendarSlot(day="Wednesday", platform="LinkedIn", theme="Educational Deep-Dive", format="Multi-Slide Carousel"),
            ContentCalendarSlot(day="Thursday", platform="YouTube / Instagram", theme="Short Tech Teaser", format="Shorts / Reel Script"),
            ContentCalendarSlot(day="Friday", platform="LinkedIn", theme="Customer Win / Weekly Roundup", format="Case Study Post"),
        ]

        response = SocialMediaResponse(
            campaign_summary=llm_out.summary or f"Multi-channel social awareness campaign supporting {request.objective}.",
            posts=posts,
            calendar=calendar,
            growth_tactics=[
                "Engage with top 10 industry influencers within 30 minutes of posting",
                "Pin thought leadership carousel to company profile page",
                "Repurpose top comments into standalone tweet threads",
            ],
            kpis_to_track=["Reach", "Engagement Rate (Target > 4.5%)", "Website CTR", "Demo Inquiries"],
            sources=rag_context["sources"],
            confidence=0.88,
        )

        return AgentOutput(
            agent_name=self.name,
            task="social_media_strategy",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=response.growth_tactics,
            latency_ms=latency_ms,
        )


social_media_agent = SocialMediaAgent()
