"""
Qari Core API — FastAPI application entrypoint.

Serves Quran corpus content, learning lessons, user progress,
flashcards (SRS), gamification, and Ask-a-Scholar endpoints.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine, Base
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    setup_logging()
    # DB tables are managed by Alembic migrations; this is a safety net for dev.
    if settings.ENV == "dev":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Qari Core API",
    version="1.0.0",
    description="Quran learning app — content, progress, flashcards, gamification",
    lifespan=lifespan,
    default_response_class=JSONResponse,
)

# CORS — mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Routes
app.include_router(api_router, prefix="/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "core-api", "version": "1.0.0"}
