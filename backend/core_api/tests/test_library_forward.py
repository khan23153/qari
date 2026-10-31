"""Checking a forwarded hadith against the collections (POST /v1/library/check).

The matcher only finds and cites; it never grades. Editions are served by an
in-memory fake, so nothing here touches the network.
"""

import asyncio
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes.library import get_library_service
from app.library.forward_check import (
    POSSIBLE,
    STRONG,
    ForwardIndex,
    detect_language,
    tokenize,
)
from app.library.remote import DiskJsonCache, RemoteFetchError, RemoteHadithSource
from app.library.service import LibraryService
from app.main import app

BASE = "https://example.test/hadith-api"

INTENTIONS_AR = "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى فمن كانت هجرته إلى دنيا يصيبها"
INTENTIONS_EN = (
    "The reward of deeds depends upon the intentions and every person will "
    "get the reward according to what he has intended"
)
INTENTIONS_UR = (
    "اعمال کا دارومدار نیتوں پر ہے اور ہر عمل کا نتیجہ ہر انسان کو اس کی نیت "
    "کے مطابق ہی ملے گا"
)
PRAYER_EN = "The key to Paradise is prayer and the key to prayer is ablution"
PRAYER_AR = "مفتاح الجنة الصلاة ومفتاح الصلاة الوضوء"


def _full(records: list[tuple[int, str]], grades=None) -> dict:
    return {
        "metadata": {"name": "x", "section": {"1": "Revelation"}},
        "hadiths": [
            {
                "hadithnumber": n,
                "arabicnumber": n,
                "text": t,
                "grades": grades or [],
                "reference": {"book": 1, "hadith": i + 1},
            }
            for i, (n, t) in enumerate(records)
        ],
    }


def _one(number: int, text: str, grades=None) -> dict:
    return _full([(number, text)], grades)


FILES = {
    # Full editions used to build the index.
    "editions/ara-bukhari.min.json": _full([(1, INTENTIONS_AR), (2, "نص آخر عن الصيام في رمضان والقيام")]),
    "editions/eng-bukhari.min.json": _full([(1, INTENTIONS_EN), (2, "Another text about fasting in Ramadan and night prayer")]),
    "editions/urd-bukhari.min.json": _full([(1, INTENTIONS_UR)]),
    "editions/ara-tirmidhi.min.json": _full([(4, PRAYER_AR)]),
    "editions/eng-tirmidhi.min.json": _full([(4, PRAYER_EN)]),
    # Per-hadith records used to show a match.
    "editions/ara-bukhari/1.json": _one(1, INTENTIONS_AR),
    "editions/eng-bukhari/1.json": _one(1, INTENTIONS_EN),
    "editions/ara-tirmidhi/4.json": _one(4, PRAYER_AR),
    "editions/eng-tirmidhi/4.json": _one(4, PRAYER_EN, [
        {"name": "Al-Albani", "grade": "Sahih"},
        {"name": "Zubair Ali Zai", "grade": "Daif"},
    ]),
}


class FakeFetcher:
    def __init__(self, files: dict, fail: bool = False, delay: float = 0.0):
        self.files = files
        self.fail = fail
        self.delay = delay
        self.calls: list[str] = []

    async def __call__(self, url: str) -> dict:
        self.calls.append(url)
        if self.delay:
            await asyncio.sleep(self.delay)
        rel = url.removeprefix(BASE + "/")
        if self.fail or rel not in self.files:
            raise RemoteFetchError(url)
        return self.files[rel]


def _service(tmp_path: Path, fetcher: FakeFetcher | None, **kw) -> LibraryService:
    remote = None
    if fetcher is not None:
        remote = RemoteHadithSource(
            fetch_json=fetcher,
            cache=DiskJsonCache(tmp_path / "cache", max_bytes=5_000_000),
            base_url=BASE,
        )
    return LibraryService.from_bundled_data(
        remote=remote, forward_cache=tmp_path / "forward.pickle", **kw
    )


@pytest.fixture
def online(tmp_path):
    service = _service(tmp_path, FakeFetcher(FILES))
    app.dependency_overrides[get_library_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_library_service, None)


async def _check(text: str):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        return await ac.post("/v1/library/check", json={"text": text})


# --- the matcher ------------------------------------------------------------

def test_language_is_told_from_the_script():
    assert detect_language(INTENTIONS_AR) == "ar"
    assert detect_language(INTENTIONS_UR) == "ur"
    assert detect_language(INTENTIONS_EN) == "en"


def test_urdu_letters_fold_to_arabic_and_stopwords_drop():
    words = tokenize("اللہ کی کتاب", "ur")
    assert "كتاب" in words
    assert "کی" not in words and "كي" not in words


def _index() -> ForwardIndex:
    index = ForwardIndex()
    index.add_edition("bukhari", "ar", FILES["editions/ara-bukhari.min.json"])
    index.add_edition("bukhari", "en", FILES["editions/eng-bukhari.min.json"])
    index.add_edition("bukhari", "ur", FILES["editions/urd-bukhari.min.json"])
    index.add_edition("tirmidhi", "ar", FILES["editions/ara-tirmidhi.min.json"])
    index.add_edition("tirmidhi", "en", FILES["editions/eng-tirmidhi.min.json"])
    return index


