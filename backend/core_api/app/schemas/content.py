"""Pydantic schemas for learning content."""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class LessonSummary(BaseModel):
    lesson_id: UUID
    module: int
    unit_number: int
    sequence: int
    lesson_type: str
    title: dict
    xp_reward: int
    min_pass_pct: Optional[int] = 70

    class Config:
        from_attributes = True


class QuizQuestionSchema(BaseModel):
    question_id: UUID
    q_type: str
    prompt: dict
    payload: dict
    difficulty: int = 1

    class Config:
        from_attributes = True


class LessonDetail(LessonSummary):
    content: dict
    quiz_questions: list[QuizQuestionSchema] = []


class BadgeSchema(BaseModel):
    badge_id: str
    title: dict
    description: dict
    icon_url: str
