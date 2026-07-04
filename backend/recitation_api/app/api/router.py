"""Recitation API router."""
from fastapi import APIRouter

from app.api.routes import recitation, websocket

api_router = APIRouter()
api_router.include_router(recitation.router, tags=["recitation"])
api_router.include_router(websocket.router, tags=["websocket"])
