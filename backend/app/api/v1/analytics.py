"""
Analytics, Revenue Operations, and Executive Copilot API Router
Corresponds to Master Specification Sections 16, 29, 30, 31, 32, 33, 34, 36.

Provides endpoints for:
- GET  /api/v1/analytics/dashboard                — Executive KPI Dashboard (Section 31)
- POST /api/v1/analytics/analyze                  — Analytics Agent Audit (Section 16)
- GET  /api/v1/analytics/funnel                   — Marketing Funnel Engine (Section 29)
- POST /api/v1/analytics/attribution              — Multi-touch Revenue Attribution (Section 30)
- GET  /api/v1/analytics/reports                  — List Generated Reports (Section 33)
- POST /api/v1/analytics/reports/generate         — Trigger Report Generation (Daily/Weekly/Monthly/Quarterly)
- GET  /api/v1/analytics/alerts                   — System Alerts and Anomaly Notifications (Section 34)
- POST /api/v1/analytics/recommendations/generate — Generate AI Recommendations (Section 36)
- POST /api/v1/analytics/copilot/query            — AI Executive Copilot Conversational Query (Section 32)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_current_user, get_db
from app.models.organization import Organization
from app.models.user import User
from app.models.analytics import Alert, Recommendation, Report

from app.agents.analytics import AnalyticsAuditRequest, analytics_agent
from app.agents.copilot import CopilotQueryRequest, executive_copilot_agent
from app.services.analytics_service import analytics_service

router = APIRouter()


# --------------------------------------------------------------------------
# 1. Executive Dashboard (Section 31)
# --------------------------------------------------------------------------

@router.get("/dashboard")
async def get_dashboard(
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated executive dashboard metrics including revenue overview,
    pipeline created, CAC, CPL, channel breakdown, and marketing ROI.
    """
    try:
        return await analytics_service.get_dashboard_summary(db, tenant.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assemble dashboard: {str(e)}",
        )


# --------------------------------------------------------------------------
# 2. Marketing Funnel Engine (Section 29)
# --------------------------------------------------------------------------

@router.get("/funnel")
async def get_funnel_progression(
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve full marketing funnel conversion stages from
    Visitor -> Lead -> MQL -> SQL -> Opportunity -> Customer -> Expansion.
    """
    try:
        return await analytics_service.get_funnel_metrics(db, tenant.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve funnel metrics: {str(e)}",
        )


# --------------------------------------------------------------------------
# 3. Revenue Attribution Engine (Section 30)
# --------------------------------------------------------------------------

class AttributionRequest(BaseModel):
    model: str = Field(
        default="w_shaped",
        description="Attribution model: first_touch, last_touch, linear, time_decay, w_shaped"
    )


@router.post("/attribution")
async def calculate_attribution(
    request: AttributionRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate multi-touch revenue attribution across campaigns and marketing channels.
    """
    try:
        return await analytics_service.calculate_revenue_attribution(
            db, tenant.id, request.model
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate revenue attribution: {str(e)}",
        )


# --------------------------------------------------------------------------
# 4. Analytics Agent Invocations (Section 16, 36)
# --------------------------------------------------------------------------

@router.post("/analyze")
async def run_analytics_audit(
    request: AnalyticsAuditRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the Analytics Agent to perform performance audits,
    root-cause diagnostics on CAC/CPL anomalies, and efficiency rankings.
    """
    try:
        result = await analytics_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics Agent failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# 5. Report Generation & Retrieval (Section 33, 36)
# --------------------------------------------------------------------------

class ReportGenerateRequest(BaseModel):
    report_type: str = Field(
        default="weekly",
        description="Report frequency: daily, weekly, monthly, quarterly"
    )


@router.get("/reports")
async def list_reports(
    report_type: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List historical marketing reports generated for this tenant."""
    query = select(Report).where(Report.organization_id == tenant.id)
    if report_type:
        query = query.where(Report.report_type == report_type.lower())
    query = query.order_by(Report.created_at.desc()).limit(limit)

    results = await db.scalars(query)
    reports = list(results.all())

    return [
        {
            "id": r.id,
            "title": r.title,
            "report_type": r.report_type,
            "period_start": r.period_start.isoformat(),
            "period_end": r.period_end.isoformat(),
            "metrics_summary": r.metrics_summary,
            "key_findings": r.key_findings,
            "strategic_recommendations": r.strategic_recommendations,
            "content_markdown": r.content_markdown,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]


@router.post("/reports/generate")
async def create_report(
    request: ReportGenerateRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and store a new executive marketing intelligence report."""
    try:
        report = await analytics_service.generate_report(
            db, tenant.id, request.report_type
        )
        return {
            "id": report.id,
            "title": report.title,
            "report_type": report.report_type,
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "metrics_summary": report.metrics_summary,
            "content_markdown": report.content_markdown,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# 6. Proactive Alerts System (Section 34, 36)
# --------------------------------------------------------------------------

@router.get("/alerts")
async def list_alerts(
    status_filter: Optional[str] = Query(default="ACTIVE"),
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve active and historical threshold alerts and anomalies."""
    try:
        alerts = await analytics_service.evaluate_alerts(db, tenant.id)
        if status_filter:
            alerts = [a for a in alerts if a.status == status_filter.upper()]

        return [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "metric_value": a.metric_value,
                "threshold_value": a.threshold_value,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alerts: {str(e)}",
        )


# --------------------------------------------------------------------------
# 7. AI Recommendations (Section 36)
# --------------------------------------------------------------------------

@router.post("/recommendations/generate")
async def generate_recommendations(
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate strategic marketing optimizations across budget, channel, and content."""
    try:
        dash = await analytics_service.get_dashboard_summary(db, tenant.id)
        recs = []
        for r_text in dash["ai_recommendations"]:
            rec = Recommendation(
                organization_id=tenant.id,
                category="budget" if "shift" in r_text.lower() or "budget" in r_text.lower() else "channel",
                title=r_text[:80],
                description=r_text,
                estimated_impact="High" if "roi" in r_text.lower() else "Medium",
                effort="Low",
                status="pending",
            )
            db.add(rec)
            recs.append(rec)
        await db.commit()

        return [
            {
                "id": r.id,
                "category": r.category,
                "title": r.title,
                "description": r.description,
                "estimated_impact": r.estimated_impact,
                "status": r.status,
            }
            for r in recs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}",
        )


# --------------------------------------------------------------------------
# 8. AI Executive Copilot (Section 32)
# --------------------------------------------------------------------------

@router.post("/copilot/query")
async def query_executive_copilot(
    request: CopilotQueryRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Conversational AI Executive Copilot query answering grounded questions
    regarding revenue, growth opportunities, budget allocation, and pipeline.
    """
    try:
        result = await executive_copilot_agent.execute(
            db=db,
            organization_id=tenant.id,
            params=request.model_dump(),
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Executive Copilot query failed: {str(e)}",
        )
