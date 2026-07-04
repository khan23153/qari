"""Schemas __init__ — re-export all schemas for convenience."""

from app.schemas.common import PaginatedResponse, ProblemDetail, HealthResponse, LangQueryParams
from app.schemas.corpus import (
    AyahOut, QariBrief, RootBrief, RootDetail,
    SurahBrief, SurahDetail, TajweedAnnotationOut,
    WordBrief, WordDetail, WordOccurrence,
)
from app.schemas.content import (
    BadgeOut, BadgeAwarded as BadgeAwardedSchema, LessonBrief, LessonDetail,
    QuizQuestionOut, UserBadgeOut,
)
from app.schemas.user import (
    AuthExchangeRequest, AuthExchangeResponse, AyahProgressRequest, AyahProgressResponse,
    AyahRef, ContinueReading, DueFlashcardBrief, DueFlashcardOut,
    FlashcardReviewRequest, FlashcardReviewResponse, HomeResponse,
    LessonProgressRequest, LessonProgressResponse, NextLesson,
    OnboardingRequest, OnboardingResponse, RecentBadge,
    RecitationSessionOut, RecitationWordResultOut,
    ScholarQuestionCreate, ScholarQuestionOut, UserOut,
)
