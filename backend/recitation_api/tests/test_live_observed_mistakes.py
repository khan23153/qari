"""Word errors require observed speech or an unambiguous passed omission."""
import pytest

from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher


def make_session(expected):
    s = ss.StreamingRecitationSession()
    s.reference_words = [ss._normalize(w) for w in expected]
    s.display_words = expected
    s.reference_text_with_tashkeel_words = expected
    s.word_entries = [{"text_with_tashkeel": w, "clean_text": n}
                      for w, n in zip(expected, s.reference_words)]
    s._canonical_reference_raw = True
    s._is_stub = False
    d = StreamingMatcher(s.reference_words, strict_word_identity=True,
                         known_error_words=set(s.reference_words) | {"الصمد"})
    s._matcher = main._ConservativeLiveMatcher(s.reference_words, delegate=d)
    s._matcher.max_live_words = len(expected)
    return s


def test_skipped_lillah_rabb_are_immediate_confirmed_missed_events():
    s = make_session(["الْحَمْدُ", "لِلَّهِ", "رَبِّ", "الْعَالَمِينَ", "الرَّحْمَنِ"])
    s._matcher.evaluate(["الحمد"], [.95])
    s._diff_events(s._matcher._states)
    words = ["الحمد", "العالمين", "الرحمان"]
    for _ in range(4):
        states = s._matcher.evaluate(words, [.95] * len(words))
        events = s._diff_events(states)
        missed = [e for e in events if e["word_index"] in (1, 2)]
        if missed:
            break
    assert [(e["word_index"], e["status"], e.get("error_type"), e["evidence_confirmed"])
            for e in missed] == [(1, "error_skipped", "missed", True),
                                 (2, "error_skipped", "missed", True)]
    assert not s._diff_events(states)


def test_independent_decode_preserves_raw_marks_and_timed_transcript_api(monkeypatch):
    import sys
    import types
    from ml.inference.transcript import TimedTranscript
    raw = ["أَنْعَمْتُ", "عَلَيْهِمْ"]
    native = TimedTranscript(raw, [.94, .96], [(.1, .5), (.8, 1.2)])
    fake = types.SimpleNamespace(get_transcriber=lambda: types.SimpleNamespace(transcribe=lambda *_: native))
    monkeypatch.setitem(sys.modules, "ml.inference.fastconformer_transcriber", fake)
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    decoded = ss._independent_transcriber([], 16000)
    words, scores = decoded
    assert words == ["انعمت", "عليهم"] and scores == [.94, .96]
    assert isinstance(decoded, TimedTranscript)
    assert decoded.raw_words == raw
    assert decoded.timings == native.timings


@pytest.mark.asyncio
async def test_observed_anamtu_conflict_is_live_error_without_extra_progress(monkeypatch):
    from tests.test_streaming import _pcm_seconds
    s = make_session(["أَنْعَمْتَ", "عَلَيْهِمْ", "غَيْرِ"])
    s._transcriber = lambda *_: ([], [])
    s._pcm = bytearray(_pcm_seconds(3))
    heard = ss.ObservedTimedTranscript(["انعمت", "عليهم"], [.94, .96],
                                      [(.1, .5), (.8, 1.2)], ["أَنْعَمْتُ", "عَلَيْهِمْ"])
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_transcriber", lambda *_: heard)
    events = await s.maybe_transcribe(force=True)
    first = next(e for e in events if e["word_index"] == 0)
    assert first["status"] == "error_skipped"
    assert first["error_type"] == "harakat_mistake"
    assert first["evidence_source"] == "asr_diacritic"
    assert first["evidence_confirmed"] is True
    assert first["spoken"] == "أَنْعَمْتُ"
    assert s._matcher._cursor == 2
    assert not any(e["word_index"] == 2 for e in events)


