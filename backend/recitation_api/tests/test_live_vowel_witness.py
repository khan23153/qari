"""Live red highlighting for skipped words, wrong words and wrong harakat.

The live RNNT recognizer emits undiacritized text, so these sessions get
undiacritized RNNT words; the vowel marks come only from the independent,
unprompted Whisper witness (QARI_LIVE_VOWEL_WITNESS=whisper).
"""
import pytest

from app.services import streaming_session as ss
from tests.test_live_observed_mistakes import make_session
from tests.test_streaming import _pcm_seconds

RED = "#EF4444"
SIRAT = ["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتَ", "عَلَيْهِمْ"]


def _rnnt(words, start=0.1, step=0.5):
    """An undiacritized, timed RNNT window (raw text == plain text)."""
    norm = [ss._normalize(w) for w in words]
    times = [(start + i * step, start + i * step + 0.4) for i in range(len(norm))]
    return ss.ObservedTimedTranscript(norm, [0.95] * len(norm), times, list(norm))


def _live(monkeypatch, expected, heard, witness_tokens=None, seconds=3):
    s = make_session(expected)
    s._transcriber = lambda *_: ([], [])
    s._pcm = bytearray(_pcm_seconds(seconds))
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_transcriber", lambda *_: _rnnt(heard))
    if witness_tokens is None:
        monkeypatch.setattr(ss, "VOWEL_WITNESS", "off")
    else:
        monkeypatch.setattr(ss, "VOWEL_WITNESS", "whisper")
        monkeypatch.setattr(ss, "_vowel_witness_transcriber",
                            lambda *_: (list(witness_tokens), [0.9] * len(witness_tokens)))
    return s


# (a) الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ recited as الحمد العالمين
def test_skipped_words_turn_red_and_the_next_word_stays_matched():
    s = make_session(["الْحَمْدُ", "لِلَّهِ", "رَبِّ", "الْعَالَمِينَ", "الرَّحْمَنِ"])
    s._matcher.evaluate(["الحمد"], [.95])
    s._diff_events(s._matcher._states)
    heard = ["الحمد", "العالمين", "الرحمان"]
    events = []
    for _ in range(4):
        events += s._diff_events(s._matcher.evaluate(heard, [.95] * 3))
    by_index = {e["word_index"]: e for e in events}
    for index in (1, 2):
        assert by_index[index]["status"] == "error_skipped"
        assert by_index[index]["error_type"] == "missed"
        assert by_index[index]["display_color"] == RED
    assert s._last_status[3] == "matched"
    assert by_index.get(3, {}).get("status", "match") == "match"


# (b) أَنْعَمْتُ recited for أَنْعَمْتَ
@pytest.mark.asyncio
async def test_wrong_harakat_turns_red_from_the_whisper_witness(monkeypatch):
    s = _live(monkeypatch, SIRAT, ["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتَ", "عَلَيْهِمْ"],
              witness_tokens=["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتُ", "عَلَيْهِمْ"])
    events = {e["word_index"]: e for e in await s.maybe_transcribe(force=True)}
    wrong = events[2]
    assert wrong["status"] == "error_skipped"
    assert wrong["error_type"] == "harakat_mistake"
    assert wrong["spoken"] == "أَنْعَمْتُ"
    assert wrong["display_color"] == RED
    assert wrong["harakat_conflicts"][-1]["observed"] == "ُ"
    for index in (0, 1):
        assert events[index]["status"] == "match"
        assert events[index]["display_color"] is None
    # The last word may wait for more context, but is never red.
    assert events.get(3, {"status": "match"})["status"] == "match"


@pytest.mark.asyncio
async def test_without_the_witness_the_vowel_error_is_invisible(monkeypatch):
    """Why the witness is needed: RNNT text alone carries no harakat."""
    s = _live(monkeypatch, SIRAT, ["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتَ", "عَلَيْهِمْ"])
    events = {e["word_index"]: e for e in await s.maybe_transcribe(force=True)}
    assert events[2]["status"] == "match"


@pytest.mark.asyncio
async def test_whisper_hallucinations_never_reveal_or_redden_words(monkeypatch):
    s = _live(monkeypatch, SIRAT, ["صِرَاطَ", "الَّذِينَ"],
              witness_tokens=["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتُ", "عَلَيْهِمْ", "مَا", "يَغْفَى"])
    events = await s.maybe_transcribe()
    assert {e["word_index"] for e in events} <= {0, 1}
    assert all(e["status"] == "match" for e in events)


@pytest.mark.asyncio
async def test_correct_harakat_stays_matched_with_the_witness(monkeypatch):
    s = _live(monkeypatch, SIRAT, ["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتَ", "عَلَيْهِمْ"],
              witness_tokens=["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتَ", "عَلَيْهِمْ"])
    events = await s.maybe_transcribe(force=True)
    assert events and all(e["status"] == "match" and e["display_color"] is None for e in events)


@pytest.mark.asyncio
async def test_a_failed_whisper_decode_changes_nothing(monkeypatch):
    s = _live(monkeypatch, SIRAT, ["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتَ", "عَلَيْهِمْ"],
              witness_tokens=[])
    events = await s.maybe_transcribe(force=True)
    assert events and all(e["status"] == "match" for e in events)


# (c) a partial live stream: only صِرَاطَ الَّذِينَ said so far
@pytest.mark.asyncio
async def test_words_not_yet_reached_stay_pending_not_red(monkeypatch):
    s = _live(monkeypatch, SIRAT, ["صِرَاطَ", "الَّذِينَ"],
              witness_tokens=["صِرَاطَ", "الَّذِينَ"])
    events = {e["word_index"]: e for e in await s.maybe_transcribe()}
    assert events[0]["status"] == "match" and events[1]["status"] == "match"
    assert 2 not in events and 3 not in events
    assert s._last_status.get(2) in (None, "pending")
    assert s._last_status.get(3) in (None, "pending")
