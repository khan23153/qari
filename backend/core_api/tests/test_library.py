"""Islamic Library API: catalog, hadith detail, grades, defects, isnad, rijal, gharib.

The library is file-backed (no DB/Redis), so these tests run without
Postgres. Remote catalog fetching is replaced by an in-memory fake so the
suite never touches the network.
"""

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes.library import get_library_service
from app.library.arabic import normalize_arabic, strip_clitics
from app.library.grading import display_scholar, ruling_type
from app.library.remote import DiskJsonCache, RemoteFetchError, RemoteHadithSource
from app.library.service import LibraryService
from app.main import app

BASE = "https://example.test/hadith-api"


class FakeFetcher:
    """Serves dataset-shaped JSON from a dict and counts requests."""

    def __init__(self, files: dict[str, dict], fail: bool = False):
        self.files = files
        self.fail = fail
        self.calls: list[str] = []

    async def __call__(self, url: str) -> dict:
        self.calls.append(url)
        if self.fail:
            raise RemoteFetchError(url)
        rel = url.removeprefix(BASE + "/")
        if rel not in self.files:
            raise RemoteFetchError(url)
        return self.files[rel]


def _edition(text: str, number: int, book: int, grades=None) -> dict:
    return {
        "metadata": {"name": "x", "section": {str(book): "Book of Faith"}},
        "hadiths": [{
            "hadithnumber": number,
            "arabicnumber": number,
            "text": text,
            "grades": grades or [],
            "reference": {"book": book, "hadith": 1},
        }],
    }


MUSLIM_8_FILES = {
    "editions/ara-muslim/8.json": _edition("حَدَّثَنَا فُلَانٌ قَالَ نَصٌّ عَرَبِيٌّ", 8, 1),
    "editions/eng-muslim/8.json": _edition("English text", 8, 1),
}
SECTION_FILES = {
    "editions/ara-muslim/sections/1.json": {
        "metadata": {"name": "x", "section": {"1": "The Book of Faith"}},
        "hadiths": [
            {"hadithnumber": 8, "arabicnumber": 8, "text": "نَصٌّ أَوَّلُ", "grades": [], "reference": {"book": 1, "hadith": 1}},
            {"hadithnumber": 9, "arabicnumber": 9, "text": "نَصٌّ ثَانٍ", "grades": [], "reference": {"book": 1, "hadith": 2}},
        ],
    },
    "editions/eng-muslim/sections/1.json": {
        "metadata": {"name": "x", "section": {"1": "The Book of Faith"}},
        "hadiths": [
            {"hadithnumber": 8, "arabicnumber": 8, "text": "First", "grades": [], "reference": {"book": 1, "hadith": 1}},
            {"hadithnumber": 9, "arabicnumber": 9, "text": "Second", "grades": [], "reference": {"book": 1, "hadith": 2}},
        ],
    },
}


def _service(tmp_path: Path, fetcher: FakeFetcher | None = None, max_bytes: int = 1_000_000) -> LibraryService:
    remote = None
    if fetcher is not None:
        remote = RemoteHadithSource(fetch_json=fetcher, cache=DiskJsonCache(tmp_path, max_bytes=max_bytes), base_url=BASE)
    return LibraryService.from_bundled_data(remote=remote)


@pytest.fixture
def offline(tmp_path):
    service = _service(tmp_path)
    app.dependency_overrides[get_library_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_library_service, None)


async def _get(path: str, **params):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        return await ac.get(path, params=params)


# --- pure helpers ----------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("Sahih", "sahih"),
    ("Hasan Sahih", "sahih"),
    ("Sahih Lighairihi", "sahih"),
    ("Isnaad Sahih Bukhari And Muslim", "sahih"),
    ("Hasan", "hasan"),
    ("Daif", "daif"),
    ("Daif Jiddan", "daif"),
    ("Munkar", "daif"),
    ("Mawdu", "mawdu"),
    ("", "other"),
])
def test_ruling_type_normalises_dataset_grades(raw, expected):
    assert ruling_type(raw) == expected


