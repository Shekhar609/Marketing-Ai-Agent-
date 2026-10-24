"""
Tests for Phase 5: Growth Agents
Corresponds to Master Specification Sections 10, 11, 12, 13, 14, 15, 35, 36.

Tests:
1. test_seo_agent_execution
2. test_social_media_agent_execution
3. test_email_marketing_agent_execution
4. test_campaign_management_agent_execution
5. test_lead_generation_agent_execution
6. test_sales_enablement_agent_execution
7. test_seo_api_endpoint
8. test_social_api_endpoint
9. test_email_api_endpoint
10. test_campaign_api_endpoint
11. test_lead_scoring_api_endpoint
12. test_sales_enablement_api_endpoint
13. test_growth_agents_tenant_isolation
14. test_growth_models_database_persistence
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.agents.seo_agent import seo_agent
from app.agents.social_media import social_media_agent
from app.agents.email_marketing import email_marketing_agent
from app.agents.campaign_management import campaign_management_agent
from app.agents.lead_generation import lead_generation_agent
from app.agents.sales_enablement import sales_enablement_agent

from app.models.campaign import Campaign, CampaignChannel
from app.models.lead import Lead, LeadScore
from app.models.seo import Keyword, SEOReport
from app.models.social import SocialPost, SocialMetric
from app.models.email import EmailCampaign
from tests.conftest import test_async_session_maker as async_session_maker


async def _onboard_org(client: AsyncClient, suffix: str = "growth"):
    """Helper to onboard an organization and return auth headers + org id."""
    payload = {
        "organization_name": f"AIPNT Growth Corp {suffix}",
        "organization_slug": f"aipnt-growth-{suffix}",
        "admin_email": f"growth_{suffix}@aipnt.in",
        "admin_password": "SecurePassword123!",
        "admin_name": f"Growth Lead {suffix}",
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
async def test_seo_agent_execution(async_client: AsyncClient):
    """Test SEO Agent keyword scoring and topic clustering per Section 10."""
    headers, org_id = await _onboard_org(async_client, "seo")
    async with async_session_maker() as db:
        output = await seo_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Rank for sovereign healthcare AI in India",
                "seed_keywords": ["ABDM healthcare AI", "hospital software India"],
                "industry": "Healthcare",
                "include_rag": False,
            },
        )
    assert output.status == "completed"
    assert output.agent_name == "seo_agent"
    assert "scored_keywords" in output.result
    assert len(output.result["scored_keywords"]) >= 2
    assert "topic_clusters" in output.result
    assert len(output.result["topic_clusters"]) >= 1
    # Check 5-factor scoring attributes
    first_kw = output.result["scored_keywords"][0]
    assert "composite_score" in first_kw
    assert "search_intent" in first_kw


@pytest.mark.asyncio
async def test_social_media_agent_execution(async_client: AsyncClient):
    """Test Social Media Agent posts, carousels, and calendars per Section 11."""
    headers, org_id = await _onboard_org(async_client, "social")
    async with async_session_maker() as db:
        output = await social_media_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Promote NEP 2020 AI lab partnerships to Indian schools",
                "platforms": ["linkedin", "twitter"],
                "topic": "NEP 2020 STEM Labs",
                "include_rag": False,
            },
        )
    assert output.status == "completed"
    assert output.agent_name == "social_media_agent"
    assert "posts" in output.result
    assert len(output.result["posts"]) >= 2
    assert "calendar" in output.result
    assert len(output.result["calendar"]) == 5  # Mon-Fri content plan
    carousel_post = next((p for p in output.result["posts"] if p["post_type"] == "carousel"), None)
    assert carousel_post is not None
    assert len(carousel_post["carousel_slides"]) >= 4


@pytest.mark.asyncio
async def test_email_marketing_agent_execution(async_client: AsyncClient):
    """Test Email Marketing Agent lifecycle sequence and personalization per Section 12."""
    headers, org_id = await _onboard_org(async_client, "email")
    async with async_session_maker() as db:
        output = await email_marketing_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Re-engage dormant healthcare leads who downloaded whitepaper",
                "campaign_type": "reengagement",
                "sequence_length": 3,
                "include_rag": False,
            },
        )
    assert output.status == "completed"
    assert output.agent_name == "email_marketing_agent"
    assert "sequence" in output.result
    assert len(output.result["sequence"]) == 3
    assert len(output.result["personalization_dimensions"]) == 7
    step1 = output.result["sequence"][0]
    assert "{{first_name}}" in step1["body_markdown"] or "{{first_name}}" in step1["personalization_tokens"]
    assert step1["call_to_action"] != ""


@pytest.mark.asyncio
async def test_campaign_management_agent_execution(async_client: AsyncClient):
    """Test Campaign Management Agent Section 13 schema and financial calculations."""
    headers, org_id = await _onboard_org(async_client, "campaign")
    async with async_session_maker() as db:
        output = await campaign_management_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Generate 500 qualified leads with ₹5,00,000 budget",
                "total_budget": 500000.0,
                "target_leads": 500,
                "channels": ["LinkedIn B2B", "Google Search Ads", "Direct Sales Email"],
                "include_rag": False,
            },
        )
    assert output.status == "completed"
    assert output.agent_name == "campaign_management_agent"
    # Verify Section 13 Schema
    camp = output.result["campaign"]
    assert camp["budget"] == 500000.0
    assert camp["target_cpl"] == 1000.0  # ₹5,00,000 / 500 leads
    assert camp["target_cac"] > 0
    assert camp["expected_pipeline"] > 0
    assert len(camp["creative_requirements"]) > 0
    assert "channel_allocations" in output.result
    assert len(output.result["channel_allocations"]) == 3


@pytest.mark.asyncio
async def test_lead_generation_agent_execution(async_client: AsyncClient):
    """Test Lead Generation Agent 5-factor scoring and 6-tier classification per Section 14."""
    headers, org_id = await _onboard_org(async_client, "lead")
    async with async_session_maker() as db:
        output = await lead_generation_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "lead": {
                    "first_name": "Dr. Rajesh",
                    "last_name": "Sharma",
                    "email": "rajesh.sharma@apollohospitals.org",
                    "company": "Apollo Hospital Trust",
                    "job_title": "Chief Technology Officer",
                    "industry": "Healthcare",
                    "company_size": "1000-5000",
                    "source": "Website Demo Request",
                    "page_views": 8,
                    "downloaded_content": True,
                    "attended_webinar": True,
                    "requested_demo": True,
                    "pricing_page_visits": 3,
                },
                "include_rag": False,
            },
        )
    assert output.status == "completed"
    assert output.agent_name == "lead_generation_agent"
    scored = output.result["scored_lead"]
    breakdown = scored["score_breakdown"]
    assert breakdown["company_fit"] > 0
    assert breakdown["role_fit"] > 0
    assert breakdown["engagement"] > 0
    assert breakdown["intent"] > 0
    assert breakdown["behavior"] > 0
    assert scored["total_score"] >= 80.0
    assert scored["classification"] in ["Sales Qualified", "High Intent"]
    assert "suggested_action" in scored


@pytest.mark.asyncio
async def test_sales_enablement_agent_execution(async_client: AsyncClient):
    """Test Sales Enablement Agent battlecard and objection handling per Section 15."""
    headers, org_id = await _onboard_org(async_client, "sales")
    async with async_session_maker() as db:
        output = await sales_enablement_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "account_name": "Max Healthcare Network",
                "decision_maker_name": "Dr. Sunita Patel",
                "decision_maker_title": "Medical Director & Head of IT",
                "industry": "Healthcare",
                "known_competitor": "GlobalMed AI",
                "target_product": "AIPNT DigiSwasth Suite",
                "include_rag": False,
            },
        )
    assert output.status == "completed"
    assert output.agent_name == "sales_enablement_agent"
    assert "battlecard" in output.result
    battlecard = output.result["battlecard"]
    assert battlecard["competitor"] == "GlobalMed AI"
    assert battlecard["aipnt_moat"] != ""
    assert len(battlecard["trap_questions_to_ask_prospect"]) >= 2
    assert "objection_handlers" in output.result
    assert len(output.result["objection_handlers"]) >= 2
    assert "call_prep_brief" in output.result
    assert "personalized_email_outreach" in output.result


# --------------------------------------------------------------------------
# API Endpoint Tests (Section 36)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_seo_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/seo/analyze."""
    headers, _ = await _onboard_org(async_client, "api_seo")
    payload = {
        "objective": "Rank for hospital management AI in India",
        "seed_keywords": ["hospital EHR AI", "ABDM compliance software"],
        "industry": "Healthcare",
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/seo/analyze", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "seo_agent"
    assert "scored_keywords" in data["result"]


@pytest.mark.asyncio
async def test_social_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/social/generate."""
    headers, _ = await _onboard_org(async_client, "api_social")
    payload = {
        "objective": "Launch Indian AI sovereign cloud announcement",
        "platforms": ["linkedin"],
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/social/generate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "social_media_agent"
    assert len(data["result"]["posts"]) >= 1


@pytest.mark.asyncio
async def test_email_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/email/generate."""
    headers, _ = await _onboard_org(async_client, "api_email")
    payload = {
        "objective": "Welcome sequence for new EdTech platform trialists",
        "campaign_type": "welcome",
        "sequence_length": 2,
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/email/generate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "email_marketing_agent"
    assert len(data["result"]["sequence"]) == 2


@pytest.mark.asyncio
async def test_campaign_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/campaigns/create."""
    headers, _ = await _onboard_org(async_client, "api_camp")
    payload = {
        "objective": "Drive 300 hospital pilot inquiries in 45 days",
        "total_budget": 300000.0,
        "target_leads": 300,
        "channels": ["LinkedIn B2B", "Google Search Ads"],
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/campaigns/create", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "campaign_management_agent"
    assert data["result"]["campaign"]["budget"] == 300000.0


@pytest.mark.asyncio
async def test_lead_scoring_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/leads/score."""
    headers, _ = await _onboard_org(async_client, "api_lead")
    payload = {
        "lead": {
            "first_name": "Anita",
            "last_name": "Desai",
            "email": "anita.desai@schooltrust.edu.in",
            "company": "Heritage Trust K-12",
            "job_title": "Academic Director",
            "industry": "Education",
            "source": "Webinar",
            "page_views": 4,
            "downloaded_content": True,
            "attended_webinar": True,
            "requested_demo": False,
            "pricing_page_visits": 1,
        },
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/leads/score", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "lead_generation_agent"
    assert "total_score" in data["result"]["scored_lead"]


@pytest.mark.asyncio
async def test_sales_enablement_api_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/sales/enablement."""
    headers, _ = await _onboard_org(async_client, "api_sales")
    payload = {
        "account_name": "Fortis Healthcare Chain",
        "decision_maker_name": "Dr. Vikas Verma",
        "decision_maker_title": "Chief Medical Officer",
        "industry": "Healthcare",
        "include_rag": False,
    }
    res = await async_client.post("/api/v1/sales/enablement", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "sales_enablement_agent"
    assert "battlecard" in data["result"]


# --------------------------------------------------------------------------
# Multi-Tenant Isolation & Persistence Tests
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_growth_agents_tenant_isolation(async_client: AsyncClient):
    """Verify unauthenticated access is blocked with 401 across all growth endpoints."""
    endpoints = [
        "/api/v1/seo/analyze",
        "/api/v1/social/generate",
        "/api/v1/email/generate",
        "/api/v1/campaigns/create",
        "/api/v1/leads/score",
        "/api/v1/sales/enablement",
    ]
    dummy_payload = {"objective": "Unauthorized attempt"}
    for ep in endpoints:
        res = await async_client.post(ep, json=dummy_payload)
        assert res.status_code == 401, f"Endpoint {ep} allowed unauthorized access!"


@pytest.mark.asyncio
async def test_growth_models_database_persistence():
    """Verify database persistence for Campaign, Lead, Keyword, SocialPost, and EmailCampaign models."""
    async with async_session_maker() as db:
        # 1. Campaign & CampaignChannel
        camp = Campaign(
            organization_id="org-growth-persist",
            campaign_name="Q4 MedTech Growth Sprint",
            objective="Acquire 25 hospital network clients",
            audience="Hospital CIOs and Medical Directors",
            budget=500000.0,
            channels=["LinkedIn B2B", "Direct Sales Email"],
            message="Sovereign ABDM AI for Hospitals",
            target_cpl=1000.0,
            target_cac=10000.0,
            expected_pipeline=10000000.0,
        )
        db.add(camp)
        await db.flush()

        chan = CampaignChannel(
            campaign_id=camp.id,
            channel_name="LinkedIn B2B",
            allocated_budget=300000.0,
        )
        db.add(chan)

        # 2. Lead & LeadScore
        lead = Lead(
            organization_id="org-growth-persist",
            first_name="Priya",
            last_name="Nair",
            email="priya.nair@manipalhospitals.com",
            company="Manipal Health",
            job_title="Head of Clinical IT",
            industry="Healthcare",
            classification="Sales Qualified",
            current_score=78.5,
        )
        db.add(lead)
        await db.flush()

        lscore = LeadScore(
            lead_id=lead.id,
            total_score=78.5,
            company_fit=19.0,
            role_fit=18.0,
            engagement=15.0,
            intent=12.5,
            behavior=14.0,
            classification="Sales Qualified",
            reasoning="High company and role fit",
        )
        db.add(lscore)

        # 3. Keyword
        kw = Keyword(
            organization_id="org-growth-persist",
            keyword="ABDM compliant EHR software India",
            search_intent="commercial",
            search_volume=2400,
            composite_score=0.88,
        )
        db.add(kw)

        # 4. SocialPost
        spost = SocialPost(
            organization_id="org-growth-persist",
            platform="linkedin",
            post_type="thought_leadership",
            content="Why Indian hospitals are moving to sovereign AI...",
            hashtags=["#HealthTech", "#AI"],
        )
        db.add(spost)

        # 5. EmailCampaign
        email_camp = EmailCampaign(
            organization_id="org-growth-persist",
            name="Q4 ABDM Readiness Sequence",
            campaign_type="lead_nurturing",
            subject_line="Solving ABDM compliance for your hospital",
            body_html="<p>Dear {{first_name}}, here is your guide...</p>",
        )
        db.add(email_camp)

        await db.commit()

        # Query checks
        q_camp = await db.scalar(select(Campaign).where(Campaign.organization_id == "org-growth-persist"))
        assert q_camp is not None
        assert q_camp.budget == 500000.0

        q_lead = await db.scalar(select(Lead).where(Lead.email == "priya.nair@manipalhospitals.com"))
        assert q_lead is not None
        assert q_lead.current_score == 78.5

        q_kw = await db.scalar(select(Keyword).where(Keyword.keyword == "ABDM compliant EHR software India"))
        assert q_kw is not None
        assert q_kw.search_intent == "commercial"

        q_spost = await db.scalar(select(SocialPost).where(SocialPost.platform == "linkedin"))
        assert q_spost is not None

        q_email = await db.scalar(select(EmailCampaign).where(EmailCampaign.name == "Q4 ABDM Readiness Sequence"))
        assert q_email is not None
