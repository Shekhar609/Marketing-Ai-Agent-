"""
Authentication & Onboarding Integration Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_organization_onboarding_and_login(async_client: AsyncClient):
    # 1. Onboard a new organization
    onboard_payload = {
        "organization_name": "AI PNT Technologies Private Limited",
        "organization_slug": "aipnt-test",
        "industry": "B2B SaaS / DeepTech AI",
        "admin_email": "founder@aipnt.in",
        "admin_password": "SuperSecurePassword123!",
        "admin_name": "AIPNT Executive",
        "monthly_budget": 500000.0,
        "monthly_leads_target": 500,
        "revenue_target": 10000000.0
    }
    
    response = await async_client.post("/api/v1/auth/onboard", json=onboard_payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "founder@aipnt.in"
    assert data["user"]["role"] == "admin"
    assert data["organization"]["slug"] == "aipnt-test"
    assert data["organization"]["monthly_marketing_budget"] == 500000.0

    token = data["access_token"]

    # 2. Test Login
    login_payload = {
        "email": "founder@aipnt.in",
        "password": "SuperSecurePassword123!"
    }
    login_res = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == "founder@aipnt.in"

    # 3. Test Invalid Credentials
    bad_login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "founder@aipnt.in", "password": "WrongPassword!"}
    )
    assert bad_login_res.status_code == 401

    # 4. Test Authenticated Profile (/api/v1/auth/me)
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "founder@aipnt.in"
    assert me_data["role"] == "admin"
