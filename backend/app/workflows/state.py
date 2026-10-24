"""
MarketingState TypedDict & Pydantic Schemas for LangGraph Workflows
Corresponds exactly to Master Specification Section 21 & Section 47.
"""

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class MarketingState(TypedDict):
    """Stateful schema matching Master Specification Section 21."""
    organization_id: str
    objective: str
    market_research: dict
    competitors: list
    personas: list
    campaigns: list
    content: list
    leads: list
    analytics: dict
    recommendations: list
    approvals: list
    execution_status: str
    current_step: str
    messages: list


# Pydantic Schemas for Structured Agent Reasoning (Section 47 & 50)

class MarketResearchOutput(BaseModel):
    market_summary: str
    trends: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


class CompetitorProfile(BaseModel):
    name: str
    market_share: str
    strengths: List[str]
    weaknesses: List[str]
    aipnt_moat: str


class CompetitiveAnalysisOutput(BaseModel):
    competitor_summary: str
    competitors: List[CompetitorProfile]
    content_gaps: List[str]
    opportunities: List[str]


class BuyerPersonaData(BaseModel):
    role: str
    pain_points: List[str]
    buying_triggers: List[str]
    decision_criteria: List[str]


class PersonaAnalysisOutput(BaseModel):
    icp_summary: str
    personas: List[BuyerPersonaData]


class CampaignPlan(BaseModel):
    campaign_name: str
    objective: str
    audience: str
    budget: float
    channels: List[str]
    message: str
    target_cpl: float
    target_cac: float
    expected_pipeline: float


class ContentAsset(BaseModel):
    objective: str
    audience: str
    funnel_stage: str
    content_type: str
    topic: str
    cta: str
    expected_business_impact: str


class OptimizationReportOutput(BaseModel):
    executive_summary: str
    pipeline_impact: float
    recommended_budget: float
    key_actions: List[str]
    kpis: Dict[str, Any]
