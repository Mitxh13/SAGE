"""
FastAPI application entry point for SAGE backend.

Sets up CORS, initializes SQLite database tables, registers route controllers,
and exposes system health checks.

Reference: docs/ARCHITECTURE.md §System flow & API contract
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database.db import init_db
from backend.routers import chat, sessions, units

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database tables on application startup."""
    init_db()
    yield


app = FastAPI(
    title=f"{settings.APP_NAME} Backend API",
    description=(
        "Socratic Agent for Guided Exploration — Core Orchestrator & Tutoring API "
        "for Prompt Engineering and Generative AI"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, str | bool]:
    """Check API server health and active mock AI configuration."""
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": "0.1.0",
        "use_mock_ai": settings.USE_MOCK_AI,
        "use_mock_analyzer": settings.should_mock_analyzer,
        "use_mock_rag": settings.should_mock_rag,
        "use_mock_tutor": settings.should_mock_tutor,
    }


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Root endpoint redirecting to interactive documentation."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs_url": "/docs",
        "health_check": "/api/health",
    }


# ── Mount Routers ────────────────────────────────────────────────────────────
app.include_router(units.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
