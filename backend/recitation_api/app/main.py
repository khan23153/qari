"""
Qari Recitation API — audio upload, inference queue, WebSocket results.

Separate from core-api so recitation load never degrades the app.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Qari Recitation API",
    version="1.0.0",
    description="Audio upload + AI recitation feedback engine",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.router import api_router
app.include_router(api_router, prefix="/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "recitation-api", "version": "1.0.0"}
