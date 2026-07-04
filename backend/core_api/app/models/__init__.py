"""Import all models so SQLAlchemy registers them on Base.metadata."""

from app.models.corpus import Ayah, Qari, Root, Surah, TajweedAnnotation, Word
from app.models.content import Badge, Lesson, QuizQuestion
from app.models.user import (
    Flashcard,
    FlashcardReview,
    RecitationSession,
    RecitationWordResult,
    ScholarQuestion,
    User,
    UserAyahProgress,
    UserBadge,
    UserLessonProgress,
    UserStats,
)

__all__ = [
    "Ayah", "Qari", "Root", "Surah", "TajweedAnnotation", "Word",
    "Badge", "Lesson", "QuizQuestion",
    "Flashcard", "FlashcardReview", "RecitationSession", "RecitationWordResult",
    "ScholarQuestion", "User", "UserAyahProgress", "UserBadge",
    "UserLessonProgress", "UserStats",
]
