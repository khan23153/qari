"""User, progress, flashcard, recitation, and scholar Pydantic schemas."""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from shared import AppLanguage, StartingPath


# --- Auth / Onboarding ---

class OnboardingRequest(BaseModel):
    """The ONLY onboarding write payload."""
    app_language: AppLanguage = AppLanguage.en
    starting_path: StartingPath = StartingPath.beginner
    display_name: Optional[str] = None
    timezone: Optional[str] = "Asia/Calcutta"


class OnboardingResponse(BaseModel):
    user_id: uuid.UUID
    is_onboarded: bool
    app_language: AppLanguage
    starting_path: StartingPath


class AuthExchangeRequest(BaseModel):
    firebase_token: str


class AuthExchangeResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: uuid.UUID
    is_onboarded: bool


# --- Home aggregation ---

class HomeResponse(BaseModel):
    """Aggregated home screen data."""
    streak: int
    longest_streak: int
    freeze_credits: int
    total_xp: int
    next_lesson: Optional["NextLesson"] = None
    due_flashcards_count: int
    due_flashcards: list["DueFlashcardBrief"] = []
    continue_reading: Optional["ContinueReading"] = None
    recent_badges: list["RecentBadge"] = []


class NextLesson(BaseModel):
    id: int
    title: str
    module: str
    estimated_minutes: Optional[int] = None
    model_config = {"from_attributes": True}


class DueFlashcardBrief(BaseModel):
    id: int
    text_arabic: str
    translation: Optional[str] = None
    surah_number: int
    ayah_number: int
    model_config = {"from_attributes": True}


class ContinueReading(BaseModel):
    surah_number: int
    surah_name: str
    next_ayah: int
    model_config = {"from_attributes": True}


class RecentBadge(BaseModel):
    id: int
    name: str
    icon_url: Optional[str] = None
    tier: str
    awarded_at: datetime
    model_config = {"from_attributes": True}


# --- Progress ---

class LessonProgressRequest(BaseModel):
    status: str = Field(..., pattern="^(not_started|in_progress|completed)$")
    score: Optional[float] = Field(None, ge=0, le=100)
    idempotency_key: str = Field(..., min_length=1, max_length=100)


class LessonProgressResponse(BaseModel):
    lesson_id: int
    status: str
    xp_earned: int
    total_xp: int
    new_badges: list["BadgeAwarded"] = []
    streak: int
    streak_updated: bool


class BadgeAwarded(BaseModel):
    id: int
    slug: str
    name: str
    tier: str
    xp_reward: int


class AyahProgressRequest(BaseModel):
    """Batch mark ayahs as studied."""
    ayahs: list["AyahRef"] = Field(..., min_length=1, max_length=50)
    idempotency_key: str = Field(..., min_length=1, max_length=100)


class AyahRef(BaseModel):
    surah_number: int = Field(..., ge=1, le=114)
    ayah_number: int = Field(..., ge=1)


class AyahProgressResponse(BaseModel):
    marked: int
    total_requested: int
    streak: int
    streak_updated: bool


# --- Flashcards ---

class DueFlashcardOut(BaseModel):
    """A due flashcard with embedded word data."""
    id: int
    word_id: int
    surah_number: int
    ayah_number: int
    word_position: int
    text_arabic: str
    text_transliteration: Optional[str] = None
    translation: Optional[str] = None
    pos_group: Optional[str] = None
    root_text: Optional[str] = None
    audio_url: Optional[str] = None
    due_at: datetime
    sm2_repetitions: int
    model_config = {"from_attributes": True}


class FlashcardReviewRequest(BaseModel):
    grade: int = Field(..., ge=0, le=5)


class FlashcardReviewResponse(BaseModel):
    flashcard_id: int
    new_easiness: float
    new_interval: int
    new_repetitions: int
    next_due_at: datetime
    is_suspended: bool


# --- Recitation ---

class RecitationWordResultOut(BaseModel):
    id: int
    surah_number: int
    ayah_number: int
    word_position: int
    expected_text: str
    detected_text: Optional[str] = None
    verdict: str
    confidence: Optional[float] = None
    error_detail: Optional[str] = None
    audio_start_sec: Optional[float] = None
    audio_end_sec: Optional[float] = None
    model_config = {"from_attributes": True}


class RecitationSessionOut(BaseModel):
    id: uuid.UUID
    surah_number: int
    ayah_from: int
    ayah_to: int
    status: str
    audio_duration_sec: Optional[float] = None
    total_words: Optional[int] = None
    correct_words: Optional[int] = None
    accuracy_pct: Optional[float] = None
    error_message: Optional[str] = None
    queued_at: datetime
    completed_at: Optional[datetime] = None
    word_results: list[RecitationWordResultOut] = []
    model_config = {"from_attributes": True}


# --- Scholar Q&A ---

class ScholarQuestionOut(BaseModel):
    id: int
    question_text: Optional[str] = None
    audio_url: Optional[str] = None
    surah_ref: Optional[str] = None
    ayah_ref: Optional[str] = None
    status: str
    answer_text: Optional[str] = None
    scholar_name: Optional[str] = None
    answered_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ScholarQuestionCreate(BaseModel):
    question_text: Optional[str] = None
    surah_ref: Optional[str] = None
    ayah_ref: Optional[str] = None


# --- User profile ---

class UserOut(BaseModel):
    id: uuid.UUID
    email: Optional[str] = None
    display_name: Optional[str] = None
    app_language: str
    starting_path: Optional[str] = None
    is_onboarded: bool
    total_xp: int
    current_streak: int
    longest_streak: int
    freeze_credits: int
    created_at: datetime
    model_config = {"from_attributes": True}


# Resolve forward refs
HomeResponse.model_rebuild()
LessonProgressResponse.model_rebuild()
AyahProgressRequest.model_rebuild()
