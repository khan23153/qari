"""Learning content models: Lesson, QuizQuestion, Badge."""

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, Integer, JSON, Numeric, SmallInteger, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Badge(Base):
    """An achievement badge that users can earn."""

    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ur: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    name_hi_latn: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_hi_latn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="bronze")
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    criteria_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=__import__("sqlalchemy").func.now(),
    )

    # Relationships
    user_badges: Mapped[list["UserBadge"]] = relationship(back_populates="badge", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("tier IN ('bronze','silver','gold','platinum')", name="ck_badges_tier"),
        CheckConstraint("xp_reward >= 0", name="ck_badges_xp_reward_nonneg"),
        UniqueConstraint("slug", name="uq_badges_slug"),
    )


class Lesson(Base):
    """A structured learning lesson within a module."""

    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    title_en: Mapped[str] = mapped_column(String(300), nullable=False)
    title_ur: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    title_hi_latn: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    summary_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_hi_latn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_en: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    content_ur: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    content_hi_latn: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    lesson_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    surah_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ayah_range: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    published_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=__import__("sqlalchemy").func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=__import__("sqlalchemy").func.now(),
        onupdate=__import__("sqlalchemy").func.now(),
    )

    # Relationships
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan",
        order_by="QuizQuestion.order_index",
    )
    user_progress: Mapped[list["UserLessonProgress"]] = relationship(back_populates="lesson")

    __table_args__ = (
        CheckConstraint(
            "review_status IN ('draft','in_review','published','archived')",
            name="ck_lessons_review_status",
        ),
        CheckConstraint(
            "estimated_minutes IS NULL OR estimated_minutes > 0",
            name="ck_lessons_estimated_minutes_positive",
        ),
        CheckConstraint("xp_reward >= 0", name="ck_lessons_xp_reward_nonneg"),
        UniqueConstraint("slug", name="uq_lessons_slug"),
    )


class QuizQuestion(Base):
    """A quiz question attached to a lesson."""

    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    question_en: Mapped[str] = mapped_column(Text, nullable=False)
    question_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    question_hi_latn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False, default="multiple_choice")
    options_en: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    options_ur: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    options_hi_latn: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_hi_latn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=__import__("sqlalchemy").func.now(),
    )

    # Relationships
    lesson: Mapped["Lesson"] = relationship(back_populates="quiz_questions")

    __table_args__ = (
        CheckConstraint(
            "question_type IN ('multiple_choice','true_false','fill_blank','match')",
            name="ck_quiz_questions_question_type",
        ),
        CheckConstraint("points > 0", name="ck_quiz_questions_points_positive"),
    )
