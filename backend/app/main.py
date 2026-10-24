import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.database import init_db
from app.core.middleware import ProductionSecurityMiddleware, RateLimiterMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database schema is initialized
    await init_db()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise-grade autonomous Agentic AI Marketing & Revenue Operations Platform. "
                "Transforms high-level business goals directly into multi-agent strategy, execution, and revenue.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# Production Middlewares
app.add_middleware(ProductionSecurityMiddleware)
app.add_middleware(RateLimiterMiddleware, max_requests=1000, window_seconds=60)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mounting
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/app", tags=["Frontend SPA"], response_class=FileResponse)
async def serve_spa():
    index_file = static_dir / "index.html"
    return FileResponse(str(index_file))


@app.get("/", tags=["Root"])
async def root(request: Request):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header and not "application/json" in accept_header:
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
        "app_ui": "/app",
        "api_v1": settings.API_V1_PREFIX
    }
