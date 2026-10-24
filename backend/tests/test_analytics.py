"""
Tests for Phase 6: Analytics, Revenue Operations, and Executive Copilot
Corresponds to Master Specification Sections 16, 29, 30, 31, 32, 33, 34, 35, 36.

Tests:
1. test_funnel_engine_calculation
2. test_multi_touch_revenue_attribution
3. test_dashboard_kpis_and_roi
4. test_report_generation_periodic
5. test_proactive_alert_engine
6. test_analytics_agent_audit_execution
7. test_ai_executive_copilot_execution
8. test_api_dashboard_endpoint
9. test_api_funnel_endpoint
10. test_api_attribution_endpoint
11. test_api_reports_endpoints
12. test_api_alerts_endpoint
13. test_api_recommendations_generate
14. test_api_copilot_query
15. test_analytics_tenant_isolation
16. test_analytics_models_persistence
"""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy import select

from app.services.analytics_service import analytics_service
from app.agents.analytics import analytics_agent
from app.agents.copilot import executive_copilot_agent
from app.models.analytics import Alert, AnalyticsEvent, Opportunity, Recommendation, Report
from app.models.campaign import Campaign
from app.models.lead import Lead
from tests.conftest import test_async_session_maker as async_session_maker


async def _onboard_org(client: AsyncClient, suffix: str = "analytics"):
    """Helper to onboard an organization and return auth headers + org id."""
    payload = {
        "organization_name": f"AIPNT Analytics Corp {suffix}",
        "organization_slug": f"aipnt-analytics-{suffix}",
        "admin_email": f"analytics_{suffix}@aipnt.in",
        "admin_password": "SecurePassword123!",
        "admin_name": f"RevOps Lead {suffix}",
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
# Service & Agent Direct Tests
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_funnel_engine_calculation(async_client: AsyncClient):
    """Test Marketing Funnel Engine (Section 29) stage progression & conversion rates."""
    headers, org_id = await _onboard_org(async_client, "funnel")
    async with async_session_maker() as db:
        funnel = await analytics_service.get_funnel_metrics(db, org_id)

    stages = [s["stage"] for s in funnel["stages"]]
    assert "Visitor" in stages
    assert "Lead" in stages
    assert "MQL" in stages
    assert "SQL" in stages
    assert "Opportunity" in stages
    assert "Customer" in stages
    assert "Expansion" in stages
    assert funnel["overall_conversion_rate"] > 0
    assert funnel["lead_to_customer_rate"] > 0


@pytest.mark.asyncio
async def test_multi_touch_revenue_attribution(async_client: AsyncClient):
    """Test Revenue Attribution Engine (Section 30) across all 5 attribution models."""
    headers, org_id = await _onboard_org(async_client, "attrib")
    async with async_session_maker() as db:
        for model in ["first_touch", "last_touch", "linear", "time_decay", "w_shaped"]:
            attr = await analytics_service.calculate_revenue_attribution(db, org_id, model=model)
            assert attr["attribution_model"] == model
            assert attr["total_closed_revenue"] > 0
            assert len(attr["channels"]) == 3
            total_pct = sum(c["attributed_percentage"] for c in attr["channels"])
            assert 99.0 <= total_pct <= 101.0  # Sums to 100%


@pytest.mark.asyncio
async def test_dashboard_kpis_and_roi(async_client: AsyncClient):
    """Test KPI Engine & Executive Dashboard Summary (Section 31)."""
    headers, org_id = await _onboard_org(async_client, "dash")
    async with async_session_maker() as db:
        dash = await analytics_service.get_dashboard_summary(db, org_id)

    rev = dash["revenue_overview"]
    assert rev["pipeline_created"] > 0
    assert rev["cac"] > 0
    assert rev["cpl"] > 0
    assert "x" in rev["marketing_roi"]
    assert len(dash["channel_performance"]) == 3
    assert len(dash["ai_recommendations"]) >= 2


@pytest.mark.asyncio
async def test_report_generation_periodic(async_client: AsyncClient):
    """Test Automated Report Generation (Section 33) across periodic intervals."""
    headers, org_id = await _onboard_org(async_client, "rep")
    async with async_session_maker() as db:
        for rtype in ["daily", "weekly", "monthly", "quarterly"]:
            report = await analytics_service.generate_report(db, org_id, report_type=rtype)
            assert report.report_type == rtype
            assert report.title != ""
            assert "Executive Summary" in report.content_markdown
            assert len(report.key_findings) > 0


@pytest.mark.asyncio
async def test_proactive_alert_engine(async_client: AsyncClient):
    """Test Anomaly and Threshold Alert Engine (Section 34)."""
    headers, org_id = await _onboard_org(async_client, "alrt")
    async with async_session_maker() as db:
        alerts = await analytics_service.evaluate_alerts(db, org_id)

    assert len(alerts) >= 2
    types = [a.alert_type for a in alerts]
    assert "high_intent_lead" in types or "cac_increase" in types


@pytest.mark.asyncio
async def test_analytics_agent_audit_execution(async_client: AsyncClient):
    """Test Analytics Agent (Section 16) root-cause diagnostics and performance audit."""
    headers, org_id = await _onboard_org(async_client, "agent_audit")
    async with async_session_maker() as db:
        output = await analytics_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "objective": "Audit Q4 performance and explain CAC increase",
                "time_period": "Q4 2026",
                "include_rag": False,
            },
        )

    assert output.status == "completed"
    assert output.agent_name == "analytics_agent"
    assert "audit_summary" in output.result
    assert "findings" in output.result
    assert len(output.result["findings"]) >= 2
    first_f = output.result["findings"][0]
    assert "metric" in first_f
    assert "root_cause" in first_f


