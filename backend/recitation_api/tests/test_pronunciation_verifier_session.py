"""The v3 pronunciation model only adds confident red marks to heard words."""
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

    def score(self, window, phonemes):
        self.calls.append((len(window), list(phonemes)))
        return VerifierResult([.9 if p in self.bad else .1 for p in phonemes], self.threshold)


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
