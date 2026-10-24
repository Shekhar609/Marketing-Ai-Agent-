"""
Authentication and Onboarding Service
"""

from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.product import Product
from app.repositories.organization_repo import organization_repo
from app.repositories.user_repo import user_repo
from app.schemas.auth import LoginRequest, OnboardRegisterRequest, Token
from app.schemas.organization import OrganizationResponse
from app.schemas.user import UserResponse


class AuthService:
    async def authenticate(
        self, db: AsyncSession, login_data: LoginRequest
    ) -> Tuple[User, Organization, str]:
        user = await user_repo.get_by_email(db, login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is deactivated"
            )
            
        org = await organization_repo.get(db, user.organization_id)
        if not org or not org.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization tenant is inactive"
            )
            
        token = create_access_token(
            subject=user.id,
            organization_id=org.id,
            role=user.role.value
        )
        return user, org, token

    async def onboard(
        self, db: AsyncSession, data: OnboardRegisterRequest
    ) -> Token:
        # Check existing organization slug
        existing_org = await organization_repo.get_by_slug(db, data.organization_slug)
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An organization with this slug already exists"
            )

        # Check existing user email
        existing_user = await user_repo.get_by_email(db, data.admin_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists"
            )

        # 1. Create Organization
        org_data = {
            "name": data.organization_name,
            "slug": data.organization_slug.lower(),
            "industry": data.industry,
            "monthly_marketing_budget": data.monthly_budget,
            "monthly_lead_target": data.monthly_leads_target,
            "revenue_target": data.revenue_target,
            "products": [
                "Prarambh (AI Coding & STEM)",
                "DigiSwasth (AI Healthcare)",
                "ATAT (AI Teaching Assistant)",
                "Constituency Intelligence"
            ],
            "services": [
                "Corporate AI Training",
                "GovTech AI Digitization",
                "Enterprise Copilot Development"
            ],
            "target_markets": ["India", "Southeast Asia", "United States"],
            "competitors": ["HealthCube", "Clinics On Cloud", "Avishkaar", "STEMROBO", "Gnani.ai"],
            "existing_channels": ["LinkedIn", "Direct Sales", "Industry Expos", "Organic Search"]
        }
        org = await organization_repo.create(db, org_data)

        # 2. Create Admin User
        user_data = {
            "organization_id": org.id,
            "email": data.admin_email,
            "full_name": data.admin_name,
            "hashed_password": hash_password(data.admin_password),
            "role": UserRole.ADMIN,
            "is_active": True,
            "is_superuser": True
        }
        user = await user_repo.create(db, user_data)

        # 3. Seed Default AIPNT Products if AIPNT
        default_products = [
            {
                "organization_id": org.id,
                "name": "Prarambh",
                "slug": "prarambh",
                "domain": "EduTech",
                "description": "AI-Powered STEM Coding & Robotics Platform with Odia & English dual AI audio",
                "features": ["Block & Python coding", "Robotics hardware integration", "NEP 2020 aligned"],
                "pricing_model": "Annual School License",
            },
            {
                "organization_id": org.id,
                "name": "DigiSwasth",
                "slug": "digiswasth",
                "domain": "MedTech",
                "description": "AI-Powered Digital Healthcare Ecosystem & ABDM-compliant EHR",
                "features": ["10+ Vital diagnostics", "Smart triage kiosk", "ABDM EHR certified"],
                "pricing_model": "Per-Kiosk Hardware + SaaS Subscription",
            },
            {
                "organization_id": org.id,
                "name": "ATAT",
                "slug": "atat",
                "domain": "EduTech",
                "description": "AI Teaching Assistant & Interactive Classroom Co-Teacher",
                "features": ["Dual Student/Teacher modes", "Smart board instant sync", "AI PPT conversion"],
                "pricing_model": "Institutional Classroom License",
            },
            {
                "organization_id": org.id,
                "name": "Constituency Intelligence",
                "slug": "constituency-intelligence",
                "domain": "DigiTech",
                "description": "GovTech Grievance Redressal and Municipal Triage Suite",
                "features": ["Ward GIS geo-tagging", "Citizen sentiment NLP", "Field dispatch engine"],
                "pricing_model": "Government Tender / Annual Municipal Contract",
            }
        ]
        for prod_item in default_products:
            prod_obj = Product(**prod_item)
            db.add(prod_obj)
        await db.flush()

        # 4. Generate JWT Token
        token_str = create_access_token(
            subject=user.id,
            organization_id=org.id,
            role=user.role.value
        )

        return Token(
            access_token=token_str,
            token_type="bearer",
            expires_in_minutes=1440,
            user=UserResponse.model_validate(user),
            organization=OrganizationResponse.model_validate(org)
        )


auth_service = AuthService()
