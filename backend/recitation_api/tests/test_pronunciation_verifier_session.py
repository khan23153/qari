"""The v3 pronunciation model runs in shadow mode unless qualified; when
qualified it only adds confident red marks to heard words."""
import struct
import types

import pytest

from app.services import streaming_session as ss
from ml.inference.pronunciation_verifier import VerifierResult


def session(words, spans, ayahs):
    s = ss.StreamingRecitationSession()
    s._is_stub = False
    s.sample_rate = 16000
    s._pcm = bytearray(struct.pack("<" + "h" * 16000 * 6, *([0] * 16000 * 6)))
    s.word_entries = [{"text_with_tashkeel": w} for w in words]
    s.ayah_boundaries = ayahs
    for i, span in enumerate(spans):
        if span:
            s._heard_word_evidence[i] = {"span": span, "raw": words[i], "expected": words[i]}
    return s


def matched(*indices):
    return [types.SimpleNamespace(index=i, status=types.SimpleNamespace(value="matched")) for i in indices]


class FakeVerifier:
    """Gives each word one phoneme named after it; ``bad`` words score high."""

    def __init__(self, bad, threshold=.35):
        self.bad, self.threshold, self.calls = bad, threshold, []

    def fingerprint(self, extra=()):
        self.extra = extra
        return "f" * 64

    def score(self, window, phonemes):
        self.calls.append((len(window), list(phonemes)))
        return VerifierResult([.9 if p in self.bad else .1 for p in phonemes], self.threshold)


@pytest.fixture(autouse=True)
def qualified(monkeypatch):
    """Most tests exercise the marking logic of a qualified model."""
    ss._pron_verifier_state.clear()
    monkeypatch.setattr(ss, "_pron_verifier_qualified", lambda v: True)


@pytest.fixture
def one_phoneme_per_word(monkeypatch):
    import ml.alignment.quran_g2p as g
    monkeypatch.setattr(g, "ayah_word_phonemes", lambda s, a: None)
    monkeypatch.setattr(g, "phonemize_words", lambda words, **_: [[w] for w in words])


def test_confident_model_marks_only_that_word(one_phoneme_per_word):
    words = ["بِسْمِ", "اللَّهِ", "الرَّحْمَنِ", "الرَّحِيمِ"]
    s = session(words, [(.1, .5), (.6, 1.0), (1.1, 1.8), (1.9, 2.5)],
                [{"surah": 1, "ayah": 1, "word_index_end": 3}])
    v = FakeVerifier(bad={"الرَّحْمَنِ"})
    s._observe_pronunciation(matched(0, 1, 2, 3), verifier=v)
    assert list(s._pron_errors) == [2]
    assert s._pron_errors[2]["source"] == "pronunciation_model"
    assert len(v.calls) == 1 and v.calls[0][1] == words  # one window for the ayah


def test_words_without_heard_spans_or_already_red_are_left_alone(one_phoneme_per_word):
    words = ["إِيَّاكَ", "نَعْبُدُ", "وَإِيَّاكَ", "نَسْتَعِينُ"]
    s = session(words, [(.1, .5), None, (1.1, 1.6), (1.7, 2.4)],
                [{"surah": 1, "ayah": 5, "word_index_end": 3}])
    s._harakat_errors[2] = {"raw": "x", "expected": words[2], "confidence": .9, "conflicts": []}
    v = FakeVerifier(bad=set(words))
    s._observe_pronunciation(matched(0, 1, 2, 3), verifier=v)
    assert sorted(s._pron_errors) == [0, 3]


def test_each_ayah_is_its_own_window(one_phoneme_per_word):
    words = ["قُلْ", "هُوَ", "اللَّهُ", "أَحَدٌ", "اللَّهُ", "الصَّمَدُ"]
    s = session(words, [(.1, .3), (.4, .6), (.7, 1.0), (1.1, 1.5), (2.0, 2.4), (2.5, 3.1)],
                [{"surah": 112, "ayah": 1, "word_index_end": 3}, {"surah": 112, "ayah": 2, "word_index_end": 5}])
    v = FakeVerifier(bad=set())
    s._observe_pronunciation(matched(*range(6)), verifier=v)
    assert [c[1] for c in v.calls] == [words[:4], words[4:]]
    assert not s._pron_errors


def test_below_threshold_is_not_a_mistake(one_phoneme_per_word):
    s = session(["رَبِّ"], [(.1, .6)], [{"surah": 1, "ayah": 2, "word_index_end": 0}])
    s._observe_pronunciation(matched(0), verifier=FakeVerifier(bad={"رَبِّ"}, threshold=.95))
    assert not s._pron_errors


