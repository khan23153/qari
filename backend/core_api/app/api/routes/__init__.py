"""Routes __init__ — import all route modules."""

from app.api.routes import (
    corpus,
    lessons,
    users,
    progress,
    flashcards,
    recitation,
    scholar,
    content_bundle,
)

__all__ = [
    "corpus", "lessons", "users", "progress",
    "flashcards", "recitation", "scholar", "content_bundle",
]
