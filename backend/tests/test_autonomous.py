"""
Tests for Phase 7: Autonomous Agent, Memory System, Experimentation Engine, and Optimization Loop
Corresponds to Master Specification Sections 20, 23, 27, 28, 46, 35, 36.

Tests:
1. test_short_term_memory
2. test_long_term_memory_persistence
3. test_episodic_memory_learning
4. test_autonomous_decision_engine_8_factors
5. test_experimentation_engine_lifecycle
6. test_marketing_orchestrator_agent
7. test_autonomous_optimization_loop_12_stages
8. test_api_orchestrator_plan
9. test_api_decisions_evaluate
10. test_api_experiments_create_and_eval
11. test_api_memory_endpoints
12. test_api_optimization_cycle
13. test_autonomous_tenant_isolation
14. test_autonomous_models_persistence
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.services.memory_service import memory_service
from app.services.decision_engine import decision_engine
from app.services.experiment_service import experiment_service
from app.services.optimization_loop import optimization_loop_service
from app.agents.orchestrator import marketing_orchestrator

from app.models.autonomous import EpisodicMemory, Experiment, ExperimentResult, MemoryItem
from tests.conftest import test_async_session_maker as async_session_maker


async def _onboard_org(client: AsyncClient, suffix: str = "auto"):
    """Helper to onboard an organization and return auth headers + org id."""
    payload = {
        "organization_name": f"AIPNT Autonomous Corp {suffix}",
        "organization_slug": f"aipnt-auto-{suffix}",
        "admin_email": f"auto_{suffix}@aipnt.in",
        "admin_password": "SecurePassword123!",
        "admin_name": f"Autonomous Ops {suffix}",
        "monthly_budget": 500000.0,
        "monthly_leads_target": 500,
        "revenue_target": 10000000.0,
    }
    res = await client.post("/api/v1/auth/onboard", json=payload)
    assert res.status_code == 201
    token = res.json()["access_token"]
    org_id = res.json()["organization"]["id"]
    return {"Authorization": f"Bearer {token}"}, org_id


# --------------------------------------------------------------------------
# 1. Memory System Tests (Section 23)
# --------------------------------------------------------------------------

def test_short_term_memory():
    """Verify short-term active working memory store."""
    session_id = "test-session-123"
    memory_service.set_short_term(session_id, "current_step", "Auditing CAC")
    memory_service.set_short_term(session_id, "active_budget", 500000.0)

    assert memory_service.get_short_term(session_id, "current_step") == "Auditing CAC"
    assert memory_service.get_short_term(session_id, "active_budget") == 500000.0

    memory_service.clear_short_term(session_id)
    assert memory_service.get_short_term(session_id, "current_step") is None


@pytest.mark.asyncio
async def test_long_term_memory_persistence(async_client: AsyncClient):
    """Verify persistent long-term memory for preferences and brand rules."""
    headers, org_id = await _onboard_org(async_client, "ltm")
    async with async_session_maker() as db:
        item = await memory_service.save_long_term(
            db=db,
            organization_id=org_id,
            memory_type="brand_rule",
            key="tone_mandate",
            value={"rule": "Must always mention sovereign ABDM compliance in healthcare copy"},
            confidence=0.98,
        )
        assert item.id is not None

        # Retrieve and verify
        memories = await memory_service.get_long_term(db, org_id, key="tone_mandate")
        assert len(memories) == 1
        assert memories[0].value["rule"].startswith("Must always mention")


@pytest.mark.asyncio
async def test_episodic_memory_learning(async_client: AsyncClient):
    """Verify episodic memory captures what worked, what failed, and outcomes."""
    headers, org_id = await _onboard_org(async_client, "epm")
    async with async_session_maker() as db:
        episode = await memory_service.record_episode(
            db=db,
            organization_id=org_id,
            task_name="paid_campaign_launch",
            action_taken="Allocated ₹3,00,000 to LinkedIn Sponsored Content",
            reason="High target density of Indian Hospital Superintendents",
            outcome="Generated 184 MQLs at ₹1,630 CPL",
            what_worked=["Case study carousel format", "Title targeting CTOs"],
            what_failed=["Generic banner creative yielded 0.8% CTR"],
            impact_score=0.91,
        )
        assert episode.id is not None

        # Retrieve
        episodes = await memory_service.retrieve_episodes(db, org_id, task_name="paid_campaign_launch")
        assert len(episodes) == 1
        assert "Case study carousel format" in episodes[0].what_worked


# --------------------------------------------------------------------------
# 2. Autonomous Decision Engine Tests (Section 27)
# --------------------------------------------------------------------------

def test_autonomous_decision_engine_8_factors():
    """Verify 8-factor evaluation, composite scoring, and risk approval gating."""
    # Action requiring approval (budget shift of ₹1,50,000 > ₹1,00,000 threshold)
    decision_large = decision_engine.evaluate_recommendation(
        recommendation="Increase paid ads budget by ₹1,50,000",
        reason="Capture high-intent Q4 search surges",
        expected_pipeline_impact=1500000.0,
        estimated_cost=150000.0,
        confidence=0.88,
        risks=["High capital commitment", "Audience saturation risk"],
    )
    assert decision_large.approval_required is True
    assert decision_large.composite_decision_score > 0
    assert decision_large.factors.revenue_impact_score > 0
    assert decision_large.factors.strategic_alignment > 0
    assert decision_large.factors.confidence == 0.88

    # Low-risk action executing autonomously without approval
    decision_low = decision_engine.evaluate_recommendation(
        recommendation="Update meta tags and internal links on blog",
        reason="Improve organic search crawl efficiency",
        expected_pipeline_impact=120000.0,
        estimated_cost=5000.0,
        confidence=0.95,
        risks=[],
    )
    assert decision_low.approval_required is False
    assert decision_low.suggested_action == "AUTONOMOUS_EXECUTE"


# --------------------------------------------------------------------------
# 3. Experimentation Engine Tests (Section 28)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_experimentation_engine_lifecycle(async_client: AsyncClient):
    """Verify experiment creation, statistical evaluation, and memory promotion."""
    headers, org_id = await _onboard_org(async_client, "exp")
    async with async_session_maker() as db:
        # Create experiment
        exp = await experiment_service.create_experiment(
            db=db,
            organization_id=org_id,
            name="Landing Page Hero Headline Test",
            experiment_type="landing_page",
            hypothesis="Mentioning ABDM certification will increase conversion by >20%",
            control="Deploy Enterprise AI Today",
            variants=["Sovereign ABDM-Certified AI Platform for Hospitals", "AI Made Simple for Healthcare"],
        )
        assert exp.id is not None
        assert exp.status == "running"

        # Evaluate experiment
        eval_res = await experiment_service.evaluate_experiment(db, org_id, exp.id)
        assert eval_res["status"] == "completed"
        assert eval_res["winner_variant"] == "Variant A"
        assert eval_res["confidence"] >= 0.95

        # Verify winner was automatically saved in long-term memory
        memories = await memory_service.get_long_term(db, org_id, memory_type="successful_messaging")
        assert len(memories) >= 1
        assert "Landing Page Hero Headline Test" in memories[0].value["experiment_name"]


# --------------------------------------------------------------------------
# 4. Marketing Orchestrator Agent Tests (Section 20)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_marketing_orchestrator_agent(async_client: AsyncClient):
    """Test goal decomposition into 12 agent subtasks and 60-day growth plan."""
    headers, org_id = await _onboard_org(async_client, "orch")
    async with async_session_maker() as db:
        output = await marketing_orchestrator.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Generate 500 qualified leads in 60 days with a ₹5 lakh marketing budget",
                "timeline_days": 60,
                "budget": 500000.0,
                "industry": "Healthcare",
                "include_rag": False,
            },
        )

    assert output.status == "completed"
    assert output.agent_name == "marketing_orchestrator_agent"
    plan = output.result["growth_plan"]
    assert plan["total_budget"] == 500000.0
    assert plan["target_leads"] == 500
    assert plan["target_cpl"] == 1000.0
    assert len(plan["agent_task_sequence"]) == 12  # All 12 specialized agents coordinated
    assert len(plan["phase_breakdown"]) == 4      # 4 distinct execution phases
    assert len(output.result["structured_inter_agent_messages"]) >= 3


# --------------------------------------------------------------------------
# 5. Autonomous Optimization Loop Tests (Section 46)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_autonomous_optimization_loop_12_stages(async_client: AsyncClient):
    """Test the complete 12-stage self-improvement loop: Observe -> Repeat."""
    headers, org_id = await _onboard_org(async_client, "opt_loop")
    async with async_session_maker() as db:
        loop_res = await optimization_loop_service.run_optimization_cycle(
            db=db,
            organization_id=org_id,
            focus_area="Funnel Conversion & CAC Compression",
        )

    assert loop_res["overall_status"] == "CYCLE_COMPLETED"
    cycle = loop_res["optimization_cycle"]
    assert len(cycle) == 12
    step_names = [s["name"] for s in cycle]
    expected_steps = [
        "OBSERVE", "ANALYZE", "IDENTIFY PROBLEM", "GENERATE OPTIONS",
        "PREDICT IMPACT", "SELECT ACTION", "APPROVAL", "EXECUTE",
        "MEASURE", "LEARN", "UPDATE MEMORY", "REPEAT"
    ]
    assert step_names == expected_steps
    assert "selected_decision" in loop_res


# --------------------------------------------------------------------------
# 6. API Endpoint Tests (Section 36)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_orchestrator_plan(async_client: AsyncClient):
    """Test POST /api/v1/orchestrator/plan."""
    headers, _ = await _onboard_org(async_client, "api_orch")
    payload = {
        "objective": "Launch MedTech platform in Tier-2 Indian cities",
        "timeline_days": 60,
        "budget": 400000.0,
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/orchestrator/plan", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "marketing_orchestrator_agent"
    assert len(data["result"]["growth_plan"]["agent_task_sequence"]) == 12


@pytest.mark.asyncio
async def test_api_decisions_evaluate(async_client: AsyncClient):
    """Test POST /api/v1/decisions/evaluate."""
    headers, _ = await _onboard_org(async_client, "api_dec")
    payload = {
        "recommendation": "Shift ₹40,000 from Display to Google Ads",
        "reason": "Higher conversion propensity",
        "expected_pipeline_impact": 350000.0,
        "estimated_cost": 40000.0,
        "confidence": 0.90,
    }
    res = await async_client.post("/api/v1/decisions/evaluate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "composite_decision_score" in data
    assert "factors" in data


@pytest.mark.asyncio
async def test_api_experiments_create_and_eval(async_client: AsyncClient):
    """Test POST /api/v1/experiments/create and POST /api/v1/experiments/{id}/eval."""
    headers, _ = await _onboard_org(async_client, "api_exp")

    # Create
    create_payload = {
        "name": "Email Subject Line Test Q4",
        "experiment_type": "email_subject",
        "hypothesis": "Urgency increases open rates by 15%",
        "control": "AIPNT Q4 Update",
        "variants": ["Action Required: New Compliance Rules for 2026", "Quick Question for Dr. {{last_name}}"],
    }
    res1 = await async_client.post("/api/v1/experiments/create", json=create_payload, headers=headers)
    assert res1.status_code == 200
    exp_id = res1.json()["id"]

    # Evaluate
    res2 = await async_client.post(f"/api/v1/experiments/{exp_id}/eval", headers=headers)
    assert res2.status_code == 200
    assert "results" in res2.json()


@pytest.mark.asyncio
async def test_api_memory_endpoints(async_client: AsyncClient):
    """Test GET /api/v1/memory/items and GET /api/v1/memory/episodes."""
    headers, _ = await _onboard_org(async_client, "api_mem")

    res1 = await async_client.get("/api/v1/memory/items", headers=headers)
    assert res1.status_code == 200

    res2 = await async_client.get("/api/v1/memory/episodes", headers=headers)
    assert res2.status_code == 200


@pytest.mark.asyncio
async def test_api_optimization_cycle(async_client: AsyncClient):
    """Test POST /api/v1/optimization/cycle."""
    headers, _ = await _onboard_org(async_client, "api_cycle")
    res = await async_client.post(
        "/api/v1/optimization/cycle",
        json={"focus_area": "Full-Funnel Velocity"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] == "CYCLE_COMPLETED"
    assert len(data["optimization_cycle"]) == 12


# --------------------------------------------------------------------------
# Multi-Tenant Isolation & Persistence Tests
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_autonomous_tenant_isolation(async_client: AsyncClient):
    """Ensure autonomous endpoints block unauthenticated access."""
    endpoints = [
        ("POST", "/api/v1/orchestrator/plan"),
        ("POST", "/api/v1/decisions/evaluate"),
        ("POST", "/api/v1/experiments/create"),
        ("GET", "/api/v1/memory/items"),
        ("GET", "/api/v1/memory/episodes"),
        ("POST", "/api/v1/optimization/cycle"),
    ]
    for method, ep in endpoints:
        if method == "GET":
            res = await async_client.get(ep)
        else:
            res = await async_client.post(ep, json={"objective": "unauth"})
        assert res.status_code == 401, f"Endpoint {ep} allowed unauthenticated access!"


@pytest.mark.asyncio
async def test_autonomous_models_persistence():
    """Verify database persistence for MemoryItem, EpisodicMemory, Experiment, ExperimentResult."""
    async with async_session_maker() as db:
        # 1. MemoryItem
        mem = MemoryItem(
            organization_id="org-auto-persist",
            memory_type="preference",
            key="preferred_channels",
            value={"channels": ["LinkedIn B2B", "Google Search Ads"]},
            confidence=0.95,
        )
        db.add(mem)

        # 2. EpisodicMemory
        ep = EpisodicMemory(
            organization_id="org-auto-persist",
            task_name="campaign_audit",
            action_taken="Shifted budget",
            reason="CAC optimization",
            outcome="CAC dropped by 14%",
            what_worked=["Shifted to search"],
            what_failed=[],
            impact_score=0.94,
        )
        db.add(ep)

        # 3. Experiment & ExperimentResult
        exp = Experiment(
            organization_id="org-auto-persist",
            name="CTA Test",
            experiment_type="cta",
            hypothesis="Low friction CTA converts better",
            control="Schedule Demo",
            variants=["Get Free Assessment"],
        )
        db.add(exp)
        await db.flush()

        res = ExperimentResult(
            experiment_id=exp.id,
            variant_name="Variant A",
            sample_size=500,
            conversions=35,
            conversion_rate=0.07,
            uplift=40.0,
            statistical_significance=98.0,
        )
        db.add(res)
        await db.commit()

        # Query back
        q_mem = await db.scalar(select(MemoryItem).where(MemoryItem.organization_id == "org-auto-persist"))
        assert q_mem is not None
        assert q_mem.key == "preferred_channels"

        q_ep = await db.scalar(select(EpisodicMemory).where(EpisodicMemory.organization_id == "org-auto-persist"))
        assert q_ep is not None
        assert q_ep.impact_score == 0.94

        q_exp = await db.scalar(select(Experiment).where(Experiment.name == "CTA Test"))
        assert q_exp is not None
        assert len(q_exp.variants) == 1
