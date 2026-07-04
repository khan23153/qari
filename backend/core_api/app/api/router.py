"""Main API router aggregating all route modules."""
from fastapi import APIRouter

from app.api.routes import corpus, lessons, users, progress, flashcards, recitation, scholar

api_router = APIRouter()
api_router.include_router(corpus.router, tags=["corpus"])
api_router.include_router(lessons.router, tags=["lessons"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(progress.router, tags=["progress"])
api_router.include_router(flashcards.router, tags=["flashcards"])
api_router.include_router(recitation.router, tags=["recitation"])
api_router.include_router(scholar.router, tags=["scholar"])
