"""
User Repository with Multi-Tenant Filtering
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_and_org(
        self, db: AsyncSession, email: str, organization_id: str
    ) -> Optional[User]:
        stmt = select(User).where(
            User.email == email,
            User.organization_id == organization_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self, db: AsyncSession, organization_id: str, skip: int = 0, limit: int = 100
    ) -> List[User]:
        stmt = select(User).where(User.organization_id == organization_id).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())


user_repo = UserRepository()
