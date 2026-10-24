"""
Integrations & External Connectors Service Layer
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.integrations import get_connector
from app.models.analytics import AnalyticsEvent
from app.models.campaign import Campaign, CampaignChannel, CampaignMetric
from app.models.integration import (
    IntegrationCredential,
    IntegrationProvider,
    IntegrationStatus,
    IntegrationSyncLog,
    WebhookEvent,
)
from app.models.lead import Lead, LeadEvent, LeadScore

logger = logging.getLogger(__name__)


class IntegrationsService:
    """
    Orchestration service for managing external credentials, executing sync pipelines,
    dispatching notifications, and ingesting incoming webhooks.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def connect_provider(
        self,
        organization_id: int,
        provider: str,
        name: str,
        credentials: Dict[str, Any],
        settings_payload: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> IntegrationCredential:
        """
        Store or update credentials and register an integration for the tenant.
        """
        effective_settings = settings_payload or settings or {}
        provider_key = provider.lower()
        query = select(IntegrationCredential).where(
            IntegrationCredential.organization_id == organization_id,
            IntegrationCredential.provider == provider_key,
        )
        result = await self.db.execute(query)
        cred = result.scalars().first()

        if cred:
            cred.name = name
            cred.credentials = credentials
            cred.settings = effective_settings
            cred.status = IntegrationStatus.CONNECTED
            cred.is_active = True
            cred.error_message = None
        else:
            cred = IntegrationCredential(
                organization_id=organization_id,
                provider=provider_key,
                name=name,
                credentials=credentials,
                settings=effective_settings,
                status=IntegrationStatus.CONNECTED,
                is_active=True,
            )
            self.db.add(cred)

        await self.db.commit()
        await self.db.refresh(cred)
        return cred

    async def ensure_default_integrations(self, organization_id: int) -> None:
        """
        Ensure default integration configurations (Salesforce, Slack, Calendar)
        are ready for the tenant with either real environment variables or sandbox presets.
        """
        query = select(IntegrationCredential).where(
            IntegrationCredential.organization_id == organization_id
        )
        res = await self.db.execute(query)
        existing = list(res.scalars().all())
        existing_providers = {c.provider.lower() for c in existing}

        # 1. Salesforce CRM
        if IntegrationProvider.SALESFORCE.value not in existing_providers:
            sf_creds = {}
            if settings.SALESFORCE_INSTANCE_URL and settings.SALESFORCE_ACCESS_TOKEN:
                sf_creds = {
                    "instance_url": settings.SALESFORCE_INSTANCE_URL,
                    "access_token": settings.SALESFORCE_ACCESS_TOKEN,
                }
            elif settings.SALESFORCE_USERNAME and settings.SALESFORCE_PASSWORD:
                sf_creds = {
                    "instance_url": settings.SALESFORCE_INSTANCE_URL,
                    "client_id": settings.SALESFORCE_CLIENT_ID,
                    "client_secret": settings.SALESFORCE_CLIENT_SECRET,
                    "username": settings.SALESFORCE_USERNAME,
                    "password": settings.SALESFORCE_PASSWORD,
                    "security_token": settings.SALESFORCE_SECURITY_TOKEN,
                }
            else:
                sf_creds = {
                    "instance_url": "https://aipnt-demo.my.salesforce.com",
                    "access_token": "mock_sf_token_live_preview",
                }
            await self.connect_provider(
                organization_id=organization_id,
                provider=IntegrationProvider.SALESFORCE.value,
                name="Salesforce Enterprise CRM",
                credentials=sf_creds,
                settings_payload={"sync_frequency_minutes": 15, "auto_enrich_leads": True},
            )

        # 2. Slack Workspace
        if IntegrationProvider.SLACK.value not in existing_providers:
            slack_creds = {}
            if settings.SLACK_WEBHOOK_URL:
                slack_creds["webhook_url"] = settings.SLACK_WEBHOOK_URL
            elif settings.SLACK_BOT_TOKEN:
                slack_creds["bot_token"] = settings.SLACK_BOT_TOKEN
            else:
                slack_creds = {"webhook_url": "mock_slack_webhook_alerts"}
            await self.connect_provider(
                organization_id=organization_id,
                provider=IntegrationProvider.SLACK.value,
                name="Slack Growth Alerts",
                credentials=slack_creds,
                settings_payload={"default_channel": settings.SLACK_DEFAULT_CHANNEL or "#growth-alerts"},
            )

        # 3. Calendar (Calendly / Google Calendar)
        if IntegrationProvider.CALENDAR.value not in existing_providers:
            cal_creds = {}
            cal_type = "calendly"
            if settings.CALENDLY_API_KEY:
                cal_creds = {"api_key": settings.CALENDLY_API_KEY}
                cal_type = "calendly"
            elif settings.GOOGLE_CALENDAR_TOKEN:
                cal_creds = {"access_token": settings.GOOGLE_CALENDAR_TOKEN}
                cal_type = "google_calendar"
            else:
                cal_creds = {"api_key": "mock_calendly_personal_token"}
            await self.connect_provider(
                organization_id=organization_id,
                provider=IntegrationProvider.CALENDAR.value,
                name="Calendly Demo Scheduler",
                credentials=cal_creds,
                settings_payload={"type": cal_type, "sync_frequency_minutes": 30},
            )

    async def get_credential(self, organization_id: int, credential_id: int) -> Optional[IntegrationCredential]:
        query = select(IntegrationCredential).where(
            IntegrationCredential.organization_id == organization_id,
            IntegrationCredential.id == credential_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_credentials(self, organization_id: int) -> List[IntegrationCredential]:
        # Ensure default/environment-configured integrations are initialized
        try:
            await self.ensure_default_integrations(organization_id)
        except Exception as e:
            logger.warning(f"Could not initialize default integrations: {e}")

        query = (
            select(IntegrationCredential)
            .where(IntegrationCredential.organization_id == organization_id)
            .order_by(IntegrationCredential.id.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_credential(self, organization_id: int, credential_id: int) -> bool:
        cred = await self.get_credential(organization_id, credential_id)
        if not cred:
            return False
        await self.db.delete(cred)
        await self.db.commit()
        return True

    async def test_connection(self, organization_id: int, credential_id: int) -> Dict[str, Any]:
        """
        Test live connectivity for a credential.
        """
        cred = await self.get_credential(organization_id, credential_id)
        if not cred:
            return {"success": False, "message": "Integration credential not found"}

        try:
            connector = get_connector(
                provider=cred.provider,
                credentials=cred.credentials,
                settings=cred.settings,
            )
            result = await connector.test_connection()
            if result.get("success"):
                cred.status = IntegrationStatus.CONNECTED
                cred.error_message = None
            else:
                cred.status = IntegrationStatus.ERROR
                cred.error_message = result.get("message")
            await self.db.commit()
            return result
        except Exception as exc:
            cred.status = IntegrationStatus.ERROR
            cred.error_message = str(exc)
            await self.db.commit()
            return {"success": False, "message": str(exc)}

    async def sync_provider(self, organization_id: int, credential_id: int) -> Dict[str, Any]:
        """
        Run synchronization pipeline and persist mapped records into CRM / Analytics models.
        """
        cred = await self.get_credential(organization_id, credential_id)
        if not cred:
            return {"success": False, "message": "Credential not found"}

        cred.status = IntegrationStatus.SYNCING
        await self.db.commit()

        try:
            connector = get_connector(
                provider=cred.provider,
                credentials=cred.credentials,
                settings=cred.settings,
            )
            sync_result = await connector.sync()

            records_processed = sync_result.get("records_processed", 0)
            records_failed = sync_result.get("records_failed", 0)

            # Route data to appropriate system tables based on provider
            provider_type = cred.provider.lower()

            # 1. CRM sync: persist inbound leads
            if provider_type in [IntegrationProvider.HUBSPOT.value, IntegrationProvider.SALESFORCE.value, IntegrationProvider.MOCK_CRM.value]:
                leads_data = sync_result.get("leads", [])
                for item in leads_data:
                    email = item.get("email")
                    if not email:
                        continue
                    # Check existing lead
                    lead_q = select(Lead).where(
                        Lead.organization_id == organization_id,
                        Lead.email == email,
                    )
                    lead_res = await self.db.execute(lead_q)
                    existing_lead = lead_res.scalars().first()

                    if not existing_lead:
                        new_lead = Lead(
                            organization_id=organization_id,
                            first_name=item.get("first_name", ""),
                            last_name=item.get("last_name", ""),
                            email=email,
                            company=item.get("company", ""),
                            job_title=item.get("job_title", ""),
                            classification="Warm",
                            source=f"CRM_{cred.provider.upper()}",
                        )
                        self.db.add(new_lead)
                        await self.db.flush()
                        # Add initial score
                        score = LeadScore(
                            lead_id=new_lead.id,
                            total_score=item.get("score", 70.0),
                            company_fit=25.0,
                            role_fit=25.0,
                            engagement=10.0,
                            intent=10.0,
                            classification="Warm",
                            reasoning="Imported via CRM sync",
                        )
                        self.db.add(score)

            # 2. Google Analytics sync: record analytics events summary
            elif provider_type == IntegrationProvider.GOOGLE_ANALYTICS.value:
                ga_data = sync_result.get("data", {})
                evt = AnalyticsEvent(
                    organization_id=organization_id,
                    event_name="ga4_sync_metric",
                    funnel_stage="visitor",
                    channel="Organic",
                    source="google_analytics",
                    properties=ga_data,
                )
                self.db.add(evt)

            # 3. Ads sync: create/update campaign metrics
            elif provider_type in [IntegrationProvider.GOOGLE_ADS.value, IntegrationProvider.LINKEDIN.value, IntegrationProvider.META.value]:
                campaigns = sync_result.get("campaigns", [])
                for camp in campaigns:
                    # Look up or create campaign record
                    c_name = camp.get("name", f"{cred.provider} Campaign")
                    camp_q = select(Campaign).where(
                        Campaign.organization_id == organization_id,
                        Campaign.campaign_name == c_name,
                    )
                    c_res = await self.db.execute(camp_q)
                    campaign_obj = c_res.scalars().first()
                    if not campaign_obj:
                        campaign_obj = Campaign(
                            organization_id=organization_id,
                            campaign_name=c_name,
                            objective="Lead Generation",
                            audience="B2B Growth Executives",
                            message="Autonomous Revenue Operations Platform",
                            channels=[cred.provider],
                            status="active",
                            budget=camp.get("spend", 1000.0),
                        )
                        self.db.add(campaign_obj)
                        await self.db.flush()
                    
                    # Add metric
                    metric = CampaignMetric(
                        campaign_id=campaign_obj.id,
                        impressions=camp.get("impressions", 0),
                        clicks=camp.get("clicks", 0),
                        leads_generated=camp.get("leads", 0),
                        conversions=camp.get("conversions", camp.get("leads", 0)),
                        cost=camp.get("spend", 0.0),
                        revenue_attributed=camp.get("spend", 0.0) * 2.5,
                    )
                    self.db.add(metric)

            # 4. Calendar sync: persist booked demo meetings & pipeline attribution
            elif provider_type == IntegrationProvider.CALENDAR.value:
                events = sync_result.get("events", [])
                for ev in events:
                    p_email = ev.get("prospect_email")
                    if not p_email:
                        continue
                    lead_q = select(Lead).where(
                        Lead.organization_id == organization_id,
                        Lead.email == p_email,
                    )
                    lead_res = await self.db.execute(lead_q)
                    lead_obj = lead_res.scalars().first()
                    p_name = ev.get("prospect_name", "Prospect")
                    parts = p_name.split(" ")
                    f_name = parts[0] if parts else "Prospect"
                    l_name = " ".join(parts[1:]) if len(parts) > 1 else "Lead"

                    if not lead_obj:
                        lead_obj = Lead(
                            organization_id=organization_id,
                            first_name=f_name,
                            last_name=l_name,
                            email=p_email,
                            company="Meeting Attendee",
                            job_title="Executive",
                            classification="Hot",
                            source=f"CALENDAR_{ev.get('utm_source', 'BOOKING').upper()}",
                        )
                        self.db.add(lead_obj)
                        await self.db.flush()
                        score = LeadScore(
                            lead_id=lead_obj.id,
                            total_score=94.0,
                            company_fit=30.0,
                            role_fit=30.0,
                            engagement=20.0,
                            intent=14.0,
                            classification="Hot",
                            reasoning=f"High-intent meeting booked: {ev.get('event_type')}",
                        )
                        self.db.add(score)

                    # Track Attribution Event
                    evt = AnalyticsEvent(
                        organization_id=organization_id,
                        event_name="demo_scheduled",
                        funnel_stage="demo_booked",
                        channel="Direct Scheduling",
                        source="calendar",
                        properties=ev,
                    )
                    self.db.add(evt)

            # Log sync run
            log = IntegrationSyncLog(
                organization_id=organization_id,
                credential_id=cred.id,
                provider=cred.provider,
                sync_type=f"{cred.provider.upper()}_SYNC",
                status="SUCCESS",
                records_processed=records_processed,
                records_failed=records_failed,
                details=sync_result,
            )
            self.db.add(log)

            cred.status = IntegrationStatus.CONNECTED
            cred.last_sync_at = datetime.now(timezone.utc)
            cred.last_sync_status = "SUCCESS"
            cred.error_message = None

            await self.db.commit()

            return {
                "success": True,
                "provider": cred.provider,
                "records_processed": records_processed,
                "records_failed": records_failed,
                "sync_id": log.id,
                "details": sync_result,
            }

        except Exception as exc:
            logger.error(f"Sync failed for credential {credential_id}: {exc}")
            log = IntegrationSyncLog(
                organization_id=organization_id,
                credential_id=cred.id,
                provider=cred.provider,
                sync_type=f"{cred.provider.upper()}_SYNC",
                status="FAILED",
                records_processed=0,
                records_failed=1,
                details={"error": str(exc)},
            )
            self.db.add(log)
            cred.status = IntegrationStatus.ERROR
            cred.last_sync_status = "FAILED"
            cred.error_message = str(exc)
            await self.db.commit()
            return {"success": False, "error": str(exc)}

    async def list_sync_logs(
        self, organization_id: int, credential_id: Optional[int] = None, limit: int = 20
    ) -> List[IntegrationSyncLog]:
        query = select(IntegrationSyncLog).where(IntegrationSyncLog.organization_id == organization_id)
        if credential_id:
            query = query.where(IntegrationSyncLog.credential_id == credential_id)
        query = query.order_by(IntegrationSyncLog.id.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def push_lead_to_crm(self, organization_id: int, lead_id: int) -> Dict[str, Any]:
        """
        Push an internal Lead record to the organization's connected CRM.
        """
        lead_q = select(Lead).where(Lead.organization_id == organization_id, Lead.id == lead_id)
        res = await self.db.execute(lead_q)
        lead = res.scalars().first()
        if not lead:
            return {"success": False, "message": "Lead not found"}

        # Find active CRM credential
        crm_q = select(IntegrationCredential).where(
            IntegrationCredential.organization_id == organization_id,
            IntegrationCredential.is_active == True,
            IntegrationCredential.provider.in_([
                IntegrationProvider.HUBSPOT.value,
                IntegrationProvider.SALESFORCE.value,
                IntegrationProvider.MOCK_CRM.value,
            ]),
        )
        crm_res = await self.db.execute(crm_q)
        cred = crm_res.scalars().first()
        if not cred:
            return {"success": False, "message": "No active CRM integration configured for organization"}

        connector = get_connector(cred.provider, cred.credentials, cred.settings)
        lead_dict = {
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "email": lead.email,
            "company": lead.company,
            "job_title": lead.job_title,
            "status": lead.classification,
        }
        push_res = await getattr(connector, "push_lead")(lead_dict)
        return {"success": True, "provider": cred.provider, "crm_result": push_res}

    async def dispatch_slack_alert(
        self,
        organization_id: int,
        title: str,
        message: str,
        severity: str = "INFO",
        action_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dispatch an alert message to the tenant's configured Slack channel.
        """
        q = select(IntegrationCredential).where(
            IntegrationCredential.organization_id == organization_id,
            IntegrationCredential.provider == IntegrationProvider.SLACK.value,
            IntegrationCredential.is_active == True,
        )
        res = await self.db.execute(q)
        cred = res.scalars().first()
        if not cred:
            return {"success": False, "message": "Slack integration not configured for this organization"}

        connector = get_connector(cred.provider, cred.credentials, cred.settings)
        return await getattr(connector, "send_alert")(
            title=title, message=message, severity=severity, action_url=action_url
        )

    async def process_incoming_webhook(
        self,
        organization_id: int,
        provider: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ingest and process an incoming webhook (e.g. website lead submission, CRM trigger).
        """
        wb_event = WebhookEvent(
            organization_id=organization_id,
            provider=provider.lower(),
            event_type=event_type,
            payload=payload,
            processed=False,
        )
        self.db.add(wb_event)
        await self.db.flush()

        try:
            # If lead capture event
            if event_type in ["lead_captured", "form_submission", "contact_created"]:
                lead_data = payload.get("lead", payload)
                email = lead_data.get("email")
                if email:
                    new_lead = Lead(
                        organization_id=organization_id,
                        first_name=lead_data.get("first_name", lead_data.get("name", "Prospect")),
                        last_name=lead_data.get("last_name", ""),
                        email=email,
                        company=lead_data.get("company", ""),
                        job_title=lead_data.get("job_title", ""),
                        source=f"WEBHOOK_{provider.upper()}",
                        classification="Cold",
                    )
                    self.db.add(new_lead)
                    await self.db.flush()

                    # Add lead event
                    event = LeadEvent(
                        lead_id=new_lead.id,
                        event_type="FORM_SUBMISSION",
                        event_data=payload,
                        weight=5.0,
                    )
                    self.db.add(event)

            # If tracking event (pageview, click)
            elif event_type in ["pageview", "click", "custom_event"]:
                track_evt = AnalyticsEvent(
                    organization_id=organization_id,
                    event_name=payload.get("event_name", event_type),
                    funnel_stage="visitor",
                    channel=payload.get("channel", "Direct"),
                    source=provider,
                    properties=payload,
                )
                self.db.add(track_evt)

            wb_event.processed = True
            wb_event.processed_at = datetime.now(timezone.utc)
            await self.db.commit()
            return {"success": True, "event_id": wb_event.id, "processed": True}

        except Exception as exc:
            wb_event.error_message = str(exc)
            await self.db.commit()
            return {"success": False, "event_id": wb_event.id, "error": str(exc)}
