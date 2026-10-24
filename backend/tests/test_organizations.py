"""
Organization Configuration & Multi-Tenant Isolation Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tenant_profile_and_update(async_client: AsyncClient):
    # Onboard Org 1
    org1_payload = {
        "organization_name": "AIPNT Alpha",
        "organization_slug": "aipnt-alpha",
        "admin_email": "alpha@aipnt.in",
        "admin_password": "AlphaPassword123!",
        "admin_name": "Alpha Admin",
        "monthly_budget": 300000.0,
        "monthly_leads_target": 350,
        "revenue_target": 7000000.0
    }
    res1 = await async_client.post("/api/v1/auth/onboard", json=org1_payload)
    assert res1.status_code == 201
    token1 = res1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Fetch current organization profile
    get_res = await async_client.get("/api/v1/organizations/me", headers=headers1)
    assert get_res.status_code == 200
    org1_data = get_res.json()
    assert org1_data["slug"] == "aipnt-alpha"
    assert org1_data["monthly_marketing_budget"] == 300000.0

    # Update marketing budget and add competitor
    patch_payload = {
        "monthly_marketing_budget": 600000.0,
        "monthly_lead_target": 600,
        "competitors": ["HealthCube", "Clinics On Cloud", "NewRival AI"]
    }
    patch_res = await async_client.patch(
        "/api/v1/organizations/me",
        json=patch_payload,
        headers=headers1
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["monthly_marketing_budget"] == 600000.0
    assert updated_data["monthly_lead_target"] == 600
    assert "NewRival AI" in updated_data["competitors"]


@pytest.mark.asyncio
async def test_multi_tenant_isolation(async_client: AsyncClient):
    # Onboard Org A
    res_a = await async_client.post("/api/v1/auth/onboard", json={
        "organization_name": "Tenant A Corp",
        "organization_slug": "tenant-a",
        "admin_email": "admin@tenanta.com",
        "admin_password": "TenantAPassword123!",
        "admin_name": "Admin A",
        "monthly_budget": 100000.0,
        "monthly_leads_target": 100,
        "revenue_target": 2000000.0
    })
    token_a = res_a.json()["access_token"]

    # Onboard Org B
    res_b = await async_client.post("/api/v1/auth/onboard", json={
        "organization_name": "Tenant B Corp",
        "organization_slug": "tenant-b",
        "admin_email": "admin@tenantb.com",
        "admin_password": "TenantBPassword123!",
        "admin_name": "Admin B",
        "monthly_budget": 900000.0,
        "monthly_leads_target": 900,
        "revenue_target": 18000000.0
    })
    token_b = res_b.json()["access_token"]

    # Verify Org A's token returns Org A data
    res_me_a = await async_client.get(
        "/api/v1/organizations/me",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_me_a.json()["slug"] == "tenant-a"
    assert res_me_a.json()["monthly_marketing_budget"] == 100000.0

    # Verify Org B's token returns Org B data
    res_me_b = await async_client.get(
        "/api/v1/organizations/me",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_me_b.json()["slug"] == "tenant-b"
    assert res_me_b.json()["monthly_marketing_budget"] == 900000.0
