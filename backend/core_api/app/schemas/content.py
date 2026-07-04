"""Lesson and quiz Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class QuizQuestionOut(BaseModel):
    """A quiz question (correct_answer omitted for published API)."""
    id: int
    question: str
    question_type: str
    options: Optional[list] = None
    explanation: Optional[str] = None
    points: int = 1
    order_index: int = 0
    model_config = {"from_attributes": True}


class LessonBrief(BaseModel):
    """Lesson metadata for list/manifest views."""
    id: int
    slug: str
    module: str
    title: str
    summary: Optional[str] = None
    lesson_order: int
    estimated_minutes: Optional[int] = None
    xp_reward: int
    surah_ref: Optional[str] = None
    ayah_range: Optional[str] = None
    tags: Optional[list] = None
    model_config = {"from_attributes": True}


class LessonDetail(BaseModel):
    """Full lesson payload with quiz questions."""
    id: int
    slug: str
    module: str
    title: str
    summary: Optional[str] = None
    content: Optional[dict] = None
    lesson_order: int
    estimated_minutes: Optional[int] = None
    xp_reward: int
    surah_ref: Optional[str] = None
    ayah_range: Optional[str] = None
    tags: Optional[list] = None
    quiz_questions: list[QuizQuestionOut] = []
    model_config = {"from_attributes": True}


class BadgeOut(BaseModel):
    """A badge definition."""
    id: int
    slug: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    tier: str
    xp_reward: int
    model_config = {"from_attributes": True}


class UserBadgeOut(BaseModel):
    """A badge awarded to a user."""
    id: int
    badge: BadgeOut
    awarded_at: datetime
    model_config = {"from_attributes": True}