def test_display_scholar_uses_conventional_transliteration():
    assert display_scholar("Al-Albani") == "al-Albani"
    assert display_scholar("Shuaib Al Arnaut") == "Shu'ayb al-Arna'ut"
    assert display_scholar("Someone New") == "Someone New"


def test_normalize_arabic_strips_tashkeel_tatweel_and_punctuation():
    assert normalize_arabic("بِالنِّيَّاتِ،") == "بالنيات"
    assert normalize_arabic("الأَعْمَالُ") == "الاعمال"
    assert normalize_arabic("هِجْرَتُهُ‏") == "هجرته"


def test_strip_clitics_yields_candidate_stems():
    stems = strip_clitics("بالنيات")
    assert "النيات" in stems and "نيات" in stems


# --- catalog ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_categories_list_all_five_with_counts(offline):
    resp = await _get("/v1/library/categories")
    assert resp.status_code == 200
    cats = {c["slug"]: c for c in resp.json()}
    assert set(cats) == {"hadith", "tafsir", "fiqh", "rijal", "daif_mawdu"}
    assert cats["hadith"]["collection_count"] == 7
    assert cats["daif_mawdu"]["name_ar"] == "الضعيف والموضوع"


@pytest.mark.asyncio
async def test_collections_filter_by_category_and_paginate(offline):
    resp = await _get("/v1/library/collections", category="hadith", page=1, page_size=4)
    body = resp.json()
    assert resp.status_code == 200
    assert body["total"] == 7 and body["page_size"] == 4 and body["has_next"] is True
    assert [c["slug"] for c in body["items"]] == ["bukhari", "muslim", "abudawud", "tirmidhi"]
    page2 = (await _get("/v1/library/collections", category="hadith", page=2, page_size=4)).json()
    assert [c["slug"] for c in page2["items"]] == ["nasai", "ibnmajah", "malik"]
    assert page2["has_next"] is False


@pytest.mark.asyncio
async def test_kutub_sittah_and_critical_works_are_listed(offline):
    items = (await _get("/v1/library/collections", page_size=100)).json()["items"]
    sittah = {c["slug"] for c in items if "kutub_sittah" in c["tags"]}
    assert sittah == {"bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah"}
    critical = {c["slug"]: c for c in items if c["category"] == "daif_mawdu"}
    assert set(critical) == {"al-mawduat", "silsilat-al-daifa"}
    assert critical["silsilat-al-daifa"]["author_en"] == "Muhammad Nasir al-Din al-Albani"


@pytest.mark.asyncio
async def test_unknown_category_is_rejected(offline):
    resp = await _get("/v1/library/collections", category="poetry")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_collection_books_come_from_the_real_chapter_index(offline):
    resp = await _get("/v1/library/collections/bukhari/books", page_size=3)
    body = resp.json()
    assert resp.status_code == 200
    assert body["total"] == 97
    first = body["items"][0]
    assert first == {"number": 1, "name_en": "Revelation", "hadith_first": 1, "hadith_last": 7, "hadith_count": 7}


@pytest.mark.asyncio
async def test_unknown_collection_is_problem_404(offline):
    resp = await _get("/v1/library/collections/nope/books")
    assert resp.status_code == 404
    assert resp.json()["title"] == "Not Found"


# --- hadith detail ---------------------------------------------------------

@pytest.mark.asyncio
async def test_bukhari_1_has_sourced_text_isnad_and_inclusion_grade(offline):
    resp = await _get("/v1/library/hadiths/bukhari:1")
    h = resp.json()
    assert resp.status_code == 200
    assert normalize_arabic(h["matn_ar"]).startswith("انما الاعمال بالنيات")
    assert "الحميدي" in normalize_arabic(h["isnad_ar"])
    assert h["book"] == {"number": 1, "name_en": "Revelation"}
    assert h["translation"]["license_status"] == "unverified"
    assert h["review_status"] == "verified_from_source"
    # Sahih al-Bukhari's own condition, attributed to the compiler, not to AI.
    assert h["grades"] == [{
        "scholar": "al-Bukhari",
        "source_book": "al-Jami' al-Sahih",
        "source_dataset": None,
        "grade": "Sahih",
        "ruling_type": "sahih",
        "basis": "inclusion_in_sahih",
    }]
    assert h["defects"] == []


