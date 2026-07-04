"""
Shared module for the Qari backend.

Contains common enums, constants, and Redis key patterns used across
both the core_api and recitation_api services.
"""

import enum
from typing import Final

# ---------------------------------------------------------------------------
# Redis key patterns
# ---------------------------------------------------------------------------

class RedisKeys:
    """Centralised Redis key patterns.

    All keys are namespaced under ``qari:`` to avoid collisions with other
    services that may share the same Redis instance.
    """

    # Caching – corpus
    SURAH_CACHE: Final[str] = "qari:cache:surah:{surah_id}"
    SURAH_LIST_CACHE: Final[str] = "qari:cache:surahs"
    AYAH_CACHE: Final[str] = "qari:cache:ayah:{surah}:{ayah}:{lang}"
    AYAH_RANGE_CACHE: Final[str] = "qari:cache:ayahs:{surah}:{from_}:{to}:{lang}:{qari}"
    WORD_CACHE: Final[str] = "qari:cache:word:{surah}:{ayah}:{pos}:{lang}"
    ROOT_CACHE: Final[str] = "qari:cache:root:{root_id}:{lang}"

    # Caching – content
    LESSON_LIST_CACHE: Final[str] = "qari:cache:lessons:{module}:{lang}"
    LESSON_CACHE: Final[str] = "qari:cache:lesson:{lesson_id}:{lang}"
    CONTENT_BUNDLE_CACHE: Final[str] = "qari:cache:bundle:{scope}:{lang}"

    # Caching – user
    HOME_CACHE: Final[str] = "qari:cache:home:{user_id}"

    # Streak lock – 48 h TTL
    STREAK_LOCK: Final[str] = "qari:streak:lock:{user_id}:{date}"

    # Rate limiting – sliding window
    RATE_LIMIT: Final[str] = "qari:ratelimit:{user_id}:{endpoint}"

    # Flashcard daily cap
    FLASHCARD_DAILY_CAP: Final[str] = "qari:flashcard:daily:{user_id}:{date}"

    # Idempotency
    IDEMPOTENCY: Final[str] = "qari:idem:{user_id}:{key}"

    # Recitation – Redis Streams
    RECITATION_STREAM: Final[str] = "qari:recitation:jobs"
    RECITATION_RESULTS: Final[str] = "qari:recitation:results:{session_id}"
    RECITATION_SESSION: Final[str] = "qari:recitation:session:{session_id}"

    # TTLs (seconds)
    TTL_AYAH: Final[int] = 86_400        # 24 h
    TTL_WORD: Final[int] = 86_400        # 24 h
    TTL_HOME: Final[int] = 60            # 60 s
    TTL_STREAK_LOCK: Final[int] = 172_800  # 48 h
    TTL_LESSON: Final[int] = 3_600       # 1 h
    TTL_BUNDLE: Final[int] = 3_600       # 1 h
    TTL_RATE_LIMIT: Final[int] = 60      # 1 min window


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AppLanguage(str, enum.Enum):
    """Supported UI / content languages."""
    en = "en"
    ur = "ur"
    hi_latn = "hi_latn"


class StartingPath(str, enum.Enum):
    """Onboarding starting path – determines initial lesson sequence."""
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    tajweed_focus = "tajweed_focus"
    memorization = "memorization"


class POSGroup(str, enum.Enum):
    """Part-of-speech groups used in morphology."""
    noun = "noun"
    verb = "verb"
    particle = "particle"
    pronoun = "pronoun"
    adjective = "adjective"
    adverb = "adverb"
    conjunction = "conjunction"
    preposition = "preposition"
    interjection = "interjection"
    proper_noun = "proper_noun"
    number = "number"


class RecitationVerdict(str, enum.Enum):
    """Per-word recitation verdict from the ML engine."""
    correct = "correct"
    mispronounced = "mispronounced"
    skipped = "skipped"
    extra = "extra"
    unclear = "unclear"


class LessonReviewStatus(str, enum.Enum):
    """Editorial review status for lessons."""
    draft = "draft"
    in_review = "in_review"
    published = "published"
    archived = "archived"


class LessonStatus(str, enum.Enum):
    """User-facing lesson completion status (progress tracking)."""
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class FlashcardGrade(int, enum.Enum):
    """SM-2 review grade (0-5)."""
    black = 0
    terrible = 1
    bad = 2
    hard = 3
    good = 4
    perfect = 5


class BadgeTier(str, enum.Enum):
    """Badge rarity tiers."""
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platinum = "platinum"


class RecitationStatus(str, enum.Enum):
    """Recitation session lifecycle."""
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ScholarQuestionStatus(str, enum.Enum):
    """Scholar Q&A lifecycle."""
    pending = "pending"
    answered = "answered"
    rejected = "rejected"


# ---------------------------------------------------------------------------
# Business constants
# ---------------------------------------------------------------------------

MAX_AYAHS_PER_REQUEST: Final[int] = 20
FLASHCARD_DAILY_CAP: Final[int] = 20
STREAK_FREEZE_GRACE_WINDOW_DAYS: Final[int] = 30
STREAK_FREEZE_GRANT: Final[int] = 1
DEFAULT_FLASHCARD_LIMIT: Final[int] = 20
SM2_MIN_EASINESS: Final[float] = 1.3
SM2_MAX_EASINESS: Final[float] = 2.5
SM2_INITIAL_EASINESS: Final[float] = 2.5
SM2_INITIAL_INTERVAL: Final[int] = 1
SM2_REPETITION_INTERVAL: Final[int] = 6