@pytest.mark.asyncio
async def test_final_retains_original_harakat_error_when_recording_decode_loses_marks(monkeypatch):
    from tests.test_streaming import _pcm_seconds
    s = make_session(["أَنْعَمْتَ", "عَلَيْهِمْ"])
    s._transcriber = lambda *_: ([], [])
    s._pcm = bytearray(_pcm_seconds(3))
    heard = ss.ObservedTimedTranscript(["انعمت", "عليهم"], [.94, .96],
                                      [(.1, .5), (.8, 1.2)], ["أَنْعَمْتُ", "عَلَيْهِمْ"])
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_transcriber", lambda *_: heard)
    monkeypatch.setattr(s, "_write_wav", lambda: None)
    async def no_persist(*_):
        pass
    monkeypatch.setattr(s, "_persist", no_persist)
    await s.maybe_transcribe(force=True)
    monkeypatch.setattr(ss, "_independent_recording_transcriber", lambda *_: ([], []))
    result = await s.finalize()
    first = result["word_verdicts"][0]
    assert first["is_correct"] is False
    assert first["error_type"] == "harakat_mistake"
    assert first["actual_text"] == "أَنْعَمْتُ"
    assert first["observed_text"] == "أَنْعَمْتُ"
    assert first["evidence_source"] == "asr_diacritic"
    assert first["display_color"] == "#EF4444"
    assert result["pronunciation_available"] is False
    assert result["tajweed_available"] is False


def test_review_schema_preserves_observed_evidence():
    from app.schemas.recitation import WordVerdictOut
    verdict = WordVerdictOut(word="انعمت", word_index=0, is_correct=False,
                             error_type="harakat_mistake", evidence_confirmed=True,
                             evidence_source="asr_diacritic", observed_text="أَنْعَمْتُ",
                             harakat_conflicts=[{"position": 4, "expected": "َ", "observed": "ُ"}],
                             display_color="#EF4444")
    data = verdict.model_dump()
    assert data["observed_text"] == "أَنْعَمْتُ"
    assert data["evidence_source"] == "asr_diacritic"
    assert data["harakat_conflicts"] and data["display_color"] == "#EF4444"


@pytest.mark.asyncio
async def test_confirmed_live_omissions_survive_independent_review_failure(monkeypatch):
    s = make_session(["الْحَمْدُ", "لِلَّهِ", "رَبِّ", "الْعَالَمِينَ", "الرَّحْمَنِ"])
    s._matcher.evaluate(["الحمد"], [.95])
    for _ in range(4):
        states = s._matcher.evaluate(["الحمد", "العالمين", "الرحمان"], [.95] * 3)
        s._diff_events(states)
    monkeypatch.setattr(s, "_write_wav", lambda: None)
    async def no_persist(*_):
        pass
    monkeypatch.setattr(s, "_persist", no_persist)
    result = await s.finalize()
    missed = [v for v in result["word_verdicts"] if v["word_index"] in (1, 2)]
    assert len(missed) == 2
    assert all(v["error_type"] == "missed" and v["evidence_confirmed"] is True
               and v["display_color"] == "#EF4444" for v in missed)


