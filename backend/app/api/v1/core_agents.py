"""
Core Agents API Router — Individual Agent Invocations
Corresponds to Master Specification Section 36.

Provides standalone endpoints for each core agent:
- POST /api/v1/research/market       — Market Research Agent
- POST /api/v1/research/competitors  — Competitive Intelligence Agent
- POST /api/v1/personas/generate     — Customer Persona Agent
- POST /api/v1/brand/strategy        — Brand Strategy Agent
- POST /api/v1/content/generate      — Content Strategy Agent
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_current_user, get_db
from app.models.organization import Organization
from app.models.user import User

from app.agents.market_research import MarketResearchRequest, market_research_agent
from app.agents.competitive_intel import CompetitiveIntelRequest, competitive_intel_agent
from app.agents.customer_persona import PersonaRequest, customer_persona_agent
from app.agents.brand_strategy import BrandStrategyRequest, brand_strategy_agent
from app.agents.content_strategy import ContentRequest, content_strategy_agent

router = APIRouter()


# --------------------------------------------------------------------------
# Market Research Agent
# --------------------------------------------------------------------------

@router.post("/research/market")
async def run_market_research(
    request: MarketResearchRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Market Research Agent to analyze markets, trends,
    and opportunities for the given business objective.
    """
    try:
        result = await market_research_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Market Research Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Competitive Intelligence Agent
# --------------------------------------------------------------------------

@router.post("/research/competitors")
async def run_competitive_analysis(
    request: CompetitiveIntelRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Competitive Intelligence Agent to analyze competitors,
    generate SWOT matrices, and identify strategic gaps.
    """
    try:
        result = await competitive_intel_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Competitive Intelligence Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Customer Persona Agent
# --------------------------------------------------------------------------

@router.post("/personas/generate")
async def run_persona_generation(
    request: PersonaRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Customer Persona Agent to build ICPs,
    buyer personas, and customer journey maps.
    """
    try:
        result = await customer_persona_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Customer Persona Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Brand Strategy Agent
# --------------------------------------------------------------------------

@router.post("/brand/strategy")
async def run_brand_strategy(
    request: BrandStrategyRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Brand Strategy Agent to create positioning,
    value propositions, and messaging frameworks.
    """
    try:
        result = await brand_strategy_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Brand Strategy Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Content Strategy Agent
# --------------------------------------------------------------------------

@router.post("/content/generate")
async def run_content_generation(
    request: ContentRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Content Strategy Agent to generate marketing content
    with full asset metadata, brand alignment, and content planning.
    """
    try:
        result = await content_strategy_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content Strategy Agent failed: {str(e)}",
        )
