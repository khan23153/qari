"""Pydantic schemas for Quran corpus responses."""
from pydantic import BaseModel, Field
from typing import Optional


class SurahSummary(BaseModel):
    surah_number: int
    name_arabic: str
    name_translit: str
    name_translated: dict
    revelation_place: str
    ayah_count: int
    has_context_story: bool = False

    class Config:
        from_attributes = True


class SurahDetail(SurahSummary):
    context_story: Optional[dict] = None


class WordSchema(BaseModel):
    word_position: int
    text_uthmani: str
    transliteration: str
    translation: dict
    pos_tag: str
    pos_group: str
    audio_url: Optional[str] = None
    tajweed_spans: list[dict] = []

    class Config:
        from_attributes = True


class AyahSchema(BaseModel):
    surah_number: int
    ayah_number: int
    text_uthmani: str
    text_imlaei: str
    page_number: Optional[int] = None
    juz_number: Optional[int] = None
    words: list[WordSchema] = []

    class Config:
        from_attributes = True


class WordDetailSchema(BaseModel):
    surah_number: int
    ayah_number: int
    word_position: int
    text_uthmani: str
    transliteration: str
    translation: dict
    pos_tag: str
    pos_group: str
    morphology: list[dict]
    lemma: Optional[str] = None
    root_id: Optional[int] = None
    root_arabic: Optional[str] = None
    root_translit: Optional[str] = None
    root_core_meaning: Optional[dict] = None
    occurrence_count: Optional[int] = None
    other_occurrences: list[dict] = []


class RootSchema(BaseModel):
    root_id: int
    root_arabic: str
    root_translit: str
    core_meaning: dict
    occurrence_count: int
    occurrences: list[dict] = []
