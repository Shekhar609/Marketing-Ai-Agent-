"""
Organization Repository
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self):
        super().__init__(Organization)

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.slug == slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


organization_repo = OrganizationRepository()
