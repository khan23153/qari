"""Corpus Pydantic response models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Qari ---

class QariBrief(BaseModel):
    id: int
    name: str
    arabic_name: Optional[str] = None
    style: Optional[str] = None
    audio_base_url: Optional[str] = None
    model_config = {"from_attributes": True}


# --- Surah ---

class SurahBrief(BaseModel):
    """Surah metadata for list views."""
    surah_number: int
    name_arabic: str
    name_transliteration: str
    name_translation: Optional[str] = None
    revelation_place: str
    revelation_order: int
    ayah_count: int
    model_config = {"from_attributes": True}


class SurahDetail(BaseModel):
    """Full surah metadata with context story."""
    surah_number: int
    name_arabic: str
    name_transliteration: str
    name_translation: Optional[str] = None
    revelation_place: str
    revelation_order: int
    ayah_count: int
    page_start: Optional[int] = None
    juz_list: Optional[list] = None
    context_story: Optional[str] = None
    model_config = {"from_attributes": True}


# --- Word ---

class TajweedAnnotationOut(BaseModel):
    id: int
    rule_category: str
    rule_name: str
    rule_name_arabic: Optional[str] = None
    description: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    model_config = {"from_attributes": True}


class WordBrief(BaseModel):
    """Embedded word in ayah responses."""
    id: int
    word_position: int
    text_arabic: str
    text_transliteration: Optional[str] = None
    translation: Optional[str] = None
    pos_group: Optional[str] = None
    audio_url: Optional[str] = None
    model_config = {"from_attributes": True}


class WordDetail(BaseModel):
    """Full word detail with morphology, root, and other occurrences."""
    id: int
    surah_number: int
    ayah_number: int
    word_position: int
    text_arabic: str
    text_transliteration: Optional[str] = None
    translation: Optional[str] = None
    pos_group: Optional[str] = None
    pos_detail: Optional[str] = None
    morphology_features: Optional[dict] = None
    audio_url: Optional[str] = None
    root: Optional["RootBrief"] = None
    tajweed_annotations: list[TajweedAnnotationOut] = []
    other_occurrences: list["WordOccurrence"] = []
    model_config = {"from_attributes": True}


class WordOccurrence(BaseModel):
    """A location where the same root appears."""
    surah_number: int
    ayah_number: int
    word_position: int
    text_arabic: str
    model_config = {"from_attributes": True}


# --- Root ---

class RootBrief(BaseModel):
    id: int
    root_arabic: str
    root_transliteration: str
    meaning: Optional[str] = None
    model_config = {"from_attributes": True}


class RootDetail(BaseModel):
    """Full root detail with meaning and occurrence list."""
    id: int
    root_arabic: str
    root_transliteration: str
    meaning: Optional[str] = None
    occurrence_count: int
    occurrences: list[WordOccurrence] = []
    model_config = {"from_attributes": True}


# --- Ayah ---

class AyahOut(BaseModel):
    """An ayah with embedded word array."""
    id: int
    surah_number: int
    ayah_number: int
    text_arabic: str
    text_translation: Optional[str] = None
    text_transliteration: Optional[str] = None
    juz: Optional[int] = None
    page: Optional[int] = None
    sajda: bool = False
    audio_url: Optional[str] = None
    words: list[WordBrief] = []
    model_config = {"from_attributes": True}


# Resolve forward refs
WordDetail.model_rebuild()
RootDetail.model_rebuild()
