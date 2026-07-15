"""Unit tests for the Faster-Whisper (CT2) live transcriber.

These exercises run WITHOUT downloading the model: we monkeypatch the underlying
``faster_whisper.WhisperModel`` so the test asserts the transcriber's shaping
logic (word extraction, confidence passthrough, normalization hand-off) and the
singleton loader, not the actual ASR weights.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ml.inference.faster_whisper_transcriber import (
    FasterWhisperTranscriber,
    get_transcriber,
    resolve_model_dir,
)


class _FakeWord:
    def __init__(self, word: str, probability: float) -> None:
        self.word = word
        self.probability = probability


class _FakeSegment:
    def __init__(self, words) -> None:
        self.words = words


class _FakeModel:
    def __init__(self, *segments) -> None:
        self._segments = segments

    def transcribe(self, *args, **kwargs):
        return list(self._segments), MagicMock()


def _patch_model(fake: _FakeModel):
    """Patch the real ``faster_whisper.WhisperModel`` symbol with ``fake``."""
    return patch("faster_whisper.WhisperModel", return_value=fake)


def test_resolve_model_dir_env_override(monkeypatch):
    monkeypatch.setenv("QARI_FASTERWHISPER_MODEL_DIR", "/tmp/custom-ct2")
    assert resolve_model_dir() == "/tmp/custom-ct2"
    assert resolve_model_dir("/explicit") == "/explicit"


def test_transcribe_extracts_words_and_confidences():
    fake = _FakeModel(
        _FakeSegment([_FakeWord("بِسْمِ", 0.91), _FakeWord("اللَّهِ", 0.88)]),
        _FakeSegment([_FakeWord("الرَّحْمَنِ", 0.80)]),
    )
    tx = FasterWhisperTranscriber(model_dir="/tmp/model")
    with _patch_model(fake):
        tx.load()
        words, confs = tx.transcribe([0.0] * 1600, 16000)
    # Raw Arabic tokens are returned verbatim (normalization is the caller's job).
    assert words == ["بِسْمِ", "اللَّهِ", "الرَّحْمَنِ"]
    assert confs == [0.91, 0.88, 0.80]


def test_transcribe_empty_audio_returns_empty():
    tx = FasterWhisperTranscriber(model_dir="/tmp/model")
    with _patch_model(_FakeModel()):
        tx.load()
        words, confs = tx.transcribe([], 16000)
    assert words == []
    assert confs == []


def test_singleton_returns_same_instance():
    # Reset module-level singleton for a clean check.
    import ml.inference.faster_whisper_transcriber as m

    m._transcriber_singleton = None
    a = get_transcriber()
    b = get_transcriber()
    assert a is b
    m._transcriber_singleton = None
