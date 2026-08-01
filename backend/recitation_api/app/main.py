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

# Compatibility guard for the live session's silence gate. The RMS helper is a
# module-level function, while the streaming code calls it through the session
# instance. Bind it as a static method at import time so production live ASR
# does not fail every pass with AttributeError. This is deliberately centralized
# here until the streaming service is split into smaller units.
from app.services import streaming_session as _streaming_session

if not hasattr(_streaming_session.StreamingRecitationSession, "_rms_energy"):
    _streaming_session.StreamingRecitationSession._rms_energy = staticmethod(
        _streaming_session._rms_energy
    )

setup_logging()
logger = get_logger(__name__)

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
    logger.info("app.starting", service=settings.app_name, version=settings.app_version)
    os.makedirs(settings.audio_storage_path, exist_ok=True)
    logger.info("app.started")
    yield
    logger.info("app.stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Qari Recitation API",
        description=(
            "Quran Learning App — Recitation API service "
            "(audio upload, WebSocket results, Redis Streams inference queue)"
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health_check():
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    @app.get("/metrics", tags=["monitoring"])
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

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