@pytest.mark.asyncio
async def test_final_only_observed_conflict_uses_original_asr_slot_after_invocation(monkeypatch):
    from tests.test_streaming import _pcm_seconds
    s = make_session(["أَنْعَمْتَ", "عَلَيْهِمْ", "أَنْعَمْتَ"])
    s._pcm = bytearray(_pcm_seconds(4))
    heard = ss.ObservedTimedTranscript(["قل", "انعمت", "عليهم", "انعمت"], [.95] * 4,
                                      [(.1, .3), (.5, .9), (1.2, 1.5), (1.8, 2.2)],
                                      ["قُلْ", "أَنْعَمْتُ", "عَلَيْهِمْ", "أَنْعَمْتَ"])
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_recording_transcriber", lambda *_: heard)
    monkeypatch.setattr(s, "_write_wav", lambda: None)
    async def no_persist(*_):
        pass
    monkeypatch.setattr(s, "_persist", no_persist)
    result = await s.finalize()
    assert [v["error_type"] for v in result["word_verdicts"]] == ["harakat_mistake", None, None]
    assert result["word_verdicts"][0]["observed_text"] == "أَنْعَمْتُ"
    assert s._matcher._cursor == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("raw,expected,score,stop,canonical", [
    ("الْعَالَمِينْ", "الْعَالَمِينَ", .95, True, True),
    ("العالمين", "الْعَالَمِينَ", .95, True, True),
    ("أَنْعَمْتُ", "أَنْعَمْتَ", .54, False, True),
    ("أَنْعَمْتُ", "أَنْعَمْتَ", .95, False, False),
    (None, "أَنْعَمْتَ", .95, False, True),
    ("أَنْعَمْتُ", "أَنْعَمْتَ", float("nan"), False, True),
    ("أَنْعَمْتُ", "أَنْعَمْتَ", 1.1, False, True),
])
async def test_stop_partial_weak_and_noncanonical_observations_abstain(monkeypatch, raw, expected, score, stop, canonical):
    from tests.test_streaming import _pcm_seconds
    s = make_session([expected, "عَلَيْهِمْ"])
    s._canonical_reference_raw = canonical
    if stop:
        s.ayah_boundaries = [{"word_index_end": 0, "word_count": 1}]
    s._transcriber = lambda *_: ([], [])
    s._pcm = bytearray(_pcm_seconds(2))
    heard = ss.ObservedTimedTranscript([ss._normalize(expected)], [score], [(.1, .5)], [raw])
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_transcriber", lambda *_: heard)
    events = await s.maybe_transcribe(force=True)
    assert not any(e.get("error_type") == "harakat_mistake" for e in events)
    assert not s._harakat_errors


@pytest.mark.asyncio
async def test_frozen_first_raw_error_cannot_be_cleared_or_borrowed_by_repetition(monkeypatch):
    from tests.test_streaming import _pcm_seconds
    s = make_session(["أَنْعَمْتَ", "عَلَيْهِمْ", "أَنْعَمْتَ"])
    s._transcriber = lambda *_: ([], [])
    replies = iter([
        ss.ObservedTimedTranscript(["انعمت", "عليهم"], [.95] * 2, [(.1, .5), (.8, 1.2)],
                                   ["أَنْعَمْتُ", "عَلَيْهِمْ"]),
        ss.ObservedTimedTranscript(["انعمت", "عليهم", "انعمت"], [.95] * 3,
                                   [(.1, .5), (.8, 1.2), (1.8, 2.2)],
                                   ["أَنْعَمْتَ", "عَلَيْهِمْ", "أَنْعَمْتَ"]),
    ])
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_transcriber", lambda *_: next(replies))
    s._pcm = bytearray(_pcm_seconds(2))
    first = await s.maybe_transcribe(force=True)
    assert first[0]["error_type"] == "harakat_mistake"
    s._pcm = bytearray(_pcm_seconds(3))
    second = await s.maybe_transcribe(force=True)
    assert [(e["word_index"], e["status"]) for e in second] == [(2, "match")]
    assert s._heard_word_evidence[0]["raw"] == "أَنْعَمْتُ"
    assert s._heard_word_evidence[2]["raw"] == "أَنْعَمْتَ"
    assert set(s._harakat_errors) == {0}


@pytest.mark.asyncio
@pytest.mark.parametrize("silent,heard", [(True, "الحمد"), (False, "الصمد"), (False, "ضظذشش"), (False, "")])
async def test_silence_unknown_and_wrong_unanchored_speech_leave_upcoming_pending(monkeypatch, silent, heard):
    from tests.test_streaming import _pcm_seconds
    s = make_session(["الْحَمْدُ", "لِلَّهِ", "رَبِّ"])
    s._transcriber = lambda *_: ([], [])
    s._pcm = bytearray(_pcm_seconds(2, silent=silent))
    calls = []
    def recognize(*_):
        calls.append(True)
        return ss.ObservedTimedTranscript([heard] if heard else [], [.95] if heard else [],
                                          [(.1, .5)] if heard else [], [heard] if heard else [])
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_transcriber", recognize)
    assert await s.maybe_transcribe(force=True) == []
    assert s._matcher._cursor == 0
    if silent:
        assert calls == []


