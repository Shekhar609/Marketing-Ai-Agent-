"""
Agent Orchestration, LangGraph Execution, and MCP Risk Gate Tests
Corresponds to Master Specification Phase 2 Deliverables.
"""

import pytest
from httpx import AsyncClient

from app.tools.registry import tool_registry


@pytest.mark.asyncio
async def test_mcp_tools_listing(async_client: AsyncClient):
    response = await async_client.get("/api/v1/agents/tools")
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) >= 5
    tool_names = [t["name"] for t in tools]
    assert "search_web" in tool_names
    assert "search_competitor" in tool_names
    assert "calculate_lead_score" in tool_names
    assert "send_email" in tool_names
    assert "create_campaign" in tool_names

    # Verify risk levels
    create_campaign_tool = next(t for t in tools if t["name"] == "create_campaign")
    assert create_campaign_tool["risk_level"] == "CRITICAL"
    assert create_campaign_tool["requires_approval"] is True


@pytest.mark.asyncio
async def test_tool_permission_gate_blocks_high_risk():
    # Attempt to execute high-risk tool without bypass or db session
    res = await tool_registry.execute(
        name="create_campaign",
        params={"budget": 100000},
        organization_id="org-test-123",
        bypass_approval=False,
    )
    assert res.success is False
    assert res.requires_approval is True
    assert "requires human approval" in res.error


@pytest.mark.asyncio
async def test_agent_workflow_execution(async_client: AsyncClient):
    # 1. Onboard Organization
    onboard_payload = {
        "organization_name": "AIPNT Growth Unit",
        "organization_slug": "aipnt-growth",
        "admin_email": "agent_test@aipnt.in",
        "admin_password": "SecurePassword123!",
        "admin_name": "Agent Ops Lead",
        "monthly_budget": 500000.0,
        "monthly_leads_target": 500,
        "revenue_target": 10000000.0,
    }
    onboard_res = await async_client.post("/api/v1/auth/onboard", json=onboard_payload)
    assert onboard_res.status_code == 201
    token = onboard_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Trigger End-to-End Autonomous Workflow (Section 45)
    run_payload = {
        "objective": "Generate 500 qualified leads for our AI customer-support SaaS in India within 60 days with a ₹5 lakh marketing budget.",
        "workflow_type": "growth_plan_60_days",
    }
    run_res = await async_client.post("/api/v1/agents/run", json=run_payload, headers=headers)
    assert run_res.status_code == 202
    run_data = run_res.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["current_step"] == "COMPLETED"
    assert run_data["latency_ms"] > 0
    assert run_data["total_tokens"] > 0

    # Verify State Checkpoint contents (Section 21)
    checkpoint = run_data["state_checkpoint"]
    assert "market_research" in checkpoint
    assert "competitors" in checkpoint
    assert "personas" in checkpoint
    assert "campaigns" in checkpoint
    assert "content" in checkpoint
    assert "leads" in checkpoint
    assert "analytics" in checkpoint

    # 3. Retrieve Run by ID
    run_id = run_data["id"]
    get_run_res = await async_client.get(f"/api/v1/agents/runs/{run_id}", headers=headers)
    assert get_run_res.status_code == 200
    assert get_run_res.json()["id"] == run_id