@pytest.mark.asyncio
async def test_ai_executive_copilot_execution(async_client: AsyncClient):
    """Test AI Executive Copilot (Section 32) natural language queries grounded in telemetry."""
    headers, org_id = await _onboard_org(async_client, "copilot_agent")
    async with async_session_maker() as db:
        output = await executive_copilot_agent.execute(
            db=db,
            organization_id=org_id,
            params={
                "query": "Where should we allocate next month's budget?",
                "include_rag": False,
            },
        )

    assert output.status == "completed"
    assert output.agent_name == "ai_executive_copilot"
    assert "answer_markdown" in output.result
    assert output.result["question"] == "Where should we allocate next month's budget?"
    assert len(output.result["suggested_follow_up_questions"]) >= 2
    assert len(output.result["action_items"]) >= 1


# --------------------------------------------------------------------------
# API Endpoint Tests (Section 36)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_dashboard_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/dashboard and GET /api/v1/analytics/dashboard."""
    headers, _ = await _onboard_org(async_client, "api_dash")

    res1 = await async_client.get("/api/v1/dashboard", headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert "revenue_overview" in data1
    assert "funnel" in data1

    res2 = await async_client.get("/api/v1/analytics/dashboard", headers=headers)
    assert res2.status_code == 200


@pytest.mark.asyncio
async def test_api_funnel_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/analytics/funnel."""
    headers, _ = await _onboard_org(async_client, "api_funnel")
    res = await async_client.get("/api/v1/analytics/funnel", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "stages" in data
    assert len(data["stages"]) == 7


@pytest.mark.asyncio
async def test_api_attribution_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/analytics/attribution."""
    headers, _ = await _onboard_org(async_client, "api_attr")
    res = await async_client.post(
        "/api/v1/analytics/attribution",
        json={"model": "w_shaped"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["attribution_model"] == "w_shaped"
    assert len(data["channels"]) == 3


@pytest.mark.asyncio
async def test_api_reports_endpoints(async_client: AsyncClient):
    """Test POST /api/v1/analytics/reports/generate and GET /api/v1/reports."""
    headers, _ = await _onboard_org(async_client, "api_reports")

    # Generate report
    gen_res = await async_client.post(
        "/api/v1/analytics/reports/generate",
        json={"report_type": "weekly"},
        headers=headers,
    )
    assert gen_res.status_code == 200
    rep_id = gen_res.json()["id"]

    # List reports
    list_res = await async_client.get("/api/v1/reports", headers=headers)
    assert list_res.status_code == 200
    reports = list_res.json()
    assert len(reports) >= 1
    assert any(r["id"] == rep_id for r in reports)


@pytest.mark.asyncio
async def test_api_alerts_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/alerts."""
    headers, _ = await _onboard_org(async_client, "api_alerts")
    res = await async_client.get("/api/v1/alerts", headers=headers)
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) >= 1


@pytest.mark.asyncio
async def test_api_recommendations_generate(async_client: AsyncClient):
    """Test POST /api/v1/recommendations/generate."""
    headers, _ = await _onboard_org(async_client, "api_recs")
    res = await async_client.post("/api/v1/recommendations/generate", headers=headers)
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) >= 2
    assert "estimated_impact" in recs[0]


@pytest.mark.asyncio
async def test_api_copilot_query(async_client: AsyncClient):
    """Test POST /api/v1/analytics/copilot/query."""
    headers, _ = await _onboard_org(async_client, "api_copilot")
    res = await async_client.post(
        "/api/v1/analytics/copilot/query",
        json={"query": "What are our biggest growth opportunities?", "include_rag": False},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "ai_executive_copilot"
    assert "answer_markdown" in data["result"]


# --------------------------------------------------------------------------
# Multi-Tenant Isolation & Persistence Tests
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analytics_tenant_isolation(async_client: AsyncClient):
    """Ensure all analytics routes block unauthenticated access."""
    endpoints = [
        ("GET", "/api/v1/dashboard"),
        ("GET", "/api/v1/analytics/funnel"),
        ("POST", "/api/v1/analytics/attribution"),
        ("GET", "/api/v1/reports"),
        ("GET", "/api/v1/alerts"),
        ("POST", "/api/v1/analytics/copilot/query"),
    ]
    for method, ep in endpoints:
        if method == "GET":
            res = await async_client.get(ep)
        else:
            res = await async_client.post(ep, json={"query": "unauth"})
        assert res.status_code == 401, f"Endpoint {ep} allowed unauthorized access!"


@pytest.mark.asyncio
async def test_analytics_models_persistence():
    """Verify database persistence for Opportunity, AnalyticsEvent, Report, Alert, Recommendation."""
    async with async_session_maker() as db:
        now = datetime.now(timezone.utc)

        # 1. Opportunity
        opp = Opportunity(
            organization_id="org-analytics-persist",
            name="Apollo Hospital AI Diagnostic Expansion",
            amount=4500000.0,
            stage="proposal",
            probability=0.6,
            expected_revenue=2700000.0,
        )
        db.add(opp)

        # 2. AnalyticsEvent
        evt = AnalyticsEvent(
            organization_id="org-analytics-persist",
            event_name="demo_request_submitted",
            funnel_stage="sql",
            channel="LinkedIn B2B",
            source="Paid Campaign",
            properties={"prospect_title": "CTO"},
        )
        db.add(evt)

        # 3. Report
        rep = Report(
            organization_id="org-analytics-persist",
            report_type="monthly",
            title="Monthly Executive Performance",
            period_start=now,
            period_end=now,
            metrics_summary={"pipeline": 10000000.0},
            content_markdown="# Monthly Report",
        )
        db.add(rep)

        # 4. Alert
        al = Alert(
            organization_id="org-analytics-persist",
            alert_type="cac_increase",
            severity="WARNING",
            title="CAC spike on display channel",
            description="Exceeded limit by 15%",
            status="ACTIVE",
        )
        db.add(al)

        # 5. Recommendation
        rec = Recommendation(
            organization_id="org-analytics-persist",
            category="budget",
            title="Reallocate ₹50k to search",
            description="High conversion potential",
            status="pending",
        )
        db.add(rec)

        await db.commit()

        # Query checks
        q_opp = await db.scalar(select(Opportunity).where(Opportunity.name == "Apollo Hospital AI Diagnostic Expansion"))
        assert q_opp is not None
        assert q_opp.amount == 4500000.0

        q_evt = await db.scalar(select(AnalyticsEvent).where(AnalyticsEvent.event_name == "demo_request_submitted"))
        assert q_evt is not None
        assert q_evt.funnel_stage == "sql"

        q_rep = await db.scalar(select(Report).where(Report.report_type == "monthly"))
        assert q_rep is not None

        q_al = await db.scalar(select(Alert).where(Alert.alert_type == "cac_increase"))
        assert q_al is not None

        q_rec = await db.scalar(select(Recommendation).where(Recommendation.category == "budget"))
        assert q_rec is not None
