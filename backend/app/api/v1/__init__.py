"""
API v1 Router Registry
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.organizations import router as org_router
from app.api.v1.agents import router as agents_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.core_agents import router as core_agents_router
from app.api.v1.growth_agents import router as growth_agents_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.autonomous import router as autonomous_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.evaluation import router as evaluation_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router, tags=["Health & Telemetry"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Onboarding"])
api_v1_router.include_router(org_router, prefix="/organizations", tags=["Organization Management"])
api_v1_router.include_router(agents_router, prefix="/agents", tags=["Agent Orchestration & Approvals"])
api_v1_router.include_router(knowledge_router, prefix="/knowledge", tags=["RAG Knowledge Base"])
api_v1_router.include_router(core_agents_router, tags=["Core Marketing Agents"])
api_v1_router.include_router(growth_agents_router, tags=["Growth Marketing Agents"])
api_v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics & Revenue Operations"])
api_v1_router.include_router(analytics_router, tags=["Analytics & Revenue Operations (Top-level)"])
api_v1_router.include_router(autonomous_router, tags=["Autonomous Agents & Optimization"])
api_v1_router.include_router(integrations_router, tags=["Integrations & Connectors"])
api_v1_router.include_router(evaluation_router, tags=["Evaluation, Guardrails & Security"])

