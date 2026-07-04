"""Pydantic schemas for user data, progress, flashcards, gamification."""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class OnboardingRequest(BaseModel):
    app_language: str = Field(..., pattern="^(en|ur|hi_latn)$")
    starting_path: str = Field(..., pattern="^(foundation|quran_direct)$")
    firebase_uid: str
    display_name: Optional[str] = None


class UserSchema(BaseModel):
    user_id: UUID
    app_language: str
    starting_path: Optional[str] = None
    font_scale: float = 1.0
    theme: str = "system"
    display_name: Optional[str] = None

    class Config:
        from_attributes = True


class HomeResponse(BaseModel):
    streak: int
    xp_total: int
    next_lesson: Optional[dict] = None
    due_flashcard_count: int
    continue_reading: Optional[dict] = None
    daily_goal_progress: float = 0.0


class LessonProgressRequest(BaseModel):
    status: str = Field(..., pattern="^(in_progress|completed)$")
    score: Optional[int] = Field(None, ge=0, le=100)
    idempotency_key: str


class LessonProgressResponse(BaseModel):
    xp_awarded: int
    new_badges: list[str] = []
    streak_state: dict


class AyahProgressRequest(BaseModel):
    surah_number: int
    ayah_numbers: list[int]
    idempotency_key: str


class FlashcardSchema(BaseModel):
    card_id: UUID
    surah_number: int
    ayah_number: int
    word_position: int
    text_uthmani: str
    transliteration: str
    translation: dict
    audio_url: Optional[str] = None

    class Config:
        from_attributes = True


class FlashcardReviewRequest(BaseModel):
    grade: int = Field(..., ge=0, le=5)


class FlashcardReviewResponse(BaseModel):
    next_due: datetime
    ease_factor: float
    interval_days: float
    repetitions: int


class RecitationResultWord(BaseModel):
    key: str  # "surah:ayah:word_position"
    verdict: str
    error_detail: Optional[dict] = None
    user_clip: Optional[dict] = None
    reference_audio_url: Optional[str] = None


class RecitationResultResponse(BaseModel):
    session_id: UUID
    overall_score: Optional[int] = None
    fluency_score: Optional[int] = None
    tajweed_score: Optional[int] = None
    words: list[RecitationResultWord] = []
    model_version: str


class ScholarQuestionRequest(BaseModel):
    text_body: Optional[str] = None
    topic: Optional[str] = None


class ScholarQuestionResponse(BaseModel):
    question_id: UUID
    status: str
    text_body: Optional[str] = None
    answer_text: Optional[str] = None
    answer_audio_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
