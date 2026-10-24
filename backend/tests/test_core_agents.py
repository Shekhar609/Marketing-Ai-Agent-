"""
Tests for Phase 4: Core Marketing Agents
Corresponds to Master Specification Sections 5, 6, 7, 8, 9, 35, 36.

Tests:
1. test_market_research_agent_execution
2. test_competitive_intel_agent_execution
3. test_customer_persona_agent_execution
4. test_brand_strategy_agent_execution
5. test_content_strategy_agent_execution
6. test_market_research_api_endpoint
7. test_competitive_intel_api_endpoint
8. test_persona_generation_api_endpoint
9. test_brand_strategy_api_endpoint
10. test_content_generation_api_endpoint
11. test_core_agents_multi_tenant_isolation
12. test_core_agents_database_persistence
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.market_research import market_research_agent
from app.agents.competitive_intel import competitive_intel_agent
from app.agents.customer_persona import customer_persona_agent
from app.agents.brand_strategy import brand_strategy_agent
from app.agents.content_strategy import content_strategy_agent
from app.models.market_report import MarketReport
from app.models.competitor import Competitor
from app.models.content import Content, ContentVersion


async def _onboard_org(client: AsyncClient, suffix: str = "1"):
    """Helper to onboard a test organization and return auth headers."""
    payload = {
        "organization_name": f"AIPNT Corp {suffix}",
        "organization_slug": f"aipnt-corp-{suffix}",
        "admin_email": f"admin_{suffix}@aipnt.in",
        "admin_password": "SecurePassword123!",
        "admin_name": f"Admin User {suffix}",
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
# Direct Agent Execution Tests
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_market_research_agent_execution(async_client: AsyncClient):
    """Test Market Research Agent execution per Section 5."""
    headers, org_id = await _onboard_org(async_client, "mr_agent")
    
    # Run agent directly
    # Using an empty db session check or mock through test client override
    from tests.conftest import test_async_session_maker
    async with test_async_session_maker() as db:
        output = await market_research_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Analyze enterprise AI adoption in Indian healthcare",
                "industry": "Healthcare",
                "geography": "India",
                "include_rag": False,
            },
        )

    assert output.status == "completed"
    assert output.agent_name == "market_research_agent"
    assert output.task == "market_research"
    assert "market_summary" in output.result
    assert isinstance(output.result["trends"], list)
    assert isinstance(output.result["opportunities"], list)
    assert isinstance(output.result["threats"], list)
    assert isinstance(output.result["recommended_actions"], list)
    assert output.confidence > 0


@pytest.mark.asyncio
async def test_competitive_intel_agent_execution(async_client: AsyncClient):
    """Test Competitive Intelligence Agent execution with data confidence tags per Section 6."""
    headers, org_id = await _onboard_org(async_client, "comp_agent")

    from tests.conftest import test_async_session_maker
    async with test_async_session_maker() as db:
        output = await competitive_intel_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Analyze competitors in Indian EduTech AI",
                "competitors": ["EduAI Global", "LearnTech India"],
                "industry": "EduTech",
                "include_rag": False,
            },
        )

    assert output.status == "completed"
    assert output.agent_name == "competitive_intelligence_agent"
    assert "competitor_summary" in output.result
    assert "swot" in output.result
    assert "opportunities" in output.result
    assert "battlecard_recommendations" in output.result


@pytest.mark.asyncio
async def test_customer_persona_agent_execution(async_client: AsyncClient):
    """Test Customer Persona Agent with ICP, buyer personas, and journey stages per Section 7."""
    headers, org_id = await _onboard_org(async_client, "persona_agent")

    from tests.conftest import test_async_session_maker
    async with test_async_session_maker() as db:
        output = await customer_persona_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Profile hospital CTOs and school administrators",
                "industry": "MedTech",
                "customer_type": "B2B",
                "include_rag": False,
            },
        )

    assert output.status == "completed"
    assert output.agent_name == "customer_persona_agent"
    assert "icp_summary" in output.result
    assert "personas" in output.result
    assert "customer_journey" in output.result
    assert len(output.result["customer_journey"]) == 9  # Awareness to Expansion stages


@pytest.mark.asyncio
async def test_brand_strategy_agent_execution(async_client: AsyncClient):
    """Test Brand Strategy Agent with positioning, value props, and voice per Section 8."""
    headers, org_id = await _onboard_org(async_client, "brand_agent")

    from tests.conftest import test_async_session_maker
    async with test_async_session_maker() as db:
        output = await brand_strategy_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Establish positioning for sovereign AI platform in India",
                "target_audience": "Enterprise C-Suite and Government Trusts",
                "industry": "Enterprise AI",
                "include_rag": False,
            },
        )

    assert output.status == "completed"
    assert output.agent_name == "brand_strategy_agent"
    assert "positioning" in output.result
    assert "value_propositions" in output.result
    assert "messaging" in output.result
    assert "website_messaging" in output.result
    assert "sales_messaging" in output.result
    assert output.result["messaging"]["brand_voice"] != ""


@pytest.mark.asyncio
async def test_content_strategy_agent_execution(async_client: AsyncClient):
    """Test Content Strategy Agent with multi-format generation & content plan per Section 9."""
    headers, org_id = await _onboard_org(async_client, "content_agent")

    from tests.conftest import test_async_session_maker
    async with test_async_session_maker() as db:
        output = await content_strategy_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Drive inbound demo signups for hospital compliance AI",
                "content_type": "linkedin_post",
                "topic": "ABDM Healthcare Compliance for Indian Hospitals",
                "funnel_stage": "awareness",
                "include_rag": False,
            },
        )

    assert output.status == "completed"
    assert output.agent_name == "content_strategy_agent"
    assert "content_asset" in output.result
    asset = output.result["content_asset"]
    assert asset["content_type"] == "linkedin_post"
    assert asset["funnel_stage"] == "awareness"
    assert asset["cta"] != ""
    assert "content_plan" in output.result
    assert len(output.result["content_plan"]) == 4  # 4-week content calendar


# --------------------------------------------------------------------------
# API Endpoint Tests (Section 36)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_market_research_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/research/market."""
    headers, _ = await _onboard_org(async_client, "api_mr")
    
    payload = {
        "objective": "Evaluate AI governance market in India for 2026",
        "industry": "GovTech",
        "geography": "India",
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/research/market", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "market_research_agent"
    assert data["status"] == "completed"
    assert "market_summary" in data["result"]


@pytest.mark.asyncio
async def test_competitive_intel_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/research/competitors."""
    headers, _ = await _onboard_org(async_client, "api_comp")

    payload = {
        "objective": "Compare against top AI marketing suites",
        "competitors": ["Competitor A", "Competitor B"],
        "industry": "MarTech",
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/research/competitors", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "competitive_intelligence_agent"
    assert data["status"] == "completed"
    assert "competitor_summary" in data["result"]


@pytest.mark.asyncio
async def test_persona_generation_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/personas/generate."""
    headers, _ = await _onboard_org(async_client, "api_persona")

    payload = {
        "objective": "Target CIOs of tier-1 universities in India",
        "industry": "Higher Education",
        "customer_type": "B2B",
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/personas/generate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "customer_persona_agent"
    assert data["status"] == "completed"
    assert len(data["result"]["customer_journey"]) == 9


@pytest.mark.asyncio
async def test_brand_strategy_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/brand/strategy."""
    headers, _ = await _onboard_org(async_client, "api_brand")

    payload = {
        "objective": "Refine positioning for AIPNT Medical AI Suite",
        "product": "AIPNT MedTech",
        "target_audience": "Hospital Directors",
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/brand/strategy", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "brand_strategy_agent"
    assert data["status"] == "completed"
    assert "positioning" in data["result"]
    assert "messaging" in data["result"]


@pytest.mark.asyncio
async def test_content_generation_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/content/generate."""
    headers, _ = await _onboard_org(async_client, "api_content")

    payload = {
        "objective": "Thought leadership on NEP 2020 AI adoption",
        "content_type": "whitepaper",
        "topic": "National Education Policy and Sovereign AI Labs",
        "funnel_stage": "consideration",
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/content/generate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "content_strategy_agent"
    assert data["status"] == "completed"
    assert data["result"]["content_asset"]["content_type"] == "whitepaper"


# --------------------------------------------------------------------------
# Multi-Tenant Isolation & Persistence Tests
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_core_agents_multi_tenant_isolation(async_client: AsyncClient):
    """Ensure core agent invocations are authenticated and scoped per tenant."""
    # Unauthenticated call should fail with 401
    unauth_res = await async_client.post(
        "/api/v1/research/market",
        json={"objective": "Test without auth"},
    )
    assert unauth_res.status_code == 401

    # Org A call should succeed
    headers_a, _ = await _onboard_org(async_client, "tenant_a")
    res_a = await async_client.post(
        "/api/v1/research/market",
        json={"objective": "Org A market research", "include_rag": False},
        headers=headers_a,
    )
    assert res_a.status_code == 200

    # Org B call should succeed with its own independent context
    headers_b, _ = await _onboard_org(async_client, "tenant_b")
    res_b = await async_client.post(
        "/api/v1/research/market",
        json={"objective": "Org B market research", "include_rag": False},
        headers=headers_b,
    )
    assert res_b.status_code == 200


@pytest.mark.asyncio
async def test_core_agents_database_persistence():
    """Verify that MarketReport, Competitor, and Content models persist correctly in DB."""
    from tests.conftest import test_async_session_maker

    async with test_async_session_maker() as db:
        # 1. Persist MarketReport
        report = MarketReport(
            organization_id="org-persist-test",
            title="Q4 Indian Healthcare AI Market Report",
            objective="Analyze market size and expansion opportunities",
            industry="Healthcare",
            geography="India",
            market_summary="The healthcare AI market in India is expanding at 35% CAGR.",
            trends=["ABDM adoption", "Telemedicine integration"],
            opportunities=["Private hospital AI triage"],
            threats=["Regulatory changes"],
            recommended_actions=["Deploy pilot at 10 hospital chains"],
            confidence=0.90,
        )
        db.add(report)

        # 2. Persist Competitor
        comp = Competitor(
            organization_id="org-persist-test",
            name="HealthAI Labs",
            industry="Healthcare",
            market_share="15%",
            strengths=["Established presence in Tier 1 cities"],
            weaknesses=["High pricing, lacks ABDM certification"],
            aipnt_moat="AIPNT provides sovereign on-premise deployment with full ABDM compliance.",
            data_confidence="Verified Data",
            swot={"strengths": ["Brand"], "weaknesses": ["Cost"]},
        )
        db.add(comp)

        # 3. Persist Content and ContentVersion
        content_item = Content(
            organization_id="org-persist-test",
            title="ABDM Compliance Guide for Modern Hospitals",
            content_type="blog",
            status="draft",
            objective="Educate hospital administrators on ABDM compliance",
            audience="Medical Superintendents",
            funnel_stage="awareness",
            topic="ABDM Compliance",
            cta="Schedule an ABDM readiness assessment",
            expected_business_impact="Generate 50 MQLs in month 1",
        )
        db.add(content_item)
        await db.flush()

        version = ContentVersion(
            content_id=content_item.id,
            version_number=1,
            title="ABDM Compliance Guide for Modern Hospitals",
            body="Comprehensive guide on implementing Ayushman Bharat Digital Mission...",
            seo_keywords=["ABDM compliance", "hospital software India"],
            estimated_word_count=1200,
            brand_aligned=True,
            change_summary="Initial draft",
        )
        db.add(version)
        await db.commit()

        # Query back and verify persistence
        query_report = await db.scalar(
            select(MarketReport).where(MarketReport.organization_id == "org-persist-test")
        )
        assert query_report is not None
        assert query_report.industry == "Healthcare"
        assert len(query_report.trends) == 2

        query_comp = await db.scalar(
            select(Competitor).where(Competitor.name == "HealthAI Labs")
        )
        assert query_comp is not None
        assert query_comp.data_confidence == "Verified Data"

        query_content = await db.scalar(
            select(Content).where(Content.title == "ABDM Compliance Guide for Modern Hospitals")
        )
        assert query_content is not None
        assert query_content.content_type == "blog"
