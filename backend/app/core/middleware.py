"""
Production Middleware: Rate Limiting, Security Headers, and Global Exception Handling
Corresponds to Master Specification Section 46 & Section 53.
"""

import time
import uuid
import logging
from typing import Dict, Tuple
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ProductionSecurityMiddleware(BaseHTTPMiddleware):
    """
    Applies enterprise security headers and request tracing IDs to every response.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        # Set Security Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter per client IP.
    Default: 200 requests per minute per IP.
    """

    def __init__(self, app, max_requests: int = 300, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clients: Dict[str, Tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # Exclude static assets and healthcheck from aggressive rate limiting
        if request.url.path.startswith("/static") or request.url.path in ["/health", "/", "/docs"]:
            return await call_next(request)

        count, start_time = self._clients.get(client_ip, (0, now))

        if now - start_time > self.window_seconds:
            # Window expired, reset
            self._clients[client_ip] = (1, now)
        else:
            if count >= self.max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded. Please throttle your requests.",
                        "retry_after_seconds": int(self.window_seconds - (now - start_time)),
                    },
                    headers={"Retry-After": str(int(self.window_seconds - (now - start_time)))},
                )
            self._clients[client_ip] = (count + 1, start_time)

        return await call_next(request)
