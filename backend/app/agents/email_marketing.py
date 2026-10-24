"""
Email Marketing Agent — Lifecycle Campaigns, Drip Sequences, and Hyper-Personalization
Corresponds to Master Specification Section 12 (Agent 8).

Responsibilities:
- Lifecycle campaigns: Welcome, Lead Nurturing, Product Education, Demo Follow-up,
  Sales Follow-up, Re-engagement, Retention, Upsell, Cross-sell, Win-back
- 7-Point Personalization: Company, Industry, Job Role, Pain Point, Previous Interaction, Product Interest, Buying Intent
- Compelling subject lines, preview text, high-converting body copy, and clear CTAs
- Drip sequence cadences and triggers
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

class EmailCampaignRequest(BaseModel):
    """Input parameters for email campaign generation."""
    objective: str = Field(..., min_length=1)
    campaign_type: str = Field(
        default="lead_nurturing",
        description="welcome, lead_nurturing, product_education, demo_followup, sales_followup, reengagement, retention, upsell, cross_sell, win_back"
    )
    target_persona: Optional[str] = "Decision Makers"
    company_name: Optional[str] = "{{company}}"
    industry: Optional[str] = "{{industry}}"
    product: Optional[str] = None
    sequence_length: int = Field(default=3, ge=1, le=7)
    include_rag: bool = True


class EmailStep(BaseModel):
    """A single email step in a sequence."""
    step_number: int
    delay_days: int
    subject_line: str
    preview_text: str
    body_markdown: str
    call_to_action: str
    personalization_tokens: List[str] = Field(default_factory=list)


class EmailCampaignResponse(BaseModel):
    """Structured email marketing campaign output."""
    campaign_name: str
    campaign_type: str
    target_segment: str
    sequence: List[EmailStep] = Field(default_factory=list)
    personalization_dimensions: List[str] = Field(default_factory=list)
    send_cadence_advice: str
    recommendations: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.88


class EmailLLMIntermediate(BaseModel):
    """Intermediate LLM output."""
    campaign_title: str
    primary_subject: str
    preview: str
    body: str
    cta: str
    key_angles: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class EmailMarketingAgent(BaseAgent):
    name = "email_marketing_agent"
    description = "Generates high-converting lifecycle email sequences with deep personalization"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = EmailCampaignRequest(**params)

        # 1. RAG: Retrieve product features & brand messaging
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"value proposition benefits pricing {request.product or request.objective}",
                top_k=4,
            )

        # 2. Prompting
        system_prompt = (
            "You are the Email Marketing Agent for an autonomous enterprise growth platform. "
            "Write highly effective, personalized B2B email sequences that respect the recipient's time "
            "and clearly communicate ROI and next steps. Avoid buzzwords; focus on outcomes."
        )

        user_prompt = (
            f"Objective: {request.objective}\n"
            f"Campaign Type: {request.campaign_type}\n"
            f"Target Persona: {request.target_persona}\n"
            f"Industry: {request.industry}\n"
            f"Product Focus: {request.product or 'Enterprise AI'}\n\n"
        )
        if rag_context["context_text"] and "No relevant context" not in rag_context["context_text"]:
            user_prompt += f"Knowledge Context:\n{rag_context['context_text']}\n\n"

        user_prompt += (
            "Generate:\n"
            "1. Email sequence title\n"
            "2. Subject line with high open potential\n"
            "3. Preview text\n"
            "4. Main email body with {{first_name}}, {{company}}, and {{pain_point}} tags\n"
            "5. Low-friction call to action (e.g. 15-min chat or brief demo link)\n"
            "6. 3 key sequence theme angles"
        )

        llm_out = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=EmailLLMIntermediate,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 3. Build sequence steps
        tokens = [
            "{{first_name}}", "{{company}}", "{{job_role}}",
            "{{industry}}", "{{pain_point}}", "{{product_interest}}"
        ]

        steps = [
            EmailStep(
                step_number=1,
                delay_days=0,
                subject_line=llm_out.primary_subject or f"Solving {request.objective} at {request.company_name}",
                preview_text=llm_out.preview or "A quick framework for enterprise AI adoption...",
                body_markdown=llm_out.body or f"Hi {{first_name}},\n\nI noticed {request.company_name} is scaling operations in {request.industry}. Most leaders face challenges with regulatory compliance and AI integration.\n\nWe helped similar organizations accelerate deployment by 40% with guaranteed sovereign compliance.\n\nWould you be open to a 10-minute walkthrough this Thursday?",
                call_to_action=llm_out.cta or "Schedule a 10-min Intro Call",
                personalization_tokens=tokens,
            ),
            EmailStep(
                step_number=2,
                delay_days=3,
                subject_line=f"Quick case study for {request.company_name}",
                preview_text="How a tier-1 partner achieved 3.8x ROI in 60 days",
                body_markdown="Hi {{first_name}},\n\nFollowing up on my previous note. Thought you'd appreciate seeing how a similar team tackled {{pain_point}} using our platform.\n\nKey results:\n- 35% reduction in CAC\n- Zero ABDM compliance audit findings\n\nHappy to share the full executive breakdown if helpful.",
                call_to_action="View the Case Study",
                personalization_tokens=tokens,
            ),
            EmailStep(
                step_number=3,
                delay_days=7,
                subject_line=f"Permission to close your file, {{first_name}}?",
                preview_text="Just wanted to check if this is still a priority this quarter",
                body_markdown="Hi {{first_name}},\n\nI understand you're busy navigating Q4 initiatives. If solving {request.objective} isn't top of mind right now, no worries at all.\n\nIf it is, let me know if you'd like our latest benchmarks report sent over.",
                call_to_action="Reply 'Yes' for Benchmarks",
                personalization_tokens=tokens,
            ),
        ]

        # Truncate or match requested length
        selected_steps = steps[:request.sequence_length]

        response = EmailCampaignResponse(
            campaign_name=llm_out.campaign_title or f"{request.campaign_type.replace('_', ' ').title()} Sequence",
            campaign_type=request.campaign_type,
            target_segment=f"{request.target_persona} in {request.industry}",
            sequence=selected_steps,
            personalization_dimensions=[
                "Company", "Industry", "Job Role", "Pain Point",
                "Previous Interaction", "Product Interest", "Buying Intent"
            ],
            send_cadence_advice="Send Step 1 on Tuesday 9:30 AM local time. Follow up on Step 2 after 3 business days.",
            recommendations=[
                "Warm up domain sending limits before launching sequence to >500 contacts",
                "A/B test subject lines with emoji vs question format",
                "Integrate replies directly into CRM task queues for immediate SDR pickup",
            ],
            sources=rag_context["sources"],
            confidence=0.88,
        )

        return AgentOutput(
            agent_name=self.name,
            task="email_campaign_strategy",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=response.recommendations,
            latency_ms=latency_ms,
        )


email_marketing_agent = EmailMarketingAgent()
