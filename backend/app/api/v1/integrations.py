"""
Integrations & External Connectors API Router
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.integrations.website import WebsiteConnector
from app.models.integration import IntegrationProvider
from app.models.user import User
from app.services.integrations_service import IntegrationsService

router = APIRouter(prefix="/integrations", tags=["Integrations & Connectors"])


# --- Schemas ---

class ConnectIntegrationRequest(BaseModel):
    provider: str = Field(..., description="Provider name (hubspot, salesforce, google_analytics, etc.)")
    name: str = Field(..., description="Display name for this integration connection")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="API keys, tokens, or auth secrets")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters & preferences")


class SlackNotifyRequest(BaseModel):
    title: str
    message: str
    severity: str = "INFO"
    action_url: Optional[str] = None


class PushLeadRequest(BaseModel):
    lead_id: str


class WebhookIngestRequest(BaseModel):
    organization_id: str
    event_type: str
    payload: Dict[str, Any]


# --- Endpoints ---

@router.get("", summary="List configured integrations and available providers")
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IntegrationsService(db)
    active_integrations = await service.list_credentials(current_user.organization_id)
    
    # Supported providers metadata
    available_providers = [
        {"id": p.value, "name": p.name.replace("_", " ").title(), "type": "CRM" if "CRM" in p.name or p.value in ["hubspot", "salesforce"] else "MARKETING"}
        for p in IntegrationProvider
    ]

    return {
        "integrations": [
            {
                "id": item.id,
                "provider": item.provider,
                "name": item.name,
                "status": item.status,
                "is_active": item.is_active,
                "last_sync_at": item.last_sync_at,
                "last_sync_status": item.last_sync_status,
                "error_message": item.error_message,
                "created_at": item.created_at,
            }
            for item in active_integrations
        ],
        "available_providers": available_providers,
    }


@router.post("/connect", status_code=status.HTTP_201_CREATED, summary="Connect a new integration provider")
async def connect_integration(
    payload: ConnectIntegrationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IntegrationsService(db)
    try:
        cred = await service.connect_provider(
            organization_id=current_user.organization_id,
            provider=payload.provider,
            name=payload.name,
            credentials=payload.credentials,
            settings=payload.settings,
        )
        return {
            "success": True,
            "message": f"Successfully connected {payload.provider}",
            "integration_id": cred.id,
            "status": cred.status,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{integration_id}", summary="Get integration details")
async def get_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IntegrationsService(db)
    cred = await service.get_credential(current_user.organization_id, integration_id)
    if not cred:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {
        "id": cred.id,
        "provider": cred.provider,
        "name": cred.name,
        "status": cred.status,
        "settings": cred.settings,
        "last_sync_at": cred.last_sync_at,
        "last_sync_status": cred.last_sync_status,
        "error_message": cred.error_message,
    }


@router.delete("/{integration_id}", summary="Disconnect and remove an integration")
async def delete_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IntegrationsService(db)
    success = await service.delete_credential(current_user.organization_id, integration_id)
    if not success:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"success": True, "message": "Integration disconnected successfully"}


@router.post("/{integration_id}/test", summary="Test integration connection health")
async def test_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IntegrationsService(db)
    result = await service.test_connection(current_user.organization_id, integration_id)
    return result


@router.post("/{integration_id}/sync", summary="Trigger synchronization pipeline for an integration")
async def sync_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IntegrationsService(db)
    result = await service.sync_provider(current_user.organization_id, integration_id)
    return result


@router.get("/{integration_id}/logs", summary="Get sync logs for an integration")
async def get_integration_logs(
    integration_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IntegrationsService(db)
    logs = await service.list_sync_logs(
        organization_id=current_user.organization_id,
        credential_id=integration_id,
        limit=limit,
    )
    return {"logs": logs}


@router.post("/crm/push-lead", summary="Push a lead to connected CRM")
async def push_lead_crm(
    payload: PushLeadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IntegrationsService(db)
    res = await service.push_lead_to_crm(current_user.organization_id, payload.lead_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@router.post("/slack/notify", summary="Dispatch real-time notification to connected Slack channel")
async def notify_slack(
    payload: SlackNotifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IntegrationsService(db)
    res = await service.dispatch_slack_alert(
        organization_id=current_user.organization_id,
        title=payload.title,
        message=payload.message,
        severity=payload.severity,
        action_url=payload.action_url,
    )
    return res


@router.get("/website/tracking-snippet", summary="Generate embeddable website tracking script tag")
async def get_tracking_snippet(
    current_user: User = Depends(get_current_user),
):
    snippet = WebsiteConnector.generate_tracking_snippet(
        organization_id=current_user.organization_id
    )
    return {
        "organization_id": current_user.organization_id,
        "snippet": snippet,
        "instructions": "Paste this tag into the <head> of every page on your website to enable autonomous visitor tracking and lead attribution."
    }


@router.post("/webhook/{provider}", summary="Public/Authenticated incoming webhook receiver")
async def receive_webhook(
    provider: str,
    payload: WebhookIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Public webhook receiver for website snippets, form submissions, and 3rd-party webhook events.
    """
    service = IntegrationsService(db)
    result = await service.process_incoming_webhook(
        organization_id=payload.organization_id,
        provider=provider,
        event_type=payload.event_type,
        payload=payload.payload,
    )
    return result
