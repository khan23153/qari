"""User Data models — progress, SRS, recitation, gamification."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, SmallInteger, Text, JSON, Integer, Float, Boolean,
    ForeignKey, Date, DateTime, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_provider_id = Column(Text, unique=True, nullable=False)
    display_name = Column(Text)
    app_language = Column(Text, nullable=False, default="hi_latn")
    starting_path = Column(Text)
    font_scale = Column(Float, default=1.0)
    theme = Column(Text, default="system")
    preferred_qari = Column(SmallInteger, ForeignKey("qaris.qari_id"))
    audio_training_consent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    stats = relationship("UserStats", back_populates="user", uselist=False)
    lesson_progress = relationship("UserLessonProgress", back_populates="user")
    flashcards = relationship("Flashcard", back_populates="user")


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.lesson_id"), primary_key=True)
    status = Column(Text, nullable=False, default="not_started")
    best_score = Column(SmallInteger)
    attempts = Column(SmallInteger, default=0)
    completed_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="lesson_progress")


class UserAyahProgress(Base):
    __tablename__ = "user_ayah_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    surah_number = Column(SmallInteger, primary_key=True)
    ayah_number = Column(SmallInteger, primary_key=True)
    studied_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Flashcard(Base):
    __tablename__ = "flashcards"

    card_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    surah_number = Column(SmallInteger)
    ayah_number = Column(SmallInteger)
    word_position = Column(SmallInteger)
    source = Column(Text, nullable=False)
    ease_factor = Column(Float, nullable=False, default=2.5)
    interval_days = Column(Float, nullable=False, default=0)
    repetitions = Column(Integer, nullable=False, default=0)
    due_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    suspended = Column(Boolean, default=False)

    user = relationship("User", back_populates="flashcards")
    reviews = relationship("FlashcardReview", back_populates="card")

    __table_args__ = (
        UniqueConstraint("user_id", "surah_number", "ayah_number", "word_position"),
        Index("idx_flashcards_due", "user_id", "due_at"),
    )


class FlashcardReview(Base):
    __tablename__ = "flashcard_reviews"

    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID(as_uuid=True), ForeignKey("flashcards.card_id"))
    grade = Column(SmallInteger, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    card = relationship("Flashcard", back_populates="reviews")


class UserStats(Base):
    __tablename__ = "user_stats"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    xp_total = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_active_date = Column(Date)
    timezone = Column(Text, default="Asia/Kolkata")

    user = relationship("User", back_populates="stats")


class UserBadge(Base):
    __tablename__ = "user_badges"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    badge_id = Column(Text, ForeignKey("badges.badge_id"), primary_key=True)
    earned_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class RecitationSession(Base):
    __tablename__ = "recitation_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    surah_number = Column(SmallInteger)
    ayah_start = Column(SmallInteger)
    ayah_end = Column(SmallInteger)
    audio_url = Column(Text)
    overall_score = Column(SmallInteger)
    fluency_score = Column(SmallInteger)
    tajweed_score = Column(SmallInteger)
    model_version = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    word_results = relationship("RecitationWordResult", back_populates="session")


class RecitationWordResult(Base):
    __tablename__ = "recitation_word_results"

    session_id = Column(UUID(as_uuid=True), ForeignKey("recitation_sessions.session_id"), primary_key=True)
    surah_number = Column(SmallInteger, primary_key=True)
    ayah_number = Column(SmallInteger, primary_key=True)
    word_position = Column(SmallInteger, primary_key=True)
    verdict = Column(Text, nullable=False)
    error_detail = Column(JSON)
    start_ms = Column(Integer)
    end_ms = Column(Integer)

    session = relationship("RecitationSession", back_populates="word_results")


class ScholarQuestion(Base):
    __tablename__ = "scholar_questions"

    question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    audio_url = Column(Text)
    text_body = Column(Text)
    status = Column(Text, nullable=False, default="queued")
    scholar_id = Column(UUID(as_uuid=True))
    answer_audio_url = Column(Text)
    answer_text = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    answered_at = Column(DateTime(timezone=True))
