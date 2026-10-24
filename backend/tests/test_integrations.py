"""
Phase 8: Comprehensive Tests for Integrations & External Connectors
Covers:
- CRM Connectors (HubSpot, Salesforce, MockCRM)
- Web Analytics Connector (Google Analytics GA4)
- Ad Platform Connectors (Google Ads, LinkedIn, Meta)
- Email Delivery Connectors (SendGrid, SMTP)
- Real-time Notifications & Slack Connector
- Calendar & Demo Scheduling Connector
- Website Tracking Snippet & Webhook Ingestion
- Integrations Service Orchestration & Database Sync
- Integrations API Endpoints (CRUD, test, sync, webhook, tracking)
- Tool Registry MCP Integration (including high-risk CRM gate)
- Multi-Tenant Isolation
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.integrations import (
    CalendarConnector,
    GoogleAdsConnector,
    GoogleAnalyticsConnector,
    HubSpotConnector,
    LinkedInAdsConnector,
    MetaAdsConnector,
    MockCRMConnector,
    SalesforceConnector,
    SendGridConnector,
    SlackConnector,
    SMTPConnector,
    WebsiteConnector,
    get_connector,
)
from app.main import app
from app.models.analytics import AnalyticsEvent
from app.models.campaign import Campaign, CampaignMetric
from app.models.integration import (
    IntegrationCredential,
    IntegrationProvider,
    IntegrationStatus,
    IntegrationSyncLog,
    WebhookEvent,
)
from app.models.lead import Lead
from app.models.organization import Organization
from app.models.user import User
from app.services.integrations_service import IntegrationsService
from app.tools.registry import tool_registry
from tests.conftest import test_async_session_maker as async_session_maker


async def _onboard_org(client: AsyncClient, suffix: str = "integrations"):
    payload = {
        "organization_name": f"AIPNT Integrations Corp {suffix}",
        "organization_slug": f"aipnt-integrations-{suffix}",
        "admin_email": f"integrations_{suffix}@aipnt.in",
        "admin_password": "SecurePassword123!",
        "admin_name": f"Integration Lead {suffix}",
        "monthly_budget": 500000.0,
        "monthly_leads_target": 500,
        "revenue_target": 10000000.0,
    }
    res = await client.post("/api/v1/auth/onboard", json=payload)
    assert res.status_code == 201
    token = res.json()["access_token"]
    org_id = res.json()["organization"]["id"]
    return {"Authorization": f"Bearer {token}"}, org_id


# =====================================================================
# 1. Direct Connector Unit Tests
# =====================================================================

@pytest.mark.asyncio
async def test_crm_connectors_unit():
    # Mock CRM
    mock_crm = MockCRMConnector(credentials={"api_key": "mock_crm_key"})
    res_test = await mock_crm.test_connection()
    assert res_test["success"] is True
    assert "mock_acc_8849" in res_test["account_id"]

    res_sync = await mock_crm.sync()
    assert res_sync["success"] is True
    assert len(res_sync["leads"]) == 2
    assert res_sync["leads"][0]["email"] == "elena.rostova@enterprisecorp.com"

    res_push = await mock_crm.push_lead({"email": "test@lead.com", "name": "Test"})
    assert res_push["success"] is True

    # HubSpot (Mock Token)
    hs = HubSpotConnector(credentials={"access_token": "mock_hs_token"})
    hs_test = await hs.test_connection()
    assert hs_test["success"] is True
    hs_sync = await hs.sync()
    assert hs_sync["success"] is True
    assert len(hs_sync["leads"]) == 1
    hs_push = await hs.push_lead({"email": "test@lead.com"})
    assert hs_push["success"] is True

    # Salesforce (Mock Token)
    sf = SalesforceConnector(credentials={"access_token": "mock_sf_token", "instance_url": "https://mock.salesforce.com"})
    sf_test = await sf.test_connection()
    assert sf_test["success"] is True
    sf_sync = await sf.sync()
    assert sf_sync["success"] is True
    assert len(sf_sync["leads"]) == 1


@pytest.mark.asyncio
async def test_analytics_and_ads_connectors_unit():
    # GA4
    ga = GoogleAnalyticsConnector(
        credentials={"api_key": "mock_key"},
        settings={"property_id": "GA4-TEST-001"},
    )
    ga_test = await ga.test_connection()
    assert ga_test["success"] is True
    ga_sync = await ga.sync()
    assert ga_sync["success"] is True
    assert ga_sync["data"]["active_users"] > 0
    assert "Organic Search" in ga_sync["data"]["channel_groupings"]

    # Google Ads
    gads = GoogleAdsConnector(
        credentials={"developer_token": "dev_token_123"},
        settings={"customer_id": "123-456-7890"},
    )
    gads_test = await gads.test_connection()
    assert gads_test["success"] is True
    gads_sync = await gads.sync()
    assert gads_sync["success"] is True
    assert len(gads_sync["campaigns"]) == 2
    assert gads_sync["total_spend"] > 0

    # LinkedIn Ads
    li = LinkedInAdsConnector(
        credentials={"access_token": "mock_token"},
        settings={"account_id": "li_acc_99"},
    )
    li_test = await li.test_connection()
    assert li_test["success"] is True
    li_sync = await li.sync()
    assert li_sync["success"] is True

    # Meta Ads
    meta = MetaAdsConnector(
        credentials={"access_token": "mock_token"},
        settings={"ad_account_id": "act_8849"},
    )
    meta_test = await meta.test_connection()
    assert meta_test["success"] is True
    meta_sync = await meta.sync()
    assert meta_sync["success"] is True


@pytest.mark.asyncio
async def test_email_slack_calendar_website_connectors_unit():
    # SendGrid
    sg = SendGridConnector(credentials={"api_key": "mock_sendgrid_key"})
    sg_test = await sg.test_connection()
    assert sg_test["success"] is True
    sg_send = await sg.send_email(
        to_email="prospect@company.com",
        subject="AI Growth Strategy",
        html_content="<p>Hello</p>",
    )
    assert sg_send["success"] is True
    assert sg_send["status"] == "SENT"

    # SMTP
    smtp = SMTPConnector(credentials={"host": "mail.aipnt.ai", "port": 587})
    smtp_test = await smtp.test_connection()
    assert smtp_test["success"] is True

    # Slack
    slack = SlackConnector(
        credentials={"webhook_url": "mock://hooks.slack.com/services/T00/B00/X00"},
        settings={"default_channel": "#marketing-alerts"},
    )
    slack_test = await slack.test_connection()
    assert slack_test["success"] is True
    slack_msg = await slack.send_message("Testing Slack notification")
    assert slack_msg["success"] is True
    slack_alert = await slack.send_alert(
        title="High Lead Velocity", message="15 new SQLs today", severity="HIGH"
    )
    assert slack_alert["success"] is True
    slack_approval = await slack.send_approval_request(
        request_id=1,
        title="Launch Q4 Campaign",
        reason="Budget > $5000",
        risk_level="HIGH",
        approve_url="https://app.aipnt.ai/approve/1",
        reject_url="https://app.aipnt.ai/reject/1",
    )
    assert slack_approval["success"] is True

    # Calendar
    cal = CalendarConnector(credentials={"api_key": "mock_cal_key"})
    cal_test = await cal.test_connection()
    assert cal_test["success"] is True
    cal_sync = await cal.sync()
    assert cal_sync["success"] is True
    assert len(cal_sync["events"]) == 2

    # Website
    site = WebsiteConnector(settings={"domain": "aipnt.ai"})
    site_test = await site.test_connection()
    assert site_test["success"] is True
    snippet = WebsiteConnector.generate_tracking_snippet(organization_id=42)
    assert "orgId: '42'" in snippet
    assert "<script>" in snippet


# =====================================================================
# 2. Integrations Service Lifecycle & Sync Pipelines
# =====================================================================

@pytest.mark.asyncio
async def test_integrations_service_full_lifecycle():
    async with async_session_maker() as db:
        org = Organization(name="OmniCorp Global", slug="omnicorp-global")
        db.add(org)
        await db.commit()
        await db.refresh(org)

        service = IntegrationsService(db)

        # 1. Connect CRM
        crm_cred = await service.connect_provider(
            organization_id=org.id,
            provider="mock_crm",
            name="Primary Mock CRM",
            credentials={"api_key": "mock_key_123"},
            settings={"sync_frequency": "hourly"},
        )
        assert crm_cred.id is not None
        assert crm_cred.status == IntegrationStatus.CONNECTED

        # 2. Connect Slack
        slack_cred = await service.connect_provider(
            organization_id=org.id,
            provider="slack",
            name="Marketing Slack Notifications",
            credentials={"webhook_url": "mock://slack.com/hook"},
            settings={"default_channel": "#growth-team"},
        )
        assert slack_cred.id is not None

        # 3. Connect Google Analytics
        ga_cred = await service.connect_provider(
            organization_id=org.id,
            provider="google_analytics",
            name="GA4 Production Stream",
            credentials={"api_key": "mock_key"},
            settings={"property_id": "GA4-998811"},
        )
        assert ga_cred.id is not None

        # 4. Connect Google Ads
        ads_cred = await service.connect_provider(
            organization_id=org.id,
            provider="google_ads",
            name="Google Ads Production",
            credentials={"developer_token": "token_abc"},
            settings={"customer_id": "999-888-7777"},
        )
        assert ads_cred.id is not None

        # Test Connection via Service
        test_res = await service.test_connection(org.id, crm_cred.id)
        assert test_res["success"] is True

        # Sync CRM -> verify leads created in Lead table
        sync_crm_res = await service.sync_provider(org.id, crm_cred.id)
        assert sync_crm_res["success"] is True
        assert sync_crm_res["records_processed"] == 2

        leads_q = select(Lead).where(Lead.organization_id == org.id)
        leads = (await db.execute(leads_q)).scalars().all()
        assert len(leads) >= 2
        elena = next(l for l in leads if l.email == "elena.rostova@enterprisecorp.com")
        assert elena.company == "Enterprise Corp"

        # Sync GA4 -> verify AnalyticsEvent recorded
        sync_ga_res = await service.sync_provider(org.id, ga_cred.id)
        assert sync_ga_res["success"] is True
        evt_q = select(AnalyticsEvent).where(AnalyticsEvent.organization_id == org.id)
        events = (await db.execute(evt_q)).scalars().all()
        assert len(events) >= 1
        assert events[0].event_name == "ga4_sync_metric"

        # Sync Ads -> verify Campaign and CampaignMetric records created
        sync_ads_res = await service.sync_provider(org.id, ads_cred.id)
        assert sync_ads_res["success"] is True
        camp_q = select(Campaign).where(Campaign.organization_id == org.id)
        camps = (await db.execute(camp_q)).scalars().all()
        assert len(camps) >= 2
        metric_q = select(CampaignMetric)
        metrics = (await db.execute(metric_q)).scalars().all()
        assert len(metrics) >= 2

        # Push Lead to CRM
        push_res = await service.push_lead_to_crm(org.id, elena.id)
        assert push_res["success"] is True
        assert push_res["provider"] == "mock_crm"

        # Dispatch Slack Notification
        slack_res = await service.dispatch_slack_alert(
            org.id,
            title="Revenue Milestone",
            message="$100k ARR achieved this sprint",
            severity="INFO",
        )
        assert slack_res["success"] is True

        # Ingest Webhook: Form Lead Submission
        wb_res = await service.process_incoming_webhook(
            organization_id=org.id,
            provider="website",
            event_type="lead_captured",
            payload={
                "first_name": "Alexander",
                "last_name": "Pierce",
                "email": "apierce@worldcorp.com",
                "company": "WorldCorp",
                "job_title": "CTO",
            },
        )
        assert wb_res["success"] is True
        alex_lead = (
            await db.execute(select(Lead).where(Lead.email == "apierce@worldcorp.com"))
        ).scalars().first()
        assert alex_lead is not None
        assert alex_lead.source == "WEBHOOK_WEBSITE"

        # Ingest Webhook: Visitor Tracking
        track_wb = await service.process_incoming_webhook(
            organization_id=org.id,
            provider="website",
            event_type="pageview",
            payload={"visitor_id": "vis_9918", "path": "/pricing", "utm_source": "google"},
        )
        assert track_wb["success"] is True

        # Verify Sync Logs
        logs = await service.list_sync_logs(org.id, crm_cred.id)
        assert len(logs) >= 1
        assert logs[0].status == "SUCCESS"


# =====================================================================
# 3. HTTP API Endpoints Tests
# =====================================================================

@pytest.mark.asyncio
async def test_integrations_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers, org_id = await _onboard_org(ac, suffix="api_endpoints")

        # 1. List Integrations (initially empty)
        res = await ac.get("/api/v1/integrations", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "integrations" in data
        assert "available_providers" in data
        assert len(data["available_providers"]) > 0

        # 2. Connect HubSpot Integration
        connect_res = await ac.post(
            "/api/v1/integrations/connect",
            headers=headers,
            json={
                "provider": "hubspot",
                "name": "Corporate HubSpot CRM",
                "credentials": {"access_token": "mock_hs_token"},
                "settings": {"sync_frequency": "daily"},
            },
        )
        assert connect_res.status_code == 201
        integration_id = connect_res.json()["integration_id"]

        # 3. Connect Slack Integration
        slack_connect = await ac.post(
            "/api/v1/integrations/connect",
            headers=headers,
            json={
                "provider": "slack",
                "name": "Team Slack",
                "credentials": {"webhook_url": "mock://slack.hook"},
                "settings": {"default_channel": "#alerts"},
            },
        )
        assert slack_connect.status_code == 201

        # 4. Get Integration Details
        get_res = await ac.get(f"/api/v1/integrations/{integration_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["provider"] == "hubspot"

        # 5. Test Connection
        test_res = await ac.post(f"/api/v1/integrations/{integration_id}/test", headers=headers)
        assert test_res.status_code == 200
        assert test_res.json()["success"] is True

        # 6. Trigger Sync
        sync_res = await ac.post(f"/api/v1/integrations/{integration_id}/sync", headers=headers)
        assert sync_res.status_code == 200
        assert sync_res.json()["success"] is True

        # 7. Get Sync Logs
        logs_res = await ac.get(f"/api/v1/integrations/{integration_id}/logs", headers=headers)
        assert logs_res.status_code == 200
        assert len(logs_res.json()["logs"]) >= 1

        # 8. Send Slack Alert via API
        slack_alert_res = await ac.post(
            "/api/v1/integrations/slack/notify",
            headers=headers,
            json={
                "title": "Campaign Goal Exceeded",
                "message": "CTR rose to 4.2% on LinkedIn ad group",
                "severity": "INFO",
            },
        )
        assert slack_alert_res.status_code == 200
        assert slack_alert_res.json()["success"] is True

        # 9. Get Website Tracking Snippet
        snippet_res = await ac.get("/api/v1/integrations/website/tracking-snippet", headers=headers)
        assert snippet_res.status_code == 200
        assert f"orgId: '{org_id}'" in snippet_res.json()["snippet"]

        # 10. Public Webhook Ingestion
        webhook_res = await ac.post(
            "/api/v1/integrations/webhook/website",
            json={
                "organization_id": org_id,
                "event_type": "form_submission",
                "payload": {
                    "first_name": "Lila",
                    "email": "lila.torres@acmeweb.org",
                    "company": "Acme Web",
                },
            },
        )
        assert webhook_res.status_code == 200
        assert webhook_res.json()["success"] is True

        # 11. Disconnect Integration
        delete_res = await ac.delete(f"/api/v1/integrations/{integration_id}", headers=headers)
        assert delete_res.status_code == 200
        assert delete_res.json()["success"] is True


# =====================================================================
# 4. MCP Tools Integration & Human Approval Gating Tests
# =====================================================================

@pytest.mark.asyncio
async def test_mcp_integration_tools():
    async with async_session_maker() as db:
        org = Organization(name="MCP Tool Org", slug="mcp-tool-org")
        db.add(org)
        await db.commit()
        await db.refresh(org)

        # 1. Test get_crm_leads (Low Risk, No Approval)
        res_leads = await tool_registry.execute(
            name="get_crm_leads",
            params={"limit": 5},
            organization_id=str(org.id),
            db=db,
        )
        assert res_leads.success is True
        assert "leads" in res_leads.result

        # 2. Test get_ga4_traffic (Low Risk, No Approval)
        res_ga4 = await tool_registry.execute(
            name="get_ga4_traffic",
            params={"period": "7d"},
            organization_id=str(org.id),
            db=db,
        )
        assert res_ga4.success is True
        assert res_ga4.result["active_users"] > 0

        # 3. Test post_slack_alert (Low Risk, No Approval)
        res_slack = await tool_registry.execute(
            name="post_slack_alert",
            params={"title": "Alert", "message": "Deploy Complete"},
            organization_id=str(org.id),
            db=db,
        )
        assert res_slack.success is True
        assert res_slack.result["status"] == "SENT"

        # 4. Test update_crm_lead (HIGH Risk, Requires Human Approval!)
        res_update_crm = await tool_registry.execute(
            name="update_crm_lead",
            params={"lead_id": "crm_101", "fields": {"stage": "Closed Won"}},
            organization_id=str(org.id),
            db=db,
            bypass_approval=False,
        )
        assert res_update_crm.success is False
        assert res_update_crm.requires_approval is True
        assert res_update_crm.approval_request_id is not None


# =====================================================================
# 5. Multi-Tenant Isolation Tests
# =====================================================================

@pytest.mark.asyncio
async def test_multi_tenant_integration_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers_a, org_a_id = await _onboard_org(ac, suffix="tenant_a")
        headers_b, org_b_id = await _onboard_org(ac, suffix="tenant_b")

        # Org A connects an integration
        connect_res = await ac.post(
            "/api/v1/integrations/connect",
            headers=headers_a,
            json={
                "provider": "hubspot",
                "name": "Alpha HubSpot",
                "credentials": {"access_token": "secret_alpha_token"},
            },
        )
        assert connect_res.status_code == 201
        cred_a_id = connect_res.json()["integration_id"]

        # User B attempts to access Org A's integration
        res_get = await ac.get(f"/api/v1/integrations/{cred_a_id}", headers=headers_b)
        assert res_get.status_code == 404

        # User B attempts to trigger sync on Org A's integration
        res_sync = await ac.post(f"/api/v1/integrations/{cred_a_id}/sync", headers=headers_b)
        assert res_sync.status_code in [200, 404]
        if res_sync.status_code == 200:
            assert res_sync.json()["success"] is False

        # User B attempts to delete Org A's integration
        res_del = await ac.delete(f"/api/v1/integrations/{cred_a_id}", headers=headers_b)
        assert res_del.status_code == 404
