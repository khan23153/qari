"""FastAPI application factory with CORS, Prometheus, health check, and lifespan."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter, Histogram, Gauge

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.security import init_firebase
from app.db.session import engine
from app.services.redis_service import init_redis, close_redis

setup_logging()
logger = get_logger(__name__)

# --- Prometheus metrics ---
REQUEST_COUNT = Counter(
    "qari_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "qari_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)
ACTIVE_REQUESTS = Gauge(
    "qari_http_active_requests",
    "Active HTTP requests",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown hooks."""
    logger.info("app.starting", service=settings.app_name, version=settings.app_version)

    # --- Startup ---
    await init_redis()
    init_firebase()
    logger.info("app.started")

    yield

    # --- Shutdown ---
    logger.info("app.stopping")
    await close_redis()
    await engine.dispose()
    logger.info("app.stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Qari Core API",
        description="Quran Learning App — Core API service",
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

    # --- Exception handlers (RFC 7807) ---
    register_exception_handlers(app)

    # --- Routes ---
    app.include_router(api_router)

    # --- Health check ---
    @app.get("/health", tags=["health"])
    async def health_check():
        """Liveness probe."""
        return {"status": "ok", "service": settings.app_name, "version": settings.app_version}

    @app.get("/ready", tags=["health"])
    async def readiness_check():
        """Readiness probe — checks Redis and DB connectivity."""
        checks = {"redis": "ok", "db": "ok"}
        try:
            from app.services.redis_service import get_redis
            await get_redis().ping()
        except Exception:
            checks["redis"] = "error"
        try:
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        except Exception:
            checks["db"] = "error"
        all_ok = all(v == "ok" for v in checks.values())
        return {"status": "ok" if all_ok else "degraded", "checks": checks}

    # --- Prometheus metrics endpoint ---
    @app.get("/metrics", tags=["monitoring"])
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # --- Metrics middleware ---
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        import time

        ACTIVE_REQUESTS.inc()
        method = request.method
        endpoint = request.url.path
        start = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=str(response.status_code),
            ).inc()
            return response
        finally:
            ACTIVE_REQUESTS.dec()

    return app


app = create_app()
