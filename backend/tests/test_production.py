"""
Phase 10: Production Readiness, Security Middleware, and Frontend Serving Tests
Covers:
- Security Headers Injection (X-Request-ID, nosniff, DENY)
- Rate Limiting Middleware
- Static Asset Delivery (tracker.js, index.css, app.js)
- Single Page Application (SPA) Root Serving (/app)
- Production Health & System Telemetry
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_security_headers_middleware():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        assert "x-request-id" in res.headers
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert res.headers.get("x-frame-options") == "DENY"
        assert res.headers.get("x-xss-protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_spa_and_static_assets_serving():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Test /app serves index.html
        res_spa = await ac.get("/app")
        assert res_spa.status_code == 200
        assert "AIPNT" in res_spa.text
        assert "Executive Revenue Dashboard" in res_spa.text

        # 2. Test /static/tracker.js
        res_tracker = await ac.get("/static/tracker.js")
        assert res_tracker.status_code == 200
        assert "aipnt" in res_tracker.text

        # 3. Test /static/index.css
        res_css = await ac.get("/static/index.css")
        assert res_css.status_code == 200
        assert "--bg-primary" in res_css.text

        # 4. Test /static/app.js
        res_js = await ac.get("/static/app.js")
        assert res_js.status_code == 200
        assert "routes" in res_js.text


@pytest.mark.asyncio
async def test_rate_limiter_permits_ordinary_traffic():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for _ in range(10):
            res = await ac.get("/")
            assert res.status_code == 200
