"""Exercise the configured matcher through the actual production wrapper."""

import math
import struct
from types import SimpleNamespace

import pytest

from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus
from ml.inference import faster_whisper_transcriber as fwt


WORDS = ["بسم", "الله", "الرحمن", "الرحيم"]
VOCABULARY = frozenset([*WORDS, "الناس", "سور", "الصور"])
BOUNDARIES = [
    {"word_index_end": 1, "word_count": 2},
    {"word_index_end": 3, "word_count": 2},
]


@pytest.fixture
def production_session(monkeypatch):
    entries = [{"text_with_tashkeel": w, "clean_text": w} for w in WORDS]
    monkeypatch.setattr(
        ss, "resolve_reference_words_sequence",
        lambda refs: (WORDS, WORDS, "", entries, BOUNDARIES),
    )
    monkeypatch.setattr(ss, "_get_live_error_vocabulary", lambda: VOCABULARY)
    monkeypatch.setattr(ss.settings, "ml_use_stub", False)
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(fwt, "get_transcriber", lambda: SimpleNamespace(load=lambda: None))
    session = ss.StreamingRecitationSession(surah=1, ayah_from=1, ayah_to=1)
    session.load_reference()
    assert isinstance(session._matcher, main._ConservativeLiveMatcher)
    return session


def pcm(seconds):
    return b"".join(
        struct.pack("<h", int(10000 * math.sin(2 * math.pi * 220 * n / 16000)))
        for n in range(int(seconds * 16000))
    )


def test_production_wrapper_retains_vocabulary_and_ayah_bounds(production_session):
    delegate = production_session._matcher._delegate
    assert delegate._known_error_words == VOCABULARY
    assert delegate._ayah_ranges == [(0, 1), (2, 3)]
    assert delegate._ayah_ceiling(0, 4) == 4


def test_production_wrapper_rejects_distinct_quran_word_alias(production_session):
    # A composed article/emphasis alias is allowed only for an unknown spelling.
    # "sur" is an actual different Quran word, not a spelling of "al-sur".
    assert not production_session._matcher._delegate._is_match("سور", "الصور")


def test_final_wrapper_retains_distinct_word_guard(production_session):
    delegate = production_session._matcher._delegate
    delegate.reference = ["الصور"]
    production_session._matcher.reference = ["الصور"]
    states = production_session._matcher.finalize(["سور"], [.95])
    assert states[0].status == WordStatus.ERROR


@pytest.mark.asyncio
async def test_supported_live_substitution_is_forwarded_and_cursor_advances(
    production_session, monkeypatch,
):
    decodes = iter([
        (["بسم", "الله"], [.95, .95]),
        (["بسم", "الله", "الناس", "الرحيم"], [.95] * 4),
    ])
    monkeypatch.setattr(ss, "_independent_transcriber", lambda audio, sr: next(decodes))
    production_session.add_audio(pcm(1.5))
    await production_session.maybe_transcribe()
    production_session.add_audio(pcm(1.5))
    events = await production_session.maybe_transcribe()
    errors = [e for e in events if e["word_index"] == 2]
    assert len(errors) == 1
    error = errors[0]
    assert error["status"] == "error_skipped"
    assert error["evidence_confirmed"] is True
    assert error["spoken"] == "الناس"
    assert any(e["word_index"] == 3 and e["status"] == "match" for e in events)
    assert production_session._matcher._cursor == 4


@pytest.mark.asyncio
@pytest.mark.parametrize("spoken,confidence", [("اسقباعه", .95), ("الناس", .2)])
async def test_unknown_or_uncertain_live_gap_stays_neutral(
    production_session, monkeypatch, spoken, confidence,
):
    decodes = iter([
        (["بسم", "الله"], [.95, .95]),
        (["بسم", "الله", spoken, "الرحيم"], [.95, .95, confidence, .95]),
    ])
    monkeypatch.setattr(ss, "_independent_transcriber", lambda audio, sr: next(decodes))
    production_session.add_audio(pcm(1.5))
    await production_session.maybe_transcribe()
    production_session.add_audio(pcm(1.5))
    events = await production_session.maybe_transcribe()
    assert all(e["word_index"] != 2 for e in events)
    assert production_session._matcher._cursor == 4


@pytest.mark.asyncio
async def test_recent_silence_does_not_decode_or_advance(production_session, monkeypatch):
    calls = []
    monkeypatch.setattr(
        ss, "_independent_transcriber",
        lambda audio, sr: (calls.append(len(audio)) or WORDS, [.95] * 4),
    )
    production_session.add_audio(pcm(1.5))
    await production_session.maybe_transcribe()
    before = (len(calls), production_session._matcher._cursor)
    production_session.add_audio(b"\0\0" * 24000)
    assert await production_session.maybe_transcribe() == []
    assert before == (len(calls), production_session._matcher._cursor)


@pytest.mark.asyncio
async def test_speech_budget_bounds_a_long_hallucinated_decode(production_session, monkeypatch):
    monkeypatch.setattr(ss, "_independent_transcriber", lambda audio, sr: (WORDS, [.95] * 4))
    # 0.24s above threshold is enough to trigger a pass, but only one word fits
    # the unchanged 2.4 words/active-second budget.
    production_session.add_audio(pcm(.24) + b"\0\0" * 20160)
    events = await production_session.maybe_transcribe()
    assert [e["word_index"] for e in events] == [0]
    assert production_session._matcher._cursor == 1