def test_exact_arabic_wording_is_a_strong_match():
    m = _index().search("إنما الأعمال بالنيات وإنما لكل امرئ ما نوى")[0]
    assert m.hadith_id == "bukhari:1"
    assert m.score >= STRONG and m.band == "strong"


def test_urdu_and_english_forwards_find_the_same_hadith():
    assert _index().search(INTENTIONS_UR)[0].hadith_id == "bukhari:1"
    assert _index().search(INTENTIONS_EN)[0].hadith_id == "bukhari:1"


def test_part_of_a_hadith_is_still_found():
    m = _index().search("The key to Paradise is prayer and the key to prayer is ablution")[0]
    assert m.hadith_id == "tirmidhi:4"


def test_unrelated_text_finds_nothing():
    assert _index().search("Share this message with ten people and you will get good news today") == []
    assert all(m.score >= POSSIBLE for m in _index().search(INTENTIONS_EN))


def test_too_short_a_text_finds_nothing():
    assert _index().search("prayer") == []


# --- the API ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_returns_the_hadith_with_scholar_grades(online):
    r = await _check(PRAYER_EN)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["query_language"] == "en"
    top = body["matches"][0]
    assert top["hadith"]["id"] == "tirmidhi:4"
    assert top["collection_name"] == "Jami' al-Tirmidhi"
    assert top["band"] in ("strong", "possible")
    # Tirmidhi 4 is curated, so its reviewed grades are shown: scholars who
    # disagree are all listed, each by name.
    scholars = {g["scholar"]: g["ruling_type"] for g in top["hadith"]["grades"]}
    assert scholars["al-Albani"] == "sahih"
    assert scholars["Zubair 'Ali Za'i"] == "daif"
    assert "Jami' al-Tirmidhi" in body["searched_collections"]


@pytest.mark.asyncio
async def test_bukhari_match_carries_its_inclusion_grade(online):
    r = await _check(INTENTIONS_UR)
    top = r.json()["matches"][0]
    assert top["hadith"]["id"] == "bukhari:1"
    assert top["language"] == "ur"
    assert any(g["basis"] == "inclusion_in_sahih" for g in top["hadith"]["grades"])


@pytest.mark.asyncio
async def test_no_match_is_reported_as_not_found_not_as_a_grade(online):
    r = await _check("Share this message with ten people and you will get good news today")
    assert r.status_code == 200
    body = r.json()
    assert body["matches"] == []
    assert "not found" in body["note"].lower()


@pytest.mark.asyncio
async def test_index_is_built_once_and_kept_on_disk(tmp_path):
    fetcher = FakeFetcher(FILES)
    service = _service(tmp_path, fetcher)
    await service.check_forward(PRAYER_EN)
    await service.check_forward(INTENTIONS_EN)
    edition_calls = [c for c in fetcher.calls if c.endswith(".min.json")]
    assert len(edition_calls) == len(set(edition_calls))
    assert (tmp_path / "forward.pickle").exists()

    # A new process reads the saved index instead of downloading again.
    fresh = FakeFetcher(FILES)
    again = _service(tmp_path, fresh)
    await again.check_forward(PRAYER_EN)
    assert not [c for c in fresh.calls if c.endswith(".min.json")]


@pytest.mark.asyncio
async def test_slow_first_build_answers_503_preparing(tmp_path):
    service = _service(tmp_path, FakeFetcher(FILES, delay=0.05), forward_wait_sec=0.01)
    app.dependency_overrides[get_library_service] = lambda: service
    try:
        r = await _check(PRAYER_EN)
        assert r.status_code == 503
        assert "preparing" in r.json()["detail"].lower()
        await asyncio.sleep(2.5)
        r = await _check(PRAYER_EN)
        assert r.status_code == 200
    finally:
        app.dependency_overrides.pop(get_library_service, None)


@pytest.mark.asyncio
async def test_unreachable_collections_are_503_and_retried(tmp_path):
    service = _service(tmp_path, FakeFetcher(FILES, fail=True))
    app.dependency_overrides[get_library_service] = lambda: service
    try:
        r = await _check(PRAYER_EN)
        assert r.status_code == 503
    finally:
        app.dependency_overrides.pop(get_library_service, None)


@pytest.mark.asyncio
async def test_without_remote_the_check_is_503(tmp_path):
    service = _service(tmp_path, None)
    app.dependency_overrides[get_library_service] = lambda: service
    try:
        r = await _check(PRAYER_EN)
        assert r.status_code == 503
    finally:
        app.dependency_overrides.pop(get_library_service, None)


@pytest.mark.asyncio
async def test_text_must_be_long_enough(online):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/v1/library/check", json={"text": "hi"})
    assert r.status_code == 422
