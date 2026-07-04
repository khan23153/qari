"""Shared constants and types between core-api and recitation-api."""
from enum import Enum


class AppLanguage(str, Enum):
    EN = "en"
    UR = "ur"
    HI_LATN = "hi_latn"


class StartingPath(str, Enum):
    FOUNDATION = "foundation"
    QURAN_DIRECT = "quran_direct"


class POSGroup(str, Enum):
    ISM = "ism"
    FIL = "fil"
    HARF = "harf"


class RecitationVerdict(str, Enum):
    CORRECT = "correct"
    MISPRONOUNCED = "mispronounced"
    OMITTED = "omitted"
    INSERTED_EXTRA = "inserted_extra"
    LOW_CONFIDENCE = "low_confidence"


class LessonReviewStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    SCHOLAR_APPROVED = "scholar_approved"
    PUBLISHED = "published"


# Redis key patterns
REDIS_KEYS = {
    "ayahs": "ayahs:{surah}:{page}:{lang}:{qari}",
    "word": "word:{s}:{a}:{p}:{lang}",
    "home": "home:{user_id}",
    "streak_lock": "streak-lock:{user_id}:{date}",
    "rate_limit": "rl:{user_id}",
    "recitation_jobs": "recitation:jobs",
    "recitation_result": "recitation:result:{session_id}",
}
