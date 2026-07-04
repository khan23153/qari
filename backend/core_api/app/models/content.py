"""Learning Content models (authored, versioned)."""
import uuid
from sqlalchemy import (
    Column, String, SmallInteger, Text, JSON, Integer, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Lesson(Base):
    __tablename__ = "lessons"

    lesson_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module = Column(SmallInteger, nullable=False)
    unit_number = Column(SmallInteger, nullable=False)
    sequence = Column(SmallInteger, nullable=False)
    lesson_type = Column(Text, nullable=False)
    title = Column(JSON, nullable=False)
    content = Column(JSON, nullable=False)
    xp_reward = Column(SmallInteger, nullable=False, default=10)
    min_pass_pct = Column(SmallInteger, default=70)
    review_status = Column(Text, nullable=False, default="draft")
    version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("module", "unit_number", "sequence"),
    )

    quiz_questions = relationship("QuizQuestion", back_populates="lesson")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.lesson_id"))
    q_type = Column(Text, nullable=False)
    prompt = Column(JSON, nullable=False)
    payload = Column(JSON, nullable=False)
    difficulty = Column(SmallInteger, default=1)

    lesson = relationship("Lesson", back_populates="quiz_questions")


class Badge(Base):
    __tablename__ = "badges"

    badge_id = Column(Text, primary_key=True)
    title = Column(JSON, nullable=False)
    description = Column(JSON, nullable=False)
    icon_url = Column(Text, nullable=False)
    criteria = Column(JSON, nullable=False)
