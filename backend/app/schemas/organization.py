"""
Organization and Onboarding Pydantic Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    name: str = Field(..., examples=["AI PNT Technologies Private Limited"])
    slug: str = Field(..., examples=["aipnt"])
    industry: str = Field(default="B2B SaaS / DeepTech AI", examples=["B2B SaaS"])
    website_url: Optional[str] = Field(default="https://aipnt.in", examples=["https://aipnt.in"])
    geography: Optional[str] = Field(default="India", examples=["India"])
    customer_type: Optional[str] = Field(default="SMB and Mid-Market", examples=["SMB and Mid-Market"])
    sales_cycle: Optional[str] = Field(default="30-90 days", examples=["30-90 days"])
    
    # Financial Targets (from Section 3 Master Spec)
    monthly_marketing_budget: float = Field(default=500000.0, examples=[500000.0])
    monthly_lead_target: int = Field(default=500, examples=[500])
    revenue_target: float = Field(default=10000000.0, examples=[10000000.0])
    
    # Onboarding details
    products: List[str] = Field(
        default_factory=lambda: [
            "Prarambh (AI Coding & STEM)",
            "DigiSwasth (AI Healthcare)",
            "ATAT (AI Teaching Assistant)",
            "Constituency Intelligence"
        ]
    )
    services: List[str] = Field(
        default_factory=lambda: [
            "Corporate AI Training",
            "GovTech AI Digitization",
            "Enterprise Copilot Development"
        ]
    )
    target_markets: List[str] = Field(
        default_factory=lambda: ["India", "Southeast Asia", "United States"]
    )
    competitors: List[str] = Field(
        default_factory=lambda: ["HealthCube", "Clinics On Cloud", "Avishkaar", "STEMROBO", "Gnani.ai"]
    )
    existing_channels: List[str] = Field(
        default_factory=lambda: ["LinkedIn", "Direct Sales", "Industry Expos", "Organic Search"]
    )
    brand_guidelines: Dict[str, Any] = Field(
        default_factory=lambda: {
            "tone": "Authoritative, Innovative, Mission-driven, Impactful",
            "tagline": "Building the Intelligence Layer for a Digital India",
            "primary_colors": ["#0ea5e9", "#7c3aed", "#10b981"]
        }
    )
    crm_config: Dict[str, Any] = Field(default_factory=dict)
    social_accounts: Dict[str, Any] = Field(
        default_factory=lambda: {
            "linkedin": "https://www.linkedin.com/company/aipnt-technologies-pvt-ltd/",
            "twitter": "https://x.com/aipnt.tech",
            "facebook": "https://www.facebook.com/aipnt.tech/",
            "instagram": "https://www.instagram.com/aipnt.tech/"
        }
    )
    analytics_platforms: Dict[str, Any] = Field(
        default_factory=lambda: {"google_analytics_4": "enabled", "posthog": "enabled"}
    )


class OrganizationCreate(OrganizationBase):
    """Schema for tenant onboarding."""
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    website_url: Optional[str] = None
    geography: Optional[str] = None
    customer_type: Optional[str] = None
    sales_cycle: Optional[str] = None
    monthly_marketing_budget: Optional[float] = None
    monthly_lead_target: Optional[int] = None
    revenue_target: Optional[float] = None
    products: Optional[List[str]] = None
    services: Optional[List[str]] = None
    target_markets: Optional[List[str]] = None
    competitors: Optional[List[str]] = None
    existing_channels: Optional[List[str]] = None
    brand_guidelines: Optional[Dict[str, Any]] = None


class OrganizationResponse(OrganizationBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
