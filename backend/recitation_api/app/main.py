"""FastAPI application for the Qari recitation_api service."""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter, Histogram, Gauge

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

# --- Prometheus metrics ---
REQUEST_COUNT = Counter(
    "qari_recitation_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "qari_recitation_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)
ACTIVE_REQUESTS = Gauge(
    "qari_recitation_http_active_requests",
    "Active HTTP requests",
)
RECITATION_QUEUED = Counter(
    "qari_recitation_queued_total",
    "Total recitation jobs queued",
)
RECITATION_COMPLETED = Counter(
    "qari_recitation_completed_total",
    "Total recitation jobs completed",
    ["status"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown hooks."""
    logger.info("app.starting", service=settings.app_name, version=settings.app_version)

    # Ensure audio storage directory exists
    os.makedirs(settings.audio_storage_path, exist_ok=True)

    logger.info("app.started")

    yield

    logger.info("app.stopped")


def create_app() -> FastAPI:
    """Create and configure the recitation FastAPI application."""
    app = FastAPI(
        title="Qari Recitation API",
        description="Quran Learning App — Recitation API service (audio upload, WebSocket results, Redis Streams inference queue)",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routes ---
    app.include_router(api_router)

    # --- Health check ---
    @app.get("/health", tags=["health"])
    async def health_check():
        """Liveness probe."""
        return {"status": "ok", "service": settings.app_name, "version": settings.app_version}

    # --- Prometheus metrics endpoint ---
    @app.get("/metrics", tags=["monitoring"])
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # --- Metrics middleware ---
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        ACTIVE_REQUESTS.inc()
        import time
        start = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=str(response.status_code),
            )
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)
            return response
        finally:
            ACTIVE_REQUESTS.dec()

    return app


app = create_app()
