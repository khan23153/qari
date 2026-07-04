"""Aggregate all route routers."""

from fastapi import APIRouter

from app.api.routes import recitation, websocket

api_router = APIRouter()
api_router.include_router(recitation.router)
api_router.include_router(websocket.router)
