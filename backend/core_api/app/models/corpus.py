"""Corpus mirror models (read-only, populated by ETL pipeline).

Tables: Surah, Ayah, Word, Root, TajweedAnnotation, Qari
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, Numeric, SmallInteger, String, Text, TIMESTAMP, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Qari(Base):
    """A Quran reciter (qari) whose audio recitations are available."""

    __tablename__ = "qaris"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    arabic_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    audio_base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=__import__("sqlalchemy").func.now())

    # Relationships
    ayahs: Mapped[list["Ayah"]] = relationship(back_populates="qari")
    recitation_sessions: Mapped[list["RecitationSession"]] = relationship(back_populates="qari")

    __table_args__ = (
        UniqueConstraint("name", name="uq_qaris_name"),
    )


class Surah(Base):
    """A surah (chapter) of the Quran — 114 total."""

    __tablename__ = "surahs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    name_arabic: Mapped[str] = mapped_column(String(100), nullable=False)
    name_transliteration: Mapped[str] = mapped_column(String(200), nullable=False)
    name_translation_en: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    name_translation_ur: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    name_translation_hi_latn: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    revelation_place: Mapped[str] = mapped_column(String(20), nullable=False)
    revelation_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ayah_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    page_start: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    juz_list: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    context_story_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_story_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_story_hi_latn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=__import__("sqlalchemy").func.now())

    # Relationships
    ayahs: Mapped[list["Ayah"]] = relationship(back_populates="surah", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_surahs_surah_number_range"),
        CheckConstraint("revelation_place IN ('meccan','medinan')", name="ck_surahs_revelation_place"),
        CheckConstraint("ayah_count > 0", name="ck_surahs_ayah_count_positive"),
        UniqueConstraint("surah_number", name="uq_surahs_surah_number"),
    )


class Root(Base):
    """An Arabic root word from which Quranic words derive."""

    __tablename__ = "roots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    root_arabic: Mapped[str] = mapped_column(String(50), nullable=False)
    root_transliteration: Mapped[str] = mapped_column(String(100), nullable=False)
    meaning_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meaning_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meaning_hi_latn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=__import__("sqlalchemy").func.now())

    # Relationships
    words: Mapped[list["Word"]] = relationship(back_populates="root")

    __table_args__ = (
        UniqueConstraint("root_arabic", name="uq_roots_root_arabic"),
    )


class Ayah(Base):
    """A single ayah (verse) within a surah."""

    __tablename__ = "ayahs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    surah_id: Mapped[int] = mapped_column(Integer, ForeignKey("surahs.id", ondelete="CASCADE"), nullable=False)
    surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    text_arabic: Mapped[str] = mapped_column(Text, nullable=False)
    text_translation_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text_translation_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text_translation_hi_latn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text_transliteration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    juz: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    page: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    ruku: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    hizb_quarter: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    sajda: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_url_ur: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    qari_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("qaris.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=__import__("sqlalchemy").func.now())

    # Relationships
    surah: Mapped["Surah"] = relationship(back_populates="ayahs")
    qari: Mapped[Optional["Qari"]] = relationship(back_populates="ayahs")
    words: Mapped[list["Word"]] = relationship(back_populates="ayah", cascade="all, delete-orphan", order_by="Word.word_position")
    tajweed_annotations: Mapped[list["TajweedAnnotation"]] = relationship(back_populates="ayah", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_ayahs_surah_number_range"),
        CheckConstraint("ayah_number >= 1", name="ck_ayahs_ayah_number_positive"),
        CheckConstraint("juz IS NULL OR (juz BETWEEN 1 AND 30)", name="ck_ayahs_juz_range"),
        CheckConstraint("page IS NULL OR (page BETWEEN 1 AND 604)", name="ck_ayahs_page_range"),
        UniqueConstraint("surah_number", "ayah_number", name="uq_ayahs_surah_ayah"),
    )


class Word(Base):
    """A single word within an ayah, with morphology and root linkage."""

    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ayah_id: Mapped[int] = mapped_column(Integer, ForeignKey("ayahs.id", ondelete="CASCADE"), nullable=False)
    surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    word_position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    text_arabic: Mapped[str] = mapped_column(String(200), nullable=False)
    text_transliteration: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    translation_en: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    translation_ur: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    translation_hi_latn: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    root_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roots.id", ondelete="SET NULL"), nullable=True)
    pos_group: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    pos_detail: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    morphology_features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=__import__("sqlalchemy").func.now())

    # Relationships
    ayah: Mapped["Ayah"] = relationship(back_populates="words")
    root: Mapped[Optional["Root"]] = relationship(back_populates="words")
    tajweed_annotations: Mapped[list["TajweedAnnotation"]] = relationship(back_populates="word", cascade="all, delete-orphan")
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="word")

    __table_args__ = (
        CheckConstraint("word_position >= 1", name="ck_words_word_position_positive"),
        CheckConstraint(
            "pos_group IS NULL OR pos_group IN ('ism','fil','harf')",
            name="ck_words_pos_group",
        ),
        UniqueConstraint("surah_number", "ayah_number", "word_position", name="uq_words_surah_ayah_pos"),
    )


class TajweedAnnotation(Base):
    """A tajweed rule annotation on a specific word."""

    __tablename__ = "tajweed_annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    ayah_id: Mapped[int] = mapped_column(Integer, ForeignKey("ayahs.id", ondelete="CASCADE"), nullable=False)
    rule_category: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_name_arabic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_hi_latn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    char_start: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    char_end: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=__import__("sqlalchemy").func.now())

    # Relationships
    word: Mapped["Word"] = relationship(back_populates="tajweed_annotations")
    ayah: Mapped["Ayah"] = relationship(back_populates="tajweed_annotations")

    __table_args__ = (
        CheckConstraint("char_start IS NULL OR char_start >= 0", name="ck_tajweed_char_start_nonneg"),
        CheckConstraint("char_end IS NULL OR char_end >= 0", name="ck_tajweed_char_end_nonneg"),
    )
