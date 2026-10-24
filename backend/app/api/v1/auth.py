"""
Authentication & Onboarding Router
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, OnboardRegisterRequest, Token
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service
from app.schemas.organization import OrganizationResponse

router = APIRouter()


@router.post("/onboard", response_model=Token, status_code=status.HTTP_201_CREATED)
async def onboard_organization(
    data: OnboardRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Onboard a new organization tenant and bootstrap admin credentials.
    Seeds default product/service catalogs and returns authentication token.
    """
    token_response = await auth_service.onboard(db, data)
    return token_response


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user with email and password, issuing a JWT access token."""
    user, org, token_str = await auth_service.authenticate(db, data)
    return Token(
        access_token=token_str,
        token_type="bearer",
        expires_in_minutes=1440,
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(org)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Retrieve profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
