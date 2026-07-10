"""Aggregate all route routers into a single APIRouter."""

from fastapi import APIRouter

from app.api.routes import (
    corpus,
    lessons,
    users,
    progress,
    flashcards,
    recitation,
    scholar,
    content_bundle,
    app_release,
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(corpus.router)
api_router.include_router(lessons.router)
api_router.include_router(users.router)
api_router.include_router(progress.router)
api_router.include_router(flashcards.router)
api_router.include_router(recitation.router)
api_router.include_router(scholar.router)
api_router.include_router(content_bundle.router)
api_router.include_router(app_release.router)
