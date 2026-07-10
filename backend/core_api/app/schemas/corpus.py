"""Corpus Pydantic response models.

These schemas emit the JSON keys the Flutter client expects (see
``lib/data/models/word_model.dart`` / ``surah_model.dart``). Internal DB/ORM
field names are preserved; the mobile-facing names are applied via
``serialization_alias`` so the hand-written Dart models parse without
regeneration.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field


# --- Qari ---

class QariBrief(BaseModel):
    id: int
    name: str
    arabic_name: Optional[str] = None
    style: Optional[str] = None
    audio_base_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# --- Surah ---

class SurahBrief(BaseModel):
    """Surah metadata for list views (mobile-compatible keys).

    Field names bind to the ORM ``Surah`` attributes; the mobile-facing
    JSON keys are applied via ``serialization_alias``.
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: int = Field(serialization_alias="surah_id")
    surah_number: int
    name_arabic: str
    name_translation_en: Optional[str] = Field(default=None, serialization_alias="name_english")
    name_transliteration: Optional[str] = Field(default=None, serialization_alias="name_translation")
    revelation_place: str = Field(serialization_alias="revelation_type")
    ayah_count: int
    revelation_order: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None

    @computed_field
    def name(self) -> Optional[str]:
        """Romanized display name (mobile ``name`` key)."""
        return self.name_transliteration


class SurahDetail(SurahBrief):
    """Full surah metadata with context story."""
    juz_list: Optional[list] = None
    context_story_en: Optional[str] = Field(default=None, serialization_alias="context_story")


# --- Word ---

class TajweedAnnotationOut(BaseModel):
    id: int
    rule_category: str
    rule_name: str
    rule_name_arabic: Optional[str] = None
    description: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class WordBrief(BaseModel):
    """Embedded word in ayah responses (mobile-compatible keys)."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    word_id: int = Field(serialization_alias="word_id")
    surah_number: int
    ayah_number: int
    word_number: int = Field(serialization_alias="word_number")
    text: str = Field(serialization_alias="text")
    text_arabic: str
    transliteration: Optional[str] = Field(default=None, serialization_alias="transliteration")
    text_transliteration: Optional[str] = None
    translation_en: Optional[str] = Field(default=None, serialization_alias="translation_en")
    translation_ur: Optional[str] = Field(default=None, serialization_alias="translation_ur")
    translation_hi: Optional[str] = Field(default=None, serialization_alias="translation_hi")
    translation: Optional[str] = None
    pos_group: Optional[str] = None
    pos_arabic: Optional[str] = None
    root_arabic: Optional[str] = None
    root_id: Optional[int] = None
    morphology: Optional[dict] = None
    lemma: Optional[str] = None
    text_clean: Optional[str] = None
    audio_url: Optional[str] = None
    tajweed_spans: Optional[list] = None


class WordDetail(BaseModel):
    """Full word detail with morphology, root, and other occurrences."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    word_id: int = Field(serialization_alias="word_id")
    surah_number: int
    ayah_number: int
    word_number: int = Field(serialization_alias="word_number")
    text: str = Field(serialization_alias="text")
    text_arabic: str
    transliteration: Optional[str] = Field(default=None, serialization_alias="transliteration")
    text_transliteration: Optional[str] = None
    translation_en: Optional[str] = Field(default=None, serialization_alias="translation_en")
    translation_ur: Optional[str] = Field(default=None, serialization_alias="translation_ur")
    translation_hi: Optional[str] = Field(default=None, serialization_alias="translation_hi")
    translation: Optional[str] = None
    pos_group: Optional[str] = None
    pos_detail: Optional[str] = None
    morphology_features: Optional[dict] = None
    audio_url: Optional[str] = None
    root: Optional["RootBrief"] = None
    tajweed_annotations: list[TajweedAnnotationOut] = []
    other_occurrences: list["WordOccurrence"] = []


class WordOccurrence(BaseModel):
    """A location where the same root appears."""
    surah_number: int
    ayah_number: int
    word_position: int
    text_arabic: str
    model_config = ConfigDict(from_attributes=True)


# --- Root ---

class RootBrief(BaseModel):
    id: int
    root_arabic: str
    root_transliteration: str
    meaning: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class RootDetail(BaseModel):
    """Full root detail with meaning and occurrence list."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    root_id: int = Field(serialization_alias="root_id")
    root_arabic: str
    root_transliteration: str
    core_meaning: Optional[str] = Field(default=None, serialization_alias="core_meaning")
    meaning: Optional[str] = None
    occurrence_count: int
    derived_words: list = []
    occurrences: list[WordOccurrence] = []


# --- Ayah ---

class AyahOut(BaseModel):
    """An ayah with embedded word array (mobile-compatible keys)."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    ayah_id: int = Field(serialization_alias="ayah_id")
    surah_number: int
    ayah_number: int
    ayah_text: str = Field(serialization_alias="ayah_text")
    text_arabic: str
    ayah_text_simple: Optional[str] = Field(default=None, serialization_alias="ayah_text_simple")
    text_transliteration: Optional[str] = None
    translation_en: Optional[str] = Field(default=None, serialization_alias="translation_en")
    translation_ur: Optional[str] = Field(default=None, serialization_alias="translation_ur")
    translation_hi: Optional[str] = Field(default=None, serialization_alias="translation_hi")
    text_translation: Optional[str] = None
    juz: Optional[int] = Field(default=None, serialization_alias="juz_number")
    page: Optional[int] = Field(default=None, serialization_alias="page_number")
    sajda: bool = False
    audio_url: Optional[str] = None
    words: list[WordBrief] = []


# Resolve forward refs
WordDetail.model_rebuild()
RootDetail.model_rebuild()
