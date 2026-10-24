"""
Organization Management & Configuration Router
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db, require_admin
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationResponse, OrganizationUpdate
from app.services.organization_service import organization_service

router = APIRouter()


@router.get("/me", response_model=OrganizationResponse)
async def get_current_organization(
    tenant: Organization = Depends(get_current_tenant)
):
    """Retrieve full configuration and targets for current tenant organization."""
    return OrganizationResponse.model_validate(tenant)


@router.patch("/me", response_model=OrganizationResponse)
async def update_organization_configuration(
    data: OrganizationUpdate,
    tenant: Organization = Depends(get_current_tenant),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update organizational marketing budget, goals, competitors, or brand guidelines."""
    updated = await organization_service.update(db, tenant.id, data)
    return updated