def test_disabled_without_a_model(monkeypatch):
    monkeypatch.setattr(ss, "PRON_VERIFIER_DIR", "")
    s = session(["رَبِّ"], [(.1, .6)], [{"surah": 1, "ayah": 2, "word_index_end": 0}])
    s._observe_pronunciation(matched(0))
    assert not s._pron_errors


def test_lexicon_phonemes_are_used_for_known_ayahs():
    words = ["بِسْمِ", "اللَّهِ", "الرَّحْمَنِ", "الرَّحِيمِ"]
    s = session(words, [(.1, .5), (.6, 1.0), (1.1, 1.8), (1.9, 2.5)],
                [{"surah": 1, "ayah": 1, "word_index_end": 3}])
    v = FakeVerifier(bad=set())
    s._observe_pronunciation(matched(1, 2), verifier=v)
    assert v.calls[0][1] == ["ll", "a", "h", "i", "rr", "a", "H", "m", "a", "n", "i"]


def test_unqualified_model_is_shadow_only(monkeypatch, one_phoneme_per_word):
    monkeypatch.setattr(ss, "_pron_verifier_qualified", lambda v: False)
    words = ["بِسْمِ", "اللَّهِ"]
    s = session(words, [(.1, .5), (.6, 1.0)], [{"surah": 1, "ayah": 1, "word_index_end": 1}])
    s._observe_pronunciation(matched(0, 1), verifier=FakeVerifier(bad={"اللَّهِ"}))
    assert not s._pron_errors  # nothing shown to the user
    shadow = s._pron_shadow
    assert shadow["qualified"] is False and shadow["model_sha256"] == "f" * 64
    assert [(w["word_index"], w["flagged"]) for w in shadow["words"]] == [(0, False), (1, True)]
    assert shadow["words"][1]["audio_span_ms"] == [600, 1000]


def _gate(monkeypatch, tmp_path, report, verdict):
    path = tmp_path / "report.json"
    path.write_text(__import__("json").dumps(report))
    monkeypatch.undo()  # drop the autouse "qualified" override
    ss._pron_verifier_state.clear()
    monkeypatch.setattr(ss, "PRON_VERIFIER_REPORT", str(path))
    seen = []
    import ml.evaluation.pronunciation as pron
    monkeypatch.setattr(pron, "qualified_for_model", lambda r, sha: seen.append((r, sha)) or verdict)
    return seen


def test_report_must_qualify_this_exact_fingerprint(monkeypatch, tmp_path):
    seen = _gate(monkeypatch, tmp_path, {"qualified": True}, True)
    v = FakeVerifier(bad=set())
    assert ss._pron_verifier_qualified(v) is True
    assert seen == [({"qualified": True}, "f" * 64)]
    # the session's own windowing / word-folding code is part of the fingerprint
    assert "def _observe_pronunciation" in v.extra[0]


def test_failing_report_keeps_shadow(monkeypatch, tmp_path):
    _gate(monkeypatch, tmp_path, {"qualified": False}, False)
    assert ss._pron_verifier_qualified(FakeVerifier(bad=set())) is False


def test_no_report_means_shadow(monkeypatch):
    monkeypatch.undo()
    ss._pron_verifier_state.clear()
    monkeypatch.setattr(ss, "PRON_VERIFIER_REPORT", "")
    assert ss._pron_verifier_qualified(FakeVerifier(bad=set())) is False


def test_real_gate_rejects_v3_numbers():
    """The shipped policy itself refuses a report with v3's QuranMB.v2 numbers."""
    from ml.evaluation.pronunciation import qualified_for_model
    assert not qualified_for_model({"schema_version": 1, "scope": "phonemic_pronunciation",
                                    "model_sha256": "f" * 64, "qualified": False,
                                    "precision": .82, "recall": .44}, "f" * 64)


def test_shadow_run_drops_work_when_model_busy(monkeypatch, one_phoneme_per_word):
    monkeypatch.setattr(ss, "_pron_verifier_qualified", lambda v: False)
    s = session(["رَبِّ"], [(.1, .6)], [{"surah": 1, "ayah": 2, "word_index_end": 0}])
    v = FakeVerifier(bad={"رَبِّ"})
    with ss._PRON_LOCK:
        s._shadow_pronunciation(matched(0), verifier=v)
    assert v.calls == [] and not s._pron_shadow


def test_shadow_run_scores_but_never_marks(monkeypatch, one_phoneme_per_word):
    monkeypatch.setattr(ss, "_pron_verifier_qualified", lambda v: False)
    s = session(["رَبِّ"], [(.1, .6)], [{"surah": 1, "ayah": 2, "word_index_end": 0}])
    s._shadow_pronunciation(matched(0), verifier=FakeVerifier(bad={"رَبِّ"}))
    assert not s._pron_errors
    assert s._pron_shadow["words"][0]["flagged"] is True
    assert not ss._PRON_LOCK.locked()