@pytest.mark.asyncio
async def test_isnad_runs_compiler_to_prophet_with_reliability(offline):
    chain = (await _get("/v1/library/hadiths/bukhari:1")).json()["chain"]
    assert chain[0]["role"] == "compiler"
    assert chain[-1]["role"] == "prophet"
    assert [n["position"] for n in chain] == list(range(len(chain)))
    by_id = {n["narrator_id"]: n for n in chain if n["narrator_id"]}
    assert by_id["umar-ibn-al-khattab"]["reliability"] == "sahabi"
    assert by_id["sufyan-ibn-uyaynah"]["reliability"] == "thiqah"
    assert by_id["sufyan-ibn-uyaynah"]["identification"] == "pending_review"


@pytest.mark.asyncio
async def test_ambiguous_narrator_keeps_candidates_instead_of_guessing(offline):
    chain = (await _get("/v1/library/hadiths/abudawud:2201")).json()["chain"]
    sufyan = next(n for n in chain if normalize_arabic(n["name_ar"]) == "سفيان")
    assert sufyan["narrator_id"] is None
    assert sufyan["identification"] == "ambiguous"
    assert sufyan["candidates"] == ["sufyan-ibn-uyaynah", "sufyan-al-thawri"]
    assert sufyan["reliability"] == "unknown"


@pytest.mark.asyncio
async def test_differing_scholar_grades_are_all_shown(offline):
    h = (await _get("/v1/library/hadiths/tirmidhi:4")).json()
    grades = {(g["scholar"], g["grade"], g["ruling_type"]) for g in h["grades"]}
    assert grades == {
        ("Ahmad Shakir", "Sahih Lighairihi", "sahih"),
        ("al-Albani", "Sahih", "sahih"),
        ("Zubair 'Ali Za'i", "Daif", "daif"),
    }
    assert all(g["source_dataset"].startswith("fawazahmed0/hadith-api") for g in h["grades"])
    causes = [(d["cause"], d["narrator_id"]) for d in h["defects"]]
    assert causes == [("su_al_hifz", "sulayman-ibn-qarm"), ("su_al_hifz", "abu-yahya-al-qattat")]


@pytest.mark.asyncio
async def test_fabricated_hadith_shows_cause_breakdown_with_citations(offline):
    h = (await _get("/v1/library/hadiths/tirmidhi:172")).json()
    assert {g["ruling_type"] for g in h["grades"]} >= {"mawdu"}
    assert normalize_arabic(h["compiler_note_ar"]).startswith("قال ابو عيسى هذا حديث غريب")
    liar = next(d for d in h["defects"] if d["cause"] == "kadhdhab_matruk")
    assert liar["narrator_name_ar"] == "يعقوب بن الوليد المدني"
    assert liar["scholar"] == "Ibn Hajar al-'Asqalani" and liar["source_book"] == "Taqrib al-Tahdhib"
    assert liar["cause_label_en"] == "Liar or abandoned narrator"
    assert liar["review_status"] == "pending_scholar_review"
    umari = next(d for d in h["defects"] if d["narrator_id"] == "abdullah-ibn-umar-al-umari")
    assert umari["quote_verified"] is True
    assert umari["quote_ar"] in h["text_ar"], "verified quote must be verbatim from the source"


@pytest.mark.asyncio
async def test_every_defect_cause_is_from_the_allowed_set(offline):
    allowed = {"inqita", "kadhdhab_matruk", "su_al_hifz", "majhul", "shudhudh", "illah"}
    for hid in ("bukhari:1", "abudawud:2201", "tirmidhi:4", "tirmidhi:172"):
        h = (await _get(f"/v1/library/hadiths/{hid}")).json()
        for d in h["defects"]:
            assert d["cause"] in allowed
            assert d["scholar"] and d["source_book"], "every defect needs a citation"