def test_unknown_or_weak_middle_token_is_not_confirmed_omission():
    for token, score in [("ضظذشش", .95), ("لله", .2)]:
        s = make_session(["الْحَمْدُ", "لِلَّهِ", "رَبِّ"])
        states = s._matcher.evaluate(["الحمد", token, "رب"], [.95, score, .95])
        events = s._diff_events(states)
        middle = next(e for e in events if e["word_index"] == 1)
        assert middle["evidence_confirmed"] is False
        assert middle["error_type"] is None and middle["display_color"] is None


def test_observed_known_wrong_word_emits_substituted_contract():
    s = make_session(["الْحَمْدُ", "لِلَّهِ", "رَبِّ"])
    states = s._matcher.evaluate(["الحمد", "الصمد", "رب"], [.95] * 3)
    middle = next(e for e in s._diff_events(states) if e["word_index"] == 1)
    assert middle["status"] == "error_skipped"
    assert middle["error_type"] == "substituted"
    assert middle["evidence_confirmed"] is True and middle["display_color"] == "#EF4444"


@pytest.mark.asyncio
async def test_native_lillah_rabb_omission_is_immediate_and_survives_window_loss(monkeypatch):
    from tests.test_streaming import _pcm_seconds
    s = make_session(["الْحَمْدُ", "لِلَّهِ", "رَبِّ", "الْعَالَمِينَ", "الرَّحْمَنِ"])
    s._transcriber = lambda *_: ([], [])
    replies = iter([
        ss.ObservedTimedTranscript(["الحمد"], [.95], [(.1, .3)], ["الْحَمْدُ"]),
        ss.ObservedTimedTranscript(["الحمد", "العالمين", "الرحمان"], [.95] * 3,
                                   [(.1, .3), (.8, 1.), (1.2, 1.5)],
                                   ["الْحَمْدُ", "الْعَالَمِينَ", "الرَّحْمَنِ"]),
    ])
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_transcriber", lambda *_: next(replies))
    s._pcm = bytearray(_pcm_seconds(2))
    await s.maybe_transcribe(force=True)
    # Existing bounded search opens only after the established stall count.
    s._matcher._delegate._stall_passes = 2
    s._pcm = bytearray(_pcm_seconds(3))
    events = await s.maybe_transcribe(force=True)
    missed = [e for e in events if e["error_type"] == "missed"]
    assert [e["word_index"] for e in missed] == [1, 2]
    assert all(e["evidence_confirmed"] for e in missed)
    s._last_native_view = None
    states = s._matcher._delegate._resolved_states
    assert not s._diff_events(states)
    assert all(s._supported_live_omission(st) for st in states if st.index in (1, 2))
    # An empty final independent decode must not discard the frozen omission
    # after its original bracketing window has gone away.
    monkeypatch.setattr(ss, "_independent_recording_transcriber", lambda *_: ([], []))
    monkeypatch.setattr(s, "_write_wav", lambda: None)
    async def no_persist(*_):
        pass
    monkeypatch.setattr(s, "_persist", no_persist)
    result = await s.finalize()
    missed = [v for v in result["word_verdicts"] if v["word_index"] in (1, 2)]
    assert len(missed) == 2
    assert all(v["error_type"] == "missed" and v["evidence_confirmed"] is True
               and v["display_color"] == "#EF4444" for v in missed)


