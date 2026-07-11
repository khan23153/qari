"""User data models: 10 tables for users, progress, flashcards, recitation, scholar Q&A."""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, JSON, Numeric, SmallInteger, String, Text, TIMESTAMP, UUID, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    """A registered app user."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    firebase_uid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    app_language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    starting_path: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    freeze_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_streak_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_freeze_grant_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    lesson_progress: Mapped[list["UserLessonProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    ayah_progress: Mapped[list["UserAyahProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    flashcard_reviews: Mapped[list["FlashcardReview"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    stats: Mapped[Optional["UserStats"]] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    badges: Mapped[list["UserBadge"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    recitation_sessions: Mapped[list["RecitationSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    scholar_questions: Mapped[list["ScholarQuestion"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("app_language IN ('en','ur','hi_latn','ar')", name="ck_users_app_language"),
        CheckConstraint(
            "starting_path IS NULL OR starting_path IN "
            "('beginner','intermediate','advanced','tajweed_focus','memorization','foundation','quran_direct')",
            name="ck_users_starting_path",
        ),
        CheckConstraint("total_xp >= 0", name="ck_users_total_xp_nonneg"),
        CheckConstraint("current_streak >= 0", name="ck_users_current_streak_nonneg"),
        CheckConstraint("longest_streak >= 0", name="ck_users_longest_streak_nonneg"),
        CheckConstraint("freeze_credits >= 0", name="ck_users_freeze_credits_nonneg"),
        UniqueConstraint("firebase_uid", name="uq_users_firebase_uid"),
    )

    # --- Password helpers (email/password auth) ---

    def set_password(self, plain: str) -> None:
        """Hash *plain* and store it on ``password_hash``."""
        from app.core.security import hash_password

        self.password_hash = hash_password(plain)

    def verify_password(self, plain: str) -> bool:
        """Return ``True`` if *plain* matches the stored password hash."""
        from app.core.security import verify_password as _verify

        if not self.password_hash:
            return False
        return _verify(plain, self.password_hash)


class UserLessonProgress(Base):
    """Per-user progress on a specific lesson."""

    __tablename__ = "user_lesson_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="lesson_progress")
    lesson: Mapped["Lesson"] = relationship(back_populates="user_progress")

    __table_args__ = (
        CheckConstraint("status IN ('not_started','in_progress','completed')", name="ck_user_lesson_progress_status"),
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="ck_user_lesson_progress_score_range"),
        CheckConstraint("xp_earned >= 0", name="ck_user_lesson_progress_xp_nonneg"),
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress_user_lesson"),
    )


class UserAyahProgress(Base):
    """Per-user study tracking for individual ayahs."""

    __tablename__ = "user_ayah_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    times_studied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_studied_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="ayah_progress")

    __table_args__ = (
        CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_user_ayah_progress_surah_range"),
        CheckConstraint("ayah_number >= 1", name="ck_user_ayah_progress_ayah_positive"),
        CheckConstraint("times_studied >= 0", name="ck_user_ayah_progress_times_studied_nonneg"),
        UniqueConstraint("user_id", "surah_number", "ayah_number", name="uq_uap_user_surah_ayah"),
    )


class Flashcard(Base):
    """An SRS flashcard for a user, linked to a specific Quranic word."""

    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    word_position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    sm2_easiness: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=2.50)
    sm2_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sm2_repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="flashcards")
    word: Mapped["Word"] = relationship(back_populates="flashcards")
    reviews: Mapped[list["FlashcardReview"]] = relationship(back_populates="flashcard", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("source IN ('manual','quiz_miss','recitation_miss')", name="ck_flashcards_source"),
        CheckConstraint("sm2_easiness >= 1.30 AND sm2_easiness <= 2.50", name="ck_flashcards_sm2_easiness_range"),
        CheckConstraint("sm2_interval >= 0", name="ck_flashcards_sm2_interval_nonneg"),
        CheckConstraint("sm2_repetitions >= 0", name="ck_flashcards_sm2_repetitions_nonneg"),
        UniqueConstraint("user_id", "word_id", name="uq_flashcards_user_word"),
    )


class FlashcardReview(Base):
    """A single review event for a flashcard (SM-2 audit trail)."""

    __tablename__ = "flashcard_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flashcard_id: Mapped[int] = mapped_column(Integer, ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    prev_easiness: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    new_easiness: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    prev_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    new_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    flashcard: Mapped["Flashcard"] = relationship(back_populates="reviews")
    user: Mapped["User"] = relationship(back_populates="flashcard_reviews")

    __table_args__ = (
        CheckConstraint("grade BETWEEN 0 AND 5", name="ck_flashcard_reviews_grade_range"),
    )


class UserStats(Base):
    """Aggregate statistics for a user (one row per user)."""

    __tablename__ = "user_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    lessons_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ayahs_studied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    flashcards_reviewed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recitation_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_recitation_duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_recitation_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    questions_asked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="stats")

    __table_args__ = (
        CheckConstraint("lessons_completed >= 0", name="ck_user_stats_lessons_completed_nonneg"),
        CheckConstraint("ayahs_studied >= 0", name="ck_user_stats_ayahs_studied_nonneg"),
        CheckConstraint("flashcards_reviewed >= 0", name="ck_user_stats_flashcards_reviewed_nonneg"),
        CheckConstraint("recitation_sessions >= 0", name="ck_user_stats_recitation_sessions_nonneg"),
        CheckConstraint("total_recitation_duration_sec >= 0", name="ck_user_stats_recitation_duration_nonneg"),
        CheckConstraint(
            "avg_recitation_accuracy IS NULL OR (avg_recitation_accuracy >= 0 AND avg_recitation_accuracy <= 100)",
            name="ck_user_stats_avg_accuracy_range",
        ),
    )


class UserBadge(Base):
    """A badge awarded to a user."""

    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id: Mapped[int] = mapped_column(Integer, ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="badges")
    badge: Mapped["Badge"] = relationship(back_populates="user_badges")

    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badges_user_badge"),
    )


class RecitationSession(Base):
    """A recitation recording session submitted for AI evaluation."""

    __tablename__ = "recitation_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ayah_from: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ayah_to: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    qari_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("qaris.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_duration_sec: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    total_words: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    correct_words: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    accuracy_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    queued_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="recitation_sessions")
    qari: Mapped[Optional["Qari"]] = relationship(back_populates="recitation_sessions")
    word_results: Mapped[list["RecitationWordResult"]] = relationship(back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_recitation_sessions_surah_range"),
        CheckConstraint("ayah_from >= 1", name="ck_recitation_sessions_ayah_from_positive"),
        CheckConstraint("ayah_to >= ayah_from", name="ck_recitation_sessions_ayah_to_gte_from"),
        CheckConstraint("status IN ('queued','processing','completed','failed')", name="ck_recitation_sessions_status"),
        CheckConstraint(
            "accuracy_pct IS NULL OR (accuracy_pct >= 0 AND accuracy_pct <= 100)",
            name="ck_recitation_sessions_accuracy_range",
        ),
    )


class RecitationWordResult(Base):
    """Per-word verdict from the ML recitation engine."""

    __tablename__ = "recitation_word_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recitation_sessions.id", ondelete="CASCADE"), nullable=False)
    surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    word_position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    expected_text: Mapped[str] = mapped_column(String(200), nullable=False)
    detected_text: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    error_detail_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_detail_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_detail_hi_latn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_start_sec: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)
    audio_end_sec: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    session: Mapped["RecitationSession"] = relationship(back_populates="word_results")

    __table_args__ = (
        CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_recitation_word_results_surah_range"),
        CheckConstraint("ayah_number >= 1", name="ck_recitation_word_results_ayah_positive"),
        CheckConstraint("word_position >= 1", name="ck_recitation_word_results_word_position_positive"),
        CheckConstraint(
            "verdict IN ('correct','mispronounced','skipped','extra','unclear')",
            name="ck_recitation_word_results_verdict",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_recitation_word_results_confidence_range",
        ),
    )


class ScholarQuestion(Base):
    """A question submitted by a user to a scholar, optionally with audio."""

    __tablename__ = "scholar_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_duration_sec: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    surah_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ayah_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    answer_audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    scholar_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    answered_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="scholar_questions")

    __table_args__ = (
        CheckConstraint("status IN ('pending','answered','rejected')", name="ck_scholar_questions_status"),
        CheckConstraint(
            "question_text IS NOT NULL OR audio_url IS NOT NULL",
            name="ck_scholar_questions_has_content",
        ),
    )
