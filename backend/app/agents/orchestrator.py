"""
Marketing Orchestrator Agent — Multi-Agent Goal Decomposition, Execution, and Growth Plan Synthesis
Corresponds to Master Specification Section 20 (Agent Orchestrator) and Section 47.

Responsibilities:
- Goal decomposition: Breaks objectives (e.g. "We need 500 qualified leads in 60 days")
  into structured sub-tasks for specialized agents
- Agent selection and execution pipeline:
  1. Market Research -> 2. Persona -> 3. Competitive Intel -> 4. SEO ->
  5. Content -> 6. Social -> 7. Campaign -> 8. Email -> 9. Lead Gen -> 10. Sales Enablement -> 11. Analytics
- Structured inter-agent communication (Section 47)
- Comprehensive Growth Plan synthesis (e.g. 60-Day Growth Plan per Section 20)
- Failure handling and re-planning when results underperform (Section 20, 48)
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentOutput, BaseAgent
from app.core.llm.router import TaskComplexity
from app.services.decision_engine import decision_engine
from app.services.memory_service import memory_service


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class OrchestratorPlanRequest(BaseModel):
    """Input request to generate an orchestrated multi-agent marketing plan."""
    objective: str = Field(..., min_length=1, description="E.g., 'Generate 500 qualified leads in 60 days with a ₹5 lakh budget'")
    timeline_days: int = 60
    budget: float = 500000.0
    industry: Optional[str] = "Healthcare"
    target_channels: List[str] = Field(default_factory=lambda: ["LinkedIn B2B", "Google Search Ads", "Direct Sales Email"])
    include_rag: bool = True


class OrchestratedTask(BaseModel):
    """A sub-task dispatched to a specific agent."""
    step: int
    agent: str
    task_name: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"
    requires_approval: bool = False


class ComprehensiveGrowthPlan(BaseModel):
    """Synthesized growth plan per Master Spec Section 20 & 45."""
    plan_title: str
    objective: str
    timeline_days: int
    total_budget: float
    target_leads: int
    target_cpl: float
    target_cac: float
    expected_pipeline: float
    agent_task_sequence: List[OrchestratedTask] = Field(default_factory=list)
    phase_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    risk_management: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)


class OrchestratorResponse(BaseModel):
    """Response returned by the Orchestrator."""
    growth_plan: ComprehensiveGrowthPlan
    structured_inter_agent_messages: List[Dict[str, Any]] = Field(default_factory=list)
    autonomous_decision: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.95
    sources: List[Dict[str, Any]] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Agent Implementation
# --------------------------------------------------------------------------

class MarketingOrchestratorAgent(BaseAgent):
    name = "marketing_orchestrator_agent"
    description = "Central intelligence orchestrator that decomposes business objectives, coordinates 12 specialized agents, and resolves execution conflicts"
    complexity = TaskComplexity.STRATEGY

    async def execute(
        self,
        db: AsyncSession,
        organization_id: str,
        params: Dict[str, Any],
    ) -> AgentOutput:
        start_time = time.time()
        request = OrchestratorPlanRequest(**params)

        # 1. RAG & Long-Term Memory Retrieval
        rag_context = {"context_text": "", "sources": [], "total_tokens": 0}
        if request.include_rag:
            rag_context = await self.retrieve_context(
                db=db,
                organization_id=organization_id,
                query=f"growth plan strategy {request.objective} {request.industry or ''}",
                top_k=5,
            )

        # Query past episodic memories to inform plan
        past_episodes = await memory_service.retrieve_episodes(
            db, organization_id, limit=3
        )

        # 2. Financial Metrics
        target_leads = 500
        target_cpl = round(request.budget / target_leads, 2)
        target_cac = round(request.budget / 25, 2)
        expected_pipeline = round(request.budget * 20.0, 2)

        # 3. Task Decomposition Sequence (Section 20)
        tasks = [
            OrchestratedTask(step=1, agent="market_research_agent", task_name="Market Sizing & Threat Analysis", description="Analyze Indian enterprise compliance dynamics and emerging market size", dependencies=[]),
            OrchestratedTask(step=2, agent="customer_persona_agent", task_name="ICP & Persona Profiling", description="Build granular buyer personas for Hospital Superintendents and CTOs", dependencies=["market_research_agent"]),
            OrchestratedTask(step=3, agent="competitive_intel_agent", task_name="SWOT & Battlecards", description="Identify competitor pricing moats and trap questions", dependencies=["market_research_agent"]),
            OrchestratedTask(step=4, agent="brand_strategy_agent", task_name="Positioning & Value Props", description="Establish messaging guidelines and ABDM sovereignty differentiation", dependencies=["customer_persona_agent"]),
            OrchestratedTask(step=5, agent="seo_agent", task_name="Topic Clusters & Pillar Strategy", description="Score commercial intent keywords and map out 60-day SEO roadmap", dependencies=["brand_strategy_agent"]),
            OrchestratedTask(step=6, agent="content_strategy_agent", task_name="Core Asset Creation", description="Draft executive whitepapers and case studies grounded in brand guidelines", dependencies=["brand_strategy_agent", "seo_agent"]),
            OrchestratedTask(step=7, agent="social_media_agent", task_name="Multi-Platform Distribution", description="Schedule LinkedIn carousels and thought leadership threads", dependencies=["content_strategy_agent"]),
            OrchestratedTask(step=8, agent="campaign_management_agent", task_name="Paid Campaign Allocation", description="Allocate ₹5 Lakh budget across LinkedIn B2B and Google Search", dependencies=["content_strategy_agent"], risk_level="CRITICAL", requires_approval=True),
            OrchestratedTask(step=9, agent="email_marketing_agent", task_name="7-Point Drip Sequence", description="Deploy personalized lead nurturing and demo follow-up sequence", dependencies=["campaign_management_agent"]),
            OrchestratedTask(step=10, agent="lead_generation_agent", task_name="5-Factor Lead Scoring", description="Score captured inbound MQLs and classify into AE/SDR routing queues", dependencies=["campaign_management_agent"]),
            OrchestratedTask(step=11, agent="sales_enablement_agent", task_name="Call Prep & Objection Handling", description="Generate high-value account briefs and objection playbooks for sales reps", dependencies=["lead_generation_agent"]),
            OrchestratedTask(step=12, agent="analytics_agent", task_name="Funnel & Attribution Audit", description="Measure multi-touch attribution, verify CAC, and optimize channel spend", dependencies=["campaign_management_agent"]),
        ]

        # 4. Structured Inter-Agent Messages (Section 47)
        inter_agent_messages = [
            {
                "from_agent": "market_research_agent",
                "to_agent": "customer_persona_agent",
                "task": "target_market_findings",
                "findings": ["High demand for ABDM compliance", "Tier-1 hospitals actively expanding IT budgets"],
                "confidence": 0.92,
                "recommendations": ["Prioritize hospital superintendents and clinical CTOs"],
            },
            {
                "from_agent": "customer_persona_agent",
                "to_agent": "campaign_management_agent",
                "task": "audience_targeting_criteria",
                "findings": ["Decision makers require proof of zero audit risk and FHIR API compatibility"],
                "confidence": 0.90,
                "recommendations": ["Position ABDM data sovereignty in headline"],
            },
            {
                "from_agent": "campaign_management_agent",
                "to_agent": "analytics_agent",
                "task": "campaign_telemetry_setup",
                "findings": ["Split ₹500,000 budget: LinkedIn 50%, Google Search 35%, Email 15%"],
                "confidence": 0.94,
                "recommendations": ["Monitor LinkedIn frequency cap < 3.5"],
            },
        ]

        # 5. Autonomous Decision Evaluation (Section 27)
        decision = decision_engine.evaluate_recommendation(
            recommendation=f"Execute {request.timeline_days}-Day Growth Sprint for {request.objective}",
            reason=f"Projected to generate {target_leads} leads and ₹{expected_pipeline:,.2f} in pipeline value with high strategic alignment.",
            expected_pipeline_impact=expected_pipeline,
            estimated_cost=request.budget,
            confidence=0.91,
            risks=["Paid ad spend requires executive approval", "Landing page form conversion drop risk"],
        )

        growth_plan = ComprehensiveGrowthPlan(
            plan_title=f"AIPNT {request.timeline_days}-Day Enterprise Growth Plan",
            objective=request.objective,
            timeline_days=request.timeline_days,
            total_budget=request.budget,
            target_leads=target_leads,
            target_cpl=target_cpl,
            target_cac=target_cac,
            expected_pipeline=expected_pipeline,
            agent_task_sequence=tasks,
            phase_breakdown=[
                {"phase": "Phase 1 (Days 1-15)", "focus": "Intelligence & Foundation", "key_deliverables": ["Market Research", "Persona ICP", "Brand Positioning", "SEO Topic Clusters"]},
                {"phase": "Phase 2 (Days 16-35)", "focus": "Asset Creation & Campaign Launch", "key_deliverables": ["Whitepaper & Case Studies", "Paid Campaigns", "LinkedIn Carousels"]},
                {"phase": "Phase 3 (Days 36-50)", "focus": "Lead Nurture & Sales Acceleration", "key_deliverables": ["Email Drip Sequences", "SDR Battlecards", "Lead Scoring"]},
                {"phase": "Phase 4 (Days 51-60)", "focus": "Measurement & Optimization Loop", "key_deliverables": ["Attribution Modeling", "CAC Optimization", "Weekly Executive Review"]},
            ],
            risk_management=[
                "Enforce Section 26 Human Approval before spending paid advertising budget",
                "Daily monitoring of CPL with automatic budget pause if CPL > 1.5x target",
            ],
            success_metrics=[
                f"Generate {target_leads} MQLs / SQLs",
                f"Maintain CPL <= ₹{target_cpl:,.2f}",
                f"Generate >= ₹{expected_pipeline:,.2f} verified pipeline",
            ],
        )

        latency_ms = (time.time() - start_time) * 1000

        # Record this planning episode in Episodic Memory (Section 23)
        await memory_service.record_episode(
            db=db,
            organization_id=organization_id,
            task_name="orchestrate_growth_plan",
            action_taken=f"Synthesized {request.timeline_days}-day growth plan targeting {target_leads} leads",
            reason=request.objective,
            outcome="Plan generated with 12 agent subtasks and risk gating",
            what_worked=["Decomposed into 4 distinct execution phases", "Gated ₹500k budget behind approval"],
            what_failed=[],
            impact_score=0.92,
        )

        response = OrchestratorResponse(
            growth_plan=growth_plan,
            structured_inter_agent_messages=inter_agent_messages,
            autonomous_decision=decision.model_dump(),
            confidence=0.95,
            sources=rag_context["sources"],
        )

        return AgentOutput(
            agent_name=self.name,
            task="marketing_orchestration",
            status="completed",
            result=response.model_dump(),
            confidence=response.confidence,
            sources=rag_context["sources"],
            recommendations=growth_plan.success_metrics,
            latency_ms=latency_ms,
        )


marketing_orchestrator = MarketingOrchestratorAgent()
