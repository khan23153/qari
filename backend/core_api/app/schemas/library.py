"""Pydantic schemas for the Islamic Library API."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse

Category = Literal["hadith", "tafsir", "fiqh", "rijal", "daif_mawdu"]
RulingType = Literal["sahih", "hasan", "daif", "mawdu", "other"]
ReviewStatus = Literal["verified_from_source", "pending_scholar_review"]
DefectCause = Literal["inqita", "kadhdhab_matruk", "su_al_hifz", "majhul", "shudhudh", "illah"]
Reliability = Literal[
    "prophet", "compiler", "sahabi", "thiqah", "saduq", "daif", "matruk", "kadhdhab", "unknown"
]


class CategoryOut(BaseModel):
    slug: Category
    name_en: str
    name_ar: str
    collection_count: int


class BookOut(BaseModel):
    number: int
    name_en: str
    hadith_first: int
    hadith_last: int
    hadith_count: int


class RemoteSourceOut(BaseModel):
    provider: str
    license: str


class CollectionBrief(BaseModel):
    slug: str
    category: Category
    name_en: str
    name_ar: str
    author_en: str
    author_ar: str
    author_death_ah: Optional[int] = None
    availability: Literal["remote", "partial", "planned"]
    hadith_count: Optional[int] = None
    book_count: int
    tags: list[str]


class CollectionDetail(CollectionBrief):
    remote: Optional[RemoteSourceOut] = None


class GradeOut(BaseModel):
    scholar: str
    source_book: Optional[str] = None
    source_dataset: Optional[str] = None
    grade: str
    ruling_type: RulingType
    basis: Literal["scholar_grading", "inclusion_in_sahih"]


class DefectOut(BaseModel):
    cause: DefectCause
    cause_label_en: str
    cause_label_ar: str
    narrator_id: Optional[str] = None
    narrator_name_ar: Optional[str] = None
    scholar: str
    source_book: str
    quote_ar: Optional[str] = None
    explanation_en: Optional[str] = None
    review_status: ReviewStatus
    quote_verified: bool = False
    source_text_ar: Optional[str] = None


class ChainNodeOut(BaseModel):
    position: int
    name_ar: str
    narrator_id: Optional[str] = None
    role: Literal["compiler", "narrator", "prophet"] = "narrator"
    term_ar: Optional[str] = None
    identification: Literal["explicit", "pending_review", "ambiguous"]
    candidates: list[str] = []
    reliability: Reliability


class TranslationOut(BaseModel):
    language: str
    text: str
    source: str
    license_status: Literal["unverified", "licensed", "public_domain"]


class BookRef(BaseModel):
    number: int
    name_en: Optional[str] = None


class CollectionRef(BaseModel):
    slug: str
    name_en: str
    name_ar: str


class SourceOut(BaseModel):
    dataset: str
    editions: list[str]
    license: str


class HadithSummary(BaseModel):
    id: str
    collection: str
    number: int
    book_number: Optional[int] = None
    matn_ar: str
    translation_text: Optional[str] = None
    grades: list[GradeOut]


class HadithDetail(BaseModel):
    id: str
    collection: CollectionRef
    number: int
    arabic_number: Optional[int] = None
    book: BookRef
    text_ar: str
    isnad_ar: Optional[str] = None
    matn_ar: Optional[str] = None
    compiler_note_ar: Optional[str] = None
    translation: Optional[TranslationOut] = None
    grades: list[GradeOut]
    defects: list[DefectOut]
    chain: list[ChainNodeOut]
    gharib_words: list[str]
    source: SourceOut
    review_status: ReviewStatus


class NarratorBrief(BaseModel):
    id: str
    name_ar: str
    name_en: str
    reliability: Reliability


class RulingOut(BaseModel):
    scholar: str
    source_book: Optional[str] = None
    ruling_ar: str
    ruling_en: str
    review_status: ReviewStatus
    # The full verbatim entry the ruling is quoted from (e.g. a Taqrib entry).
    source_text_ar: Optional[str] = None


class NarratorOut(NarratorBrief):
    kunya_ar: Optional[str] = None
    generation: str
    tabaqah: Optional[int] = None
    birth_year_ah: Optional[int] = None
    death_year_ah: Optional[int] = None
    death_note: Optional[str] = None
    rulings: list[RulingOut]
    teachers: list[NarratorBrief]
    students: list[NarratorBrief]


class GharibOut(BaseModel):
    id: str
    word_ar: str
    matched_form: str
    root_ar: str
    transliteration: str
    gloss_en: str
    definition_ar: Optional[str] = None
    source_book: str
    review_status: ReviewStatus


class SearchOut(BaseModel):
    query: str
    hadiths: list[HadithSummary]
    narrators: list[NarratorBrief]
    collections: list[CollectionBrief]


CollectionPage = PaginatedResponse[CollectionBrief]
BookPage = PaginatedResponse[BookOut]
HadithPage = PaginatedResponse[HadithSummary]


# --- Forward check ---

class ForwardCheckIn(BaseModel):
    """A forwarded message to look up, in Arabic, Urdu or English."""
    text: str = Field(..., min_length=10, max_length=3000)


class ForwardMatchOut(BaseModel):
    band: Literal["strong", "possible"]
    score: float
    language: Literal["ar", "ur", "en"]
    collection_name: str
    hadith: HadithSummary


class ForwardCheckOut(BaseModel):
    query_language: Literal["ar", "ur", "en"]
    matches: list[ForwardMatchOut]
    searched_collections: list[str]
    note: str
