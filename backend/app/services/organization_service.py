"""
Organization Management Service
"""

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization
from app.repositories.organization_repo import organization_repo
from app.schemas.organization import OrganizationResponse, OrganizationUpdate


class OrganizationService:
    async def get_by_id(self, db: AsyncSession, org_id: str) -> OrganizationResponse:
        org = await organization_repo.get(db, org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        return OrganizationResponse.model_validate(org)

    async def update(
        self, db: AsyncSession, org_id: str, data: OrganizationUpdate
    ) -> OrganizationResponse:
        org = await organization_repo.get(db, org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        updated = await organization_repo.update(db, org, data.model_dump(exclude_unset=True))
        return OrganizationResponse.model_validate(updated)


organization_service = OrganizationService()