@pytest.mark.asyncio
async def test_unknown_hadith_offline_is_404(offline):
    assert (await _get("/v1/library/hadiths/muslim:8")).status_code == 404
    assert (await _get("/v1/library/hadiths/not-a-collection:1")).status_code == 404


@pytest.mark.asyncio
async def test_malformed_hadith_id_is_422(offline):
    assert (await _get("/v1/library/hadiths/bukhari")).status_code == 422


@pytest.mark.asyncio
async def test_weak_filter_lists_hadith_any_scholar_graded_weak(offline):
    body = (await _get("/v1/library/hadiths", graded="weak")).json()
    assert [h["id"] for h in body["items"]] == ["tirmidhi:4", "tirmidhi:172"]
    fabricated = (await _get("/v1/library/hadiths", graded="fabricated")).json()
    assert [h["id"] for h in fabricated["items"]] == ["tirmidhi:172"]
    summary = fabricated["items"][0]
    assert normalize_arabic(summary["matn_ar"]).startswith("الوقت الاول")
    assert {"scholar": "al-Albani", "grade": "Mawdu", "ruling_type": "mawdu"} in [
        {k: g[k] for k in ("scholar", "grade", "ruling_type")} for g in summary["grades"]
    ]


# --- rijal and gharib ------------------------------------------------------

@pytest.mark.asyncio
async def test_narrator_profile_with_rulings_and_derived_links(offline):
    resp = await _get("/v1/library/narrators/sufyan-ibn-uyaynah")
    n = resp.json()
    assert resp.status_code == 200
    assert n["name_ar"] == "سفيان بن عيينة"
    assert n["death_year_ah"] == 198 and n["tabaqah"] == 8
    assert n["rulings"][0]["source_book"] == "Taqrib al-Tahdhib"
    assert [t["id"] for t in n["teachers"]] == ["yahya-ibn-said-al-ansari"]
    assert [s["id"] for s in n["students"]] == ["al-humaydi"]
    assert n["students"][0]["reliability"] == "thiqah"


@pytest.mark.asyncio
async def test_unknown_narrator_is_404(offline):
    assert (await _get("/v1/library/narrators/nobody")).status_code == 404


@pytest.mark.asyncio
async def test_gharib_lookup_handles_tashkeel_and_clitics(offline):
    resp = await _get("/v1/library/gharib/بِالنِّيَّاتِ،")
    g = resp.json()
    assert resp.status_code == 200
    assert g["id"] == "niyyah"
    assert g["root_ar"] == "ن و ي"
    assert g["transliteration"] == "an-niyyāt"
    assert g["matched_form"] == "النيات"
    assert "Nihayah" in g["source_book"]
    hijrah = (await _get("/v1/library/gharib/فَهِجْرَتُهُ")).json()
    assert hijrah["id"] == "hijrah"


@pytest.mark.asyncio
async def test_gharib_miss_is_404(offline):
    assert (await _get("/v1/library/gharib/الصَّلاَةُ")).status_code == 404


@pytest.mark.asyncio
async def test_search_matches_arabic_without_tashkeel_and_english(offline):
    body = (await _get("/v1/library/search", q="مفتاح الجنة")).json()
    assert [h["id"] for h in body["hadiths"]] == ["tirmidhi:4"]
    english = (await _get("/v1/library/search", q="intentions")).json()
    assert "bukhari:1" in [h["id"] for h in english["hadiths"]]
    people = (await _get("/v1/library/search", q="Sufyan")).json()
    assert {n["id"] for n in people["narrators"]} == {"sufyan-ibn-uyaynah", "sufyan-al-thawri"}
    books = (await _get("/v1/library/search", q="Albani")).json()
    assert [c["slug"] for c in books["collections"]] == ["silsilat-al-daifa"]


@pytest.mark.asyncio
async def test_search_requires_two_characters(offline):
    assert (await _get("/v1/library/search", q="a")).status_code == 422