def test_chunked_recording_keeps_raw_tokens_at_absolute_native_occurrences(monkeypatch):
    import numpy as np
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "FINAL_RECORDING_SINGLE_PASS_SEC", 1)
    monkeypatch.setattr(ss, "FINAL_RECORDING_CHUNK_SEC", 1)
    views = iter([
        ss.ObservedTimedTranscript(["انعمت"], [.93], [(.1, .5)], ["أَنْعَمْتُ"]),
        ss.ObservedTimedTranscript(["انعمت"], [.94], [(.2, .6)], ["أَنْعَمْتَ"]),
    ])
    monkeypatch.setattr(ss, "_independent_transcriber", lambda *_: next(views))
    decoded = ss._independent_recording_transcriber(np.full(32000, .2), 16000)
    assert decoded.raw_words == ["أَنْعَمْتُ", "أَنْعَمْتَ"]
    assert decoded.timings == [(.1, .5), (1.2, 1.6)]


@pytest.mark.asyncio
async def test_forced_stream_end_does_not_exempt_explicit_connected_middle_sukun(monkeypatch):
    from tests.test_streaming import _pcm_seconds
    s = make_session(["أَنْعَمْتَ", "عَلَيْهِمْ"])
    s._transcriber = lambda *_: ([], [])
    s._pcm = bytearray(_pcm_seconds(2))
    heard = ss.ObservedTimedTranscript(["انعمت", "عليهم"], [.95] * 2,
                                      [(.1, .5), (.6, 1.)], ["أَنْعَمْتْ", "عَلَيْهِمْ"])
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_transcriber", lambda *_: heard)
    events = await s.maybe_transcribe(force=True)
    assert events[0]["error_type"] == "harakat_mistake"


@pytest.mark.asyncio
async def test_forced_stream_end_is_not_a_pause_before_confirmed_substitution(monkeypatch):
    from tests.test_streaming import _pcm_seconds
    s = make_session(["أَنْعَمْتَ", "عَلَيْهِمْ", "غَيْرِ"])
    s._transcriber = lambda *_: ([], [])
    s._pcm = bytearray(_pcm_seconds(3))
    heard = ss.ObservedTimedTranscript(
        ["انعمت", "الصمد", "غير"], [.95] * 3,
        [(.1, .5), (.6, 1.), (1.1, 1.5)], ["أَنْعَمْتْ", "الصَّمَدُ", "غَيْرِ"],
    )
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_transcriber", lambda *_: heard)
    events = await s.maybe_transcribe(force=True)
    assert s._matcher._delegate._resolved_states[1].status.value == "error"
    assert events[0]["error_type"] == "harakat_mistake"
    assert s._matcher._cursor == 3


@pytest.mark.asyncio
async def test_final_only_end_context_keeps_native_substitution_slot(monkeypatch):
    from tests.test_streaming import _pcm_seconds
    s = make_session(["أَنْعَمْتَ", "عَلَيْهِمْ", "غَيْرِ"])
    s._pcm = bytearray(_pcm_seconds(3))
    heard = ss.ObservedTimedTranscript(
        ["قل", "انعمت", "الصمد", "غير"], [.95] * 4,
        [(0., .08), (.1, .5), (.6, 1.), (1.1, 1.5)],
        ["قُلْ", "أَنْعَمْتْ", "الصَّمَدُ", "غَيْرِ"],
    )
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    monkeypatch.setattr(ss, "EVIDENCE_POLICY", "tier2")
    monkeypatch.setattr(ss, "_independent_recording_transcriber", lambda *_: heard)
    monkeypatch.setattr(s, "_write_wav", lambda: None)
    async def no_persist(*_):
        pass
    monkeypatch.setattr(s, "_persist", no_persist)
    result = await s.finalize()
    assert [v["error_type"] for v in result["word_verdicts"]] == [
        "harakat_mistake", "substituted", None,
    ]
    assert result["word_verdicts"][0]["observed_text"] == "أَنْعَمْتْ"
    assert s._matcher._cursor == 0
