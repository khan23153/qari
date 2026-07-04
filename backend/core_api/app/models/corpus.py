"""Quran Corpus Mirror models (read-only at runtime, seeded by ETL)."""
from sqlalchemy import (
    Column, SmallInteger, Text, JSON, ForeignKey, Integer, Boolean,
    Index, ForeignKeyConstraint,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Surah(Base):
    __tablename__ = "surahs"

    surah_number = Column(SmallInteger, primary_key=True)
    name_arabic = Column(Text, nullable=False)
    name_translit = Column(Text, nullable=False)
    name_translated = Column(JSON, nullable=False)
    revelation_place = Column(Text, nullable=False)
    ayah_count = Column(SmallInteger, nullable=False)
    context_story = Column(JSON)

    ayahs = relationship("Ayah", back_populates="surah")


class Ayah(Base):
    __tablename__ = "ayahs"

    surah_number = Column(
        SmallInteger, ForeignKey("surahs.surah_number"), primary_key=True
    )
    ayah_number = Column(SmallInteger, primary_key=True)
    text_uthmani = Column(Text, nullable=False)
    text_imlaei = Column(Text, nullable=False)
    page_number = Column(SmallInteger)
    juz_number = Column(SmallInteger)
    audio_segments = Column(JSON)

    surah = relationship("Surah", back_populates="ayahs")
    words = relationship("Word", back_populates="ayah", cascade="all, delete-orphan")


class Root(Base):
    __tablename__ = "roots"

    root_id = Column(Integer, primary_key=True)
    root_arabic = Column(Text, nullable=False, unique=True)
    root_translit = Column(Text, nullable=False)
    core_meaning = Column(JSON, nullable=False)
    occurrence_count = Column(Integer, nullable=False)


class Word(Base):
    __tablename__ = "words"

    surah_number = Column(SmallInteger, primary_key=True)
    ayah_number = Column(SmallInteger, primary_key=True)
    word_position = Column(SmallInteger, primary_key=True)
    text_uthmani = Column(Text, nullable=False)
    transliteration = Column(Text, nullable=False)
    translation = Column(JSON, nullable=False)
    root_id = Column(Integer, ForeignKey("roots.root_id"))
    lemma = Column(Text)
    pos_tag = Column(Text, nullable=False)
    pos_group = Column(Text, nullable=False)
    morphology = Column(JSON, nullable=False)
    audio_url = Column(Text)

    ayah = relationship("Ayah", back_populates="words")
    root = relationship("Root")

    __table_args__ = (
        Index("idx_words_root", "root_id"),
        Index("idx_words_pos", "pos_group"),
        ForeignKeyConstraint(
            ["surah_number", "ayah_number"],
            ["ayahs.surah_number", "ayahs.ayah_number"],
        ),
    )


class TajweedAnnotation(Base):
    __tablename__ = "tajweed_annotations"

    surah_number = Column(SmallInteger, primary_key=True)
    ayah_number = Column(SmallInteger, primary_key=True)
    word_position = Column(SmallInteger, primary_key=True)
    char_start = Column(SmallInteger, primary_key=True)
    rule = Column(Text, primary_key=True)
    char_end = Column(SmallInteger, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["surah_number", "ayah_number", "word_position"],
            ["words.surah_number", "words.ayah_number", "words.word_position"],
        ),
    )


class Qari(Base):
    __tablename__ = "qaris"

    qari_id = Column(SmallInteger, primary_key=True)
    name = Column(Text, nullable=False)
    style = Column(Text)
    base_audio_url = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