# --- on-demand remote catalog ---------------------------------------------

@pytest.mark.asyncio
async def test_remote_hadith_is_fetched_once_then_served_from_disk_cache(tmp_path):
    fetcher = FakeFetcher(MUSLIM_8_FILES)
    service = _service(tmp_path, fetcher)
    app.dependency_overrides[get_library_service] = lambda: service
    try:
        first = await _get("/v1/library/hadiths/muslim:8")
        assert first.status_code == 200
        h = first.json()
        assert h["text_ar"] == "حَدَّثَنَا فُلَانٌ قَالَ نَصٌّ عَرَبِيٌّ"
        assert h["translation"]["text"] == "English text"
        assert h["grades"][0]["basis"] == "inclusion_in_sahih"
        assert h["chain"] == [] and h["isnad_ar"] is None
        assert len(fetcher.calls) == 2
        # A fresh service over the same cache dir proves the cache is on disk.
        service2 = _service(tmp_path, fetcher)
        app.dependency_overrides[get_library_service] = lambda: service2
        assert (await _get("/v1/library/hadiths/muslim:8")).status_code == 200
        assert len(fetcher.calls) == 2
    finally:
        app.dependency_overrides.pop(get_library_service, None)


@pytest.mark.asyncio
async def test_remote_book_page_lists_section_hadiths(tmp_path):
    fetcher = FakeFetcher(SECTION_FILES)
    service = _service(tmp_path, fetcher)
    app.dependency_overrides[get_library_service] = lambda: service
    try:
        body = (await _get("/v1/library/collections/muslim/books/1/hadiths", page_size=1)).json()
        assert body["total"] == 2 and body["has_next"] is True
        assert body["items"][0]["id"] == "muslim:8"
        assert body["items"][0]["translation_text"] == "First"
    finally:
        app.dependency_overrides.pop(get_library_service, None)


@pytest.mark.asyncio
async def test_remote_failure_is_503_problem(tmp_path):
    service = _service(tmp_path, FakeFetcher({}, fail=True))
    app.dependency_overrides[get_library_service] = lambda: service
    try:
        resp = await _get("/v1/library/hadiths/muslim:8")
        assert resp.status_code == 503
        assert resp.json()["title"] == "Service Unavailable"
    finally:
        app.dependency_overrides.pop(get_library_service, None)


@pytest.mark.asyncio
async def test_seeded_hadith_never_hits_the_network(tmp_path):
    fetcher = FakeFetcher({}, fail=True)
    service = _service(tmp_path, fetcher)
    app.dependency_overrides[get_library_service] = lambda: service
    try:
        assert (await _get("/v1/library/hadiths/tirmidhi:4")).status_code == 200
        assert fetcher.calls == []
    finally:
        app.dependency_overrides.pop(get_library_service, None)


def test_disk_cache_evicts_least_recently_used_over_budget(tmp_path):
    cache = DiskJsonCache(tmp_path, max_bytes=300)
    cache.put("a.json", {"x": "a" * 100})
    cache.put("b.json", {"x": "b" * 100})
    assert cache.get("a.json") is not None  # touch a → b is now oldest
    cache.put("c.json", {"x": "c" * 100})
    assert cache.get("b.json") is None
    assert cache.get("a.json") is not None and cache.get("c.json") is not None
    assert cache.size_bytes() <= 300


def test_disk_cache_rejects_path_escape(tmp_path):
    cache = DiskJsonCache(tmp_path, max_bytes=1000)
    with pytest.raises(ValueError):
        cache.put("../evil.json", {})


def test_bundled_data_is_valid_json_with_review_status():
    data = Path(__file__).resolve().parents[1] / "app" / "library" / "data"
    seed = json.loads((data / "seed.json").read_text(encoding="utf-8"))
    for n in seed["narrators"]:
        assert all(r["review_status"] in {"verified_from_source", "pending_scholar_review"} for r in n["rulings"])
    for g in seed["gharib"]:
        assert g["review_status"] in {"verified_from_source", "pending_scholar_review"}
