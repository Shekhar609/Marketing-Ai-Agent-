"""
Sales Enablement Agent — Account Summaries, Battlecards, Call Briefs, and Objection Handling
Corresponds to Master Specification Section 15 (Agent 11).

Responsibilities:
- High-value prospect intelligence: Account Summary, Company Research, Decision Maker Profile
- Pain points, likely needs, potential objections, and counter-arguments
- Competitor battlecard and AIPNT differentiation moats
- Personalized 1-on-1 outreach templates (Sales email, LinkedIn direct message)
- Call preparation briefs with agenda, discovery questions, and closing strategies
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

class SalesEnablementRequest(BaseModel):
    """Input parameters for sales enablement asset generation."""
    account_name: str = Field(..., min_length=1)
    decision_maker_name: str
    decision_maker_title: str
    industry: Optional[str] = "Healthcare"
    estimated_deal_size: Optional[str] = "₹25,00,000 - ₹50,00,000"
    known_competitor: Optional[str] = None
    target_product: Optional[str] = "AIPNT Medical Suite"
    include_rag: bool = True


class Battlecard(BaseModel):
    """Competitive sales battlecard."""
    competitor: str
    competitor_pitch: str
    competitor_weakness: str
    aipnt_moat: str
    trap_questions_to_ask_prospect: List[str] = Field(default_factory=list)


class ObjectionHandler(BaseModel):
    """Objection handling script."""
    objection: str
    why_they_raise_it: str
    talk_track_response: str
    proof_point: str


class CallPrepBrief(BaseModel):
    """Executive call preparation brief."""
    meeting_goal: str
    discovery_questions: List[str] = Field(default_factory=list)
    value_anchors: List[str] = Field(default_factory=list)
    suggested_closing_ask: str


class SalesEnablementResponse(BaseModel):
    """Full response from sales enablement agent."""
    account_summary: str
    decision_maker_profile: Dict[str, str] = Field(default_factory=dict)
    pain_points: List[str] = Field(default_factory=list)
    likely_needs: List[str] = Field(default_factory=list)
    personalized_email_outreach: str
    personalized_linkedin_outreach: str
    call_prep_brief: CallPrepBrief
    battlecard: Battlecard
    objection_handlers: List[ObjectionHandler] = Field(default_factory=list)
    recommended_product: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.90


class SalesLLMIntermediate(BaseModel):
    """Intermediate LLM response."""
    account_overview: str
    top_pain_points: List[str] = Field(default_factory=list)
    objection_rebuttals: List[str] = Field(default_factory=list)
    discovery_questions: List[str] = Field(default_factory=list)
    sales_email: str = ""
    linkedin_msg: str = ""


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class SalesEnablementAgent(BaseAgent):
    name = "sales_enablement_agent"
    description = "Prepares account dossiers, sales battlecards, meeting briefs, and objection playbooks"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = SalesEnablementRequest(**params)

        # 1. RAG: Retrieve competitor battlecard data & product case studies
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"battlecard competitor objection {request.known_competitor or ''} {request.target_product}",
                top_k=4,
            )

        # 2. Prompting
        system_prompt = (
            "You are the Sales Enablement Agent for an enterprise revenue team. "
            "Equip account executives and SDRs with battle-tested intel, sharp objection responses, "
            "and hyper-personalized outreach. Focus on business value, compliance moats, and deal velocity."
        )

        user_prompt = (
            f"Account: {request.account_name}\n"
            f"Decision Maker: {request.decision_maker_name} ({request.decision_maker_title})\n"
            f"Industry: {request.industry}\n"
            f"Product: {request.target_product}\n"
            f"Competitor: {request.known_competitor or 'Legacy Vendor'}\n"
            f"Deal Size: {request.estimated_deal_size}\n\n"
        )
        if rag_context["context_text"] and "No relevant context" not in rag_context["context_text"]:
            user_prompt += f"Internal Battlecard Context:\n{rag_context['context_text']}\n\n"

        user_prompt += (
            "Generate:\n"
            "1. Account intelligence overview\n"
            "2. Top 3 urgent pain points for this persona\n"
            "3. High-impact discovery questions\n"
            "4. 1-to-1 cold sales email\n"
            "5. Short LinkedIn direct message"
        )

        llm_out = await self.llm_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=SalesLLMIntermediate,
            complexity=TaskComplexity.STRATEGY,
        )

        latency_ms = (time.time() - start_time) * 1000

        # 3. Assemble Battlecard
        comp_name = request.known_competitor or "Legacy Enterprise AI Vendor"
        battlecard = Battlecard(
            competitor=comp_name,
            competitor_pitch=f"{comp_name} emphasizes broad global cloud capabilities.",
            competitor_weakness="Lacks Indian ABDM certification and sovereign on-prem deployment options; high hidden egress costs.",
            aipnt_moat="100% data sovereignty in India, pre-integrated ABDM compliance, 40% lower TCO, on-prem or private cloud.",
            trap_questions_to_ask_prospect=[
                f"How does {comp_name} guarantee that patient records remain strictly within Indian jurisdiction under DPDP regulations?",
                f"What is their SLA for custom EHR and ABDM interoperability?",
            ],
        )

        # 4. Assemble Objection Handlers (Section 15)
        objections = [
            ObjectionHandler(
                objection="We already have a system in place and migration is too painful.",
                why_they_raise_it="Fear of operational disruption and IT bandwidth shortage.",
                talk_track_response="We understand completely. That's why AIPNT runs non-intrusively alongside your current EHR via standard FHIR APIs. We pilot in parallel without changing your workflow.",
                proof_point="Deployed at Apollo Health Trust in under 14 days with zero hospital downtime.",
            ),
            ObjectionHandler(
                objection="AI is too unpredictable for our clinical / compliance standards.",
                why_they_raise_it="Regulatory liability concerns and audit risk.",
                talk_track_response="AIPNT utilizes deterministic guardrails and strict Human-in-the-Loop review gates. No critical action executes without licensed human signoff.",
                proof_point="Full audit logging per Section 38 of DPDP compliance standards.",
            ),
        ]

        # 5. Call Preparation Brief
        call_prep = CallPrepBrief(
            meeting_goal=f"Qualify budget and timeline for {request.target_product} pilot at {request.account_name}.",
            discovery_questions=llm_out.discovery_questions or [
                f"How is {request.account_name} currently managing ABDM compliance audits?",
                "What is your biggest operational bottleneck in handling high patient volumes?",
                "Who else on your clinical governance committee needs to review security before a pilot?",
            ],
            value_anchors=[
                "Guaranteed sovereign data residency (DPDP & ABDM)",
                "3.8x demonstrable operational ROI within 90 days",
                "Rapid deployment with turnkey IT support",
            ],
            suggested_closing_ask="Propose a 30-day sandboxed proof-of-concept on 100 sample records.",
        )

        # 6. Response Assembly
        response = SalesEnablementResponse(
            account_summary=llm_out.account_overview or f"{request.account_name} is a leading enterprise in {request.industry}, poised for rapid digital transformation.",
            decision_maker_profile={
                "name": request.decision_maker_name,
                "title": request.decision_maker_title,
                "role_focus": "Clinical operations, IT security, and compliance efficiency",
                "likely_motivator": "Risk reduction and measurable operational savings",
            },
            pain_points=llm_out.top_pain_points or [
                "Rising regulatory scrutiny around Indian data localization",
                "High administrative overhead from manual patient records processing",
                "Fragmented software vendors with poor interoperability",
            ],
            likely_needs=[
                "Turnkey sovereign AI pipeline with Indian regulatory approvals",
                "Executive reporting dashboard to demonstrate compliance to board",
            ],
            personalized_email_outreach=llm_out.sales_email or (
                f"Subject: Solving {request.industry} data compliance for {request.account_name}\n\n"
                f"Dear {request.decision_maker_name},\n\n"
                f"As {request.decision_maker_title}, navigating new sovereign data and ABDM requirements is likely taking up significant leadership bandwidth.\n\n"
                f"We developed {request.target_product} to solve this exact challenge for tier-1 {request.industry} organizations. Our clients deployed in under 2 weeks with zero audit findings.\n\n"
                f"Would you be open to a 10-minute briefing on Tuesday to review our live compliance architecture?\n\n"
                f"Best regards,\nAIPNT Enterprise Sales"
            ),
            personalized_linkedin_outreach=llm_out.linkedin_msg or (
                f"Hi {request.decision_maker_name}, impressive work scaling {request.account_name}'s digital initiatives. "
                f"We're helping leaders in {request.industry} meet sovereign compliance while cutting admin costs by 35%. "
                f"Would love to connect and share our latest case study."
            ),
            call_prep_brief=call_prep,
            battlecard=battlecard,
            objection_handlers=objections,
            recommended_product=request.target_product,
            sources=rag_context["sources"],
            confidence=0.90,
        )

        return AgentOutput(
            agent_name=self.name,
            task="sales_enablement",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=[call_prep.suggested_closing_ask],
            latency_ms=latency_ms,
        )


sales_enablement_agent = SalesEnablementAgent()
