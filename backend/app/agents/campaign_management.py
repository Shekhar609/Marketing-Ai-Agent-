"""
Campaign Management Agent — Multi-Channel Orchestration, Budget Allocation, and ROI Projections
Corresponds to Master Specification Section 13 (Agent 9).

Responsibilities:
- Plan campaigns across Google Ads, LinkedIn, Meta, Email, Organic Search, Events, Webinars
- Enforce required schema: campaign_name, objective, audience, budget, channels, message,
  creative_requirements, landing_page, kpis, target_cpl, target_cac, expected_pipeline
- Calculate optimal channel budget split, target CPL, target CAC, and pipeline yield
- Generate ad variants and creative briefs for each channel
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

class CampaignCreateRequest(BaseModel):
    """Input parameters for campaign creation."""
    objective: str = Field(..., min_length=1)
    campaign_name: Optional[str] = None
    target_audience: Optional[str] = "Decision Makers"
    total_budget: float = Field(default=500000.0, description="Budget in INR (e.g. ₹5,00,000)")
    channels: List[str] = Field(default_factory=lambda: ["LinkedIn B2B", "Google Search Ads", "Direct Sales Email"])
    product: Optional[str] = None
    target_leads: int = 500
    timeline_days: int = 60
    include_rag: bool = True


class ChannelAllocation(BaseModel):
    """Channel budget breakdown."""
    channel: str
    budget: float
    percentage: float
    target_cpl: float
    expected_leads: int
    creative_format: str


class CampaignSpecOutput(BaseModel):
    """Exact Master Spec Section 13 campaign format."""
    campaign_name: str
    objective: str
    audience: str
    budget: float
    channels: List[str]
    message: str
    creative_requirements: List[str]
    landing_page: str
    kpis: List[str]
    target_cpl: float
    target_cac: float
    expected_pipeline: float


class CampaignResponse(BaseModel):
    """Full campaign management response."""
    campaign: CampaignSpecOutput
    channel_allocations: List[ChannelAllocation] = Field(default_factory=list)
    ad_variants: List[Dict[str, str]] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.90


class CampaignLLMIntermediate(BaseModel):
    """Intermediate LLM response."""
    name: str
    core_message: str
    creative_specs: List[str] = Field(default_factory=list)
    landing_page_headline: str = ""
    kpis: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class CampaignManagementAgent(BaseAgent):
    name = "campaign_management_agent"
    description = "Orchestrates multi-channel growth campaigns with budget splits and CAC/CPL planning"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = CampaignCreateRequest(**params)

        # 1. RAG: Retrieve product features & past performance
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"campaigns pricing cpl cac budget {request.product or request.objective}",
                top_k=4,
            )

        # 2. Prompting
        system_prompt = (
            "You are the Campaign Management Agent for an autonomous marketing platform. "
            "Design structured, high-ROI marketing campaigns adhering to the master schema. "
            "Ensure realistic CAC and CPL targets, channel balance, and precise creative requirements."
        )

        user_prompt = (
            f"Objective: {request.objective}\n"
            f"Budget: ₹{request.total_budget:,.2f}\n"
            f"Target Leads: {request.target_leads}\n"
            f"Channels: {', '.join(request.channels)}\n"
            f"Audience: {request.target_audience}\n"
            f"Product Focus: {request.product or 'Enterprise AI'}\n\n"
        )
        if rag_context["context_text"] and "No relevant context" not in rag_context["context_text"]:
            user_prompt += f"Historical & Product Context:\n{rag_context['context_text']}\n\n"

        user_prompt += (
            "Generate:\n"
            "1. Punchy campaign name\n"
            "2. Core unifying campaign message\n"
            "3. Creative requirements per channel\n"
            "4. Landing page title\n"
            "5. Primary KPIs to track"
        )

        llm_out = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=CampaignLLMIntermediate,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 3. Financial calculations
        # Target CPL = budget / target_leads
        target_cpl = round(request.total_budget / max(1, request.target_leads), 2)
        # Assuming 10% lead-to-opportunity and 25% close rate = 2.5% lead-to-deal
        # Target CAC = budget / estimated deals
        est_deals = max(1, int(request.target_leads * 0.05))
        target_cac = round(request.total_budget / est_deals, 2)
        # Expected pipeline = 20x budget for healthy enterprise AI SaaS
        expected_pipeline = round(request.total_budget * 20.0, 2)

        campaign_name = request.campaign_name or llm_out.name or f"AIPNT {request.timeline_days}-Day Growth Sprint"

        # 4. Channel Allocations
        num_channels = len(request.channels) or 1
        allocations = []
        weight_map = {
            "linkedin b2b": 0.50,
            "google search ads": 0.35,
            "direct sales email": 0.15,
        }
        for ch in request.channels:
            weight = weight_map.get(ch.lower(), 1.0 / num_channels)
            chan_budget = round(request.total_budget * weight, 2)
            chan_cpl = target_cpl * 1.1 if "linkedin" in ch.lower() else target_cpl * 0.9
            chan_leads = int(chan_budget / max(1.0, chan_cpl))
            allocations.append(
                ChannelAllocation(
                    channel=ch,
                    budget=chan_budget,
                    percentage=round(weight * 100, 1),
                    target_cpl=round(chan_cpl, 2),
                    expected_leads=chan_leads,
                    creative_format="Sponsored InMail & Lead Gen Form" if "linkedin" in ch.lower() else "Responsive Search Ads",
                )
            )

        # 5. Build required Master Specification Section 13 schema
        campaign_spec = CampaignSpecOutput(
            campaign_name=campaign_name,
            objective=request.objective,
            audience=request.target_audience or "Decision Makers",
            budget=request.total_budget,
            channels=request.channels,
            message=llm_out.core_message or "Deploy Sovereign, Certified AI Infrastructure with AIPNT.",
            creative_requirements=llm_out.creative_specs or [
                "LinkedIn: 1200x628px Single Image Ad with High-Contrast Blue Theme",
                "Google Ads: 15 Responsive Search Ad Headlines and 4 Descriptions",
                "Direct Email: 3-touch personalized sequence with Calendly embed",
            ],
            landing_page=f"https://aipnt.in/campaigns/{campaign_name.lower().replace(' ', '-')}",
            kpis=llm_out.kpis or ["Leads (MQL)", "CPL (Cost Per Lead)", "Conversion Rate", "Pipeline Generated"],
            target_cpl=target_cpl,
            target_cac=target_cac,
            expected_pipeline=expected_pipeline,
        )

        response = CampaignResponse(
            campaign=campaign_spec,
            channel_allocations=allocations,
            ad_variants=[
                {
                    "channel": "LinkedIn",
                    "headline": "Sovereign AI for Indian Healthcare — ABDM Certified",
                    "body": "Accelerate clinical and administrative operations with zero compliance risk.",
                    "cta": "Request Executive Pilot",
                },
                {
                    "channel": "Google Search",
                    "headline": "Enterprise AI Platform India | Book Demo",
                    "body": "Compliant, sovereign AI deployment for healthcare and education. See ROI in 30 days.",
                    "cta": "Get Free Assessment",
                },
            ],
            risk_factors=[
                "Ad platform audience fatigue if frequency exceeds 3.5 per week",
                "Landing page drop-off if form has more than 5 fields",
            ],
            recommendations=[
                "Implement Human-in-the-Loop review for paid ad spends exceeding ₹1,00,000",
                "Enable automated conversion pixel tracking across all multi-tenant endpoints",
                "Review channel performance weekly and reallocate budget to lowest-CPL channels",
            ],
            sources=rag_context["sources"],
            confidence=0.90,
        )

        return AgentOutput(
            agent_name=self.name,
            task="campaign_management",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=response.recommendations,
            latency_ms=latency_ms,
        )


campaign_management_agent = CampaignManagementAgent()
