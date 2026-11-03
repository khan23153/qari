"""The pronunciation model never runs in the live server unless qualified by a
trusted evaluation bundle; when qualified it only adds confident red marks to
heard words. Unqualified research scoring is offline (export only here).

These tests use a fake model: they check the plumbing, not what the model hears."""
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
def fresh_state():
    ss._pron_verifier_state.clear()


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


class CountingVerifier(FakeVerifier):
    def __init__(self):
        super().__init__(bad=set())
        self.loads = 0
        self.loaded = False

    def load(self):
        self.loads += 1
        self.loaded = True
        return self


def test_unqualified_model_is_never_loaded_or_scored(monkeypatch, one_phoneme_per_word):
    v = CountingVerifier()
    monkeypatch.setattr(ss, "_pron_verifier_instance", lambda: v)
    monkeypatch.setattr(ss, "_pron_verifier_qualified", lambda verifier: False)
    s = session(["رَبِّ"], [(.1, .6)], [{"surah": 1, "ayah": 2, "word_index_end": 0}])
    s._qualified_pronunciation(matched(0))
    assert v.loads == 0 and v.calls == [] and not s._pron_errors and not s._pron_assessed


def test_qualified_model_marks_and_reports_assessed(monkeypatch, one_phoneme_per_word):
    v = CountingVerifier()
    v.bad = {"رَبِّ"}
    monkeypatch.setattr(ss, "_pron_verifier_instance", lambda: v)
    monkeypatch.setattr(ss, "_get_pron_verifier", lambda: v.load())
    monkeypatch.setattr(ss, "_pron_verifier_qualified", lambda verifier: True)
    s = session(["رَبِّ", "الْعَالَمِينَ"], [(.1, .6), (.7, 1.4)], [{"surah": 1, "ayah": 2, "word_index_end": 1}])
    s._qualified_pronunciation(matched(0, 1))
    assert list(s._pron_errors) == [0] and s._pron_assessed == {0, 1}
    assert not ss._PRON_LOCK.locked()


def test_export_writes_worker_inputs_without_a_model(monkeypatch, tmp_path, one_phoneme_per_word):
    import json
    monkeypatch.setattr(ss.settings, "audio_storage_path", str(tmp_path))
    words = ["بِسْمِ", "اللَّهِ"]
    s = session(words, [(.1, .5), (.6, 1.0)], [{"surah": 1, "ayah": 1, "word_index_end": 1}])
    path = s._export_pronunciation_inputs(matched(0, 1))
    data = json.loads(open(path).read())
    run = data["runs"][0]
    assert run["word_indices"] == [0, 1] and run["phonemes"] == [[w] for w in words]
    assert run["window"] == [0.0, 1.35] and (run["surah"], run["ayah"]) == (1, 1)


def test_qualification_uses_trusted_bundle_and_pipeline_fingerprint(monkeypatch):
    seen = []
    import ml.evaluation.pronunciation as pron
    monkeypatch.setattr(ss, "PRON_VERIFIER_REPORT", "/bundle")
    monkeypatch.setattr(pron, "verify_evaluation_bundle", lambda path, sha: seen.append((path, sha)) or (True, "ok"))
    v = FakeVerifier(bad=set())
    assert ss._pron_verifier_qualified(v) is True
    assert seen == [("/bundle", "f" * 64)]
    assert any("def _observe_pronunciation" in src for src in v.extra)
    assert any("def _pronunciation_runs" in src for src in v.extra)


def test_no_bundle_means_off(monkeypatch):
    monkeypatch.setattr(ss, "PRON_VERIFIER_REPORT", "")
    assert ss._pron_verifier_qualified(FakeVerifier(bad=set())) is False
