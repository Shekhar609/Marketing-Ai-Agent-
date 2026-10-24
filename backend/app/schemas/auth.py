"""
Authentication and Session Token Schemas
"""

from typing import Optional
from pydantic import BaseModel, EmailStr
from app.schemas.organization import OrganizationResponse
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OnboardRegisterRequest(BaseModel):
    """Combined registration and organization onboarding schema."""
    organization_name: str
    organization_slug: str
    industry: str = "B2B SaaS / DeepTech AI"
    admin_email: EmailStr
    admin_password: str
    admin_name: str
    monthly_budget: float = 500000.0
    monthly_leads_target: int = 500
    revenue_target: float = 10000000.0


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse
    organization: Optional[OrganizationResponse] = None
