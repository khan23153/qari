"""Import all models so Alembic and SQLAlchemy can discover them."""
from app.models.corpus import (
    Surah, Ayah, Root, Word, TajweedAnnotation, Qari,
)
from app.models.content import Lesson, QuizQuestion, Badge
from app.models.user import (
    User, UserLessonProgress, UserAyahProgress,
    Flashcard, FlashcardReview,
    UserStats, UserBadge,
    RecitationSession, RecitationWordResult,
    ScholarQuestion,
)

__all__ = [
    "Surah", "Ayah", "Root", "Word", "TajweedAnnotation", "Qari",
    "Lesson", "QuizQuestion", "Badge",
    "User", "UserLessonProgress", "UserAyahProgress",
    "Flashcard", "FlashcardReview",
    "UserStats", "UserBadge",
    "RecitationSession", "RecitationWordResult",
    "ScholarQuestion",
]
