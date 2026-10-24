"""
Growth Agents API Router — Standalone Invocations for Growth & Revenue Agents
Corresponds to Master Specification Section 36.

Provides standalone endpoints for each growth agent:
- POST /api/v1/seo/analyze         — SEO Agent (Section 10)
- POST /api/v1/social/generate     — Social Media Agent (Section 11)
- POST /api/v1/email/generate      — Email Marketing Agent (Section 12)
- POST /api/v1/campaigns/create    — Campaign Management Agent (Section 13)
- POST /api/v1/leads/score         — Lead Generation Agent (Section 14)
- POST /api/v1/sales/enablement    — Sales Enablement Agent (Section 15)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_current_user, get_db
from app.models.organization import Organization
from app.models.user import User

from app.agents.seo_agent import SEORequest, seo_agent
from app.agents.social_media import SocialMediaRequest, social_media_agent
from app.agents.email_marketing import EmailCampaignRequest, email_marketing_agent
from app.agents.campaign_management import CampaignCreateRequest, campaign_management_agent
from app.agents.lead_generation import LeadScoringRequest, lead_generation_agent
from app.agents.sales_enablement import SalesEnablementRequest, sales_enablement_agent

router = APIRouter()


# --------------------------------------------------------------------------
# SEO Agent Endpoint
# --------------------------------------------------------------------------

@router.post("/seo/analyze")
async def run_seo_analysis(
    request: SEORequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the SEO Agent to perform keyword research, 5-factor scoring,
    competitor content gap analysis, and topic cluster roadmaps.
    """
    try:
        result = await seo_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SEO Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Social Media Agent Endpoint
# --------------------------------------------------------------------------

@router.post("/social/generate")
async def run_social_media_generation(
    request: SocialMediaRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Social Media Agent to generate multi-platform posts,
    carousels, video scripts, viral hooks, and weekly content calendars.
    """
    try:
        result = await social_media_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Social Media Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Email Marketing Agent Endpoint
# --------------------------------------------------------------------------

@router.post("/email/generate")
async def run_email_generation(
    request: EmailCampaignRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Email Marketing Agent to generate personalized lifecycle
    sequences, subject lines, preview texts, and cadence strategies.
    """
    try:
        result = await email_marketing_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email Marketing Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Campaign Management Agent Endpoint
# --------------------------------------------------------------------------

@router.post("/campaigns/create")
async def run_campaign_creation(
    request: CampaignCreateRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Campaign Management Agent to design multi-channel campaigns,
    allocate budgets, determine CPL/CAC targets, and produce ad variants.
    """
    try:
        result = await campaign_management_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign Management Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Lead Generation Agent Endpoint
# --------------------------------------------------------------------------

@router.post("/leads/score")
async def run_lead_scoring(
    request: LeadScoringRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Lead Generation Agent to score leads using the 5-factor formula
    (Company Fit + Role Fit + Engagement + Intent + Behavior) and assign to 6 enterprise tiers.
    """
    try:
        result = await lead_generation_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lead Generation Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Sales Enablement Agent Endpoint
# --------------------------------------------------------------------------

@router.post("/sales/enablement")
async def run_sales_enablement(
    request: SalesEnablementRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Sales Enablement Agent to generate account dossiers,
    battlecards, objection handling scripts, and call preparation briefs.
    """
    try:
        result = await sales_enablement_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sales Enablement Agent failed: {str(e)}",
        )
