"""Faster-Whisper CTranslate2 transcriber for live Quran recitation."""

from __future__ import annotations

import logging
import os
import threading
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = "/app/models/qari-ct2-tiny-robust-v2"
ENV_MODEL_DIR = "QARI_FASTERWHISPER_MODEL_DIR"


def resolve_model_dir(explicit: Optional[str] = None) -> str:
    return explicit or os.environ.get(ENV_MODEL_DIR, DEFAULT_MODEL_DIR)


def _word_probability(word) -> float:
    """Preserve a genuine 0.0 probability; only missing values default to 1."""
    value = getattr(word, "probability", None)
    return 1.0 if value is None else float(value)


class FasterWhisperTranscriber:
    """Thin, lazy and thread-safe wrapper around ``WhisperModel``."""

    def __init__(
        self,
        model_dir: Optional[str] = None,
        device: str = "cpu",
        compute_type: str = "int8",
        cpu_threads: Optional[int] = None,
    ) -> None:
        self.model_dir = resolve_model_dir(model_dir)
        self.device = device
        self.compute_type = compute_type
        self.cpu_threads = cpu_threads or max(1, (os.cpu_count() or 2) // 2)
        self._model = None
        self._lock = threading.Lock()

    def load(self) -> None:
        if self._model is not None:
            return
        if not os.path.isdir(self.model_dir):
            raise FileNotFoundError(
                f"CTranslate2 model directory does not exist: {self.model_dir}"
            )
        from faster_whisper import WhisperModel

        logger.info(
            "Loading Faster-Whisper (%s, %d threads) from %s",
            self.compute_type,
            self.cpu_threads,
            self.model_dir,
        )
        with self._lock:
            if self._model is None:
                self._model = WhisperModel(
                    self.model_dir,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=self.cpu_threads,
                )
        logger.info("Faster-Whisper model loaded")

    def is_loaded(self) -> bool:
        return self._model is not None

    @staticmethod
    def _prepare_audio(audio, sample_rate: int):
        import numpy as np

        if audio is None or len(audio) == 0:
            return np.asarray([], dtype=np.float32)
        samples = np.asarray(audio, dtype=np.float32)
        if sample_rate != 16000:
            import librosa

            samples = librosa.resample(
                samples, orig_sr=sample_rate, target_sr=16000
            ).astype(np.float32)
        return samples

    def _decode(self, samples):
        return self._model.transcribe(
            samples,
            language="ar",
            task="transcribe",
            beam_size=1,
            word_timestamps=True,
            vad_filter=False,
            temperature=0.0,
            condition_on_previous_text=False,
        )

    def transcribe(
        self, audio, sample_rate: int = 16000
    ) -> Tuple[List[str], List[float]]:
        self.load()
        samples = self._prepare_audio(audio, sample_rate)
        if len(samples) == 0:
            return [], []
        segments, _info = self._decode(samples)
        words: List[str] = []
        confidences: List[float] = []
        for segment in segments:
            for word in getattr(segment, "words", None) or []:
                text = (getattr(word, "word", None) or "").strip()
                if text:
                    words.append(text)
                    confidences.append(_word_probability(word))
        return words, confidences

    def transcribe_with_timings(
        self, audio, sample_rate: int = 16000
    ) -> Tuple[List[str], List[float], List[int], List[int]]:
        self.load()
        samples = self._prepare_audio(audio, sample_rate)
        if len(samples) == 0:
            return [], [], [], []
        segments, _info = self._decode(samples)
        words: List[str] = []
        confidences: List[float] = []
        starts: List[int] = []
        ends: List[int] = []
        for segment in segments:
            for word in getattr(segment, "words", None) or []:
                text = (getattr(word, "word", None) or "").strip()
                if not text:
                    continue
                words.append(text)
                confidences.append(_word_probability(word))
                starts.append(int(float(getattr(word, "start", 0.0) or 0.0) * 1000))
                ends.append(int(float(getattr(word, "end", 0.0) or 0.0) * 1000))
        return words, confidences, starts, ends


_transcriber_singleton: Optional[FasterWhisperTranscriber] = None
_transcriber_lock = threading.Lock()


def get_transcriber() -> FasterWhisperTranscriber:
    global _transcriber_singleton
    if _transcriber_singleton is None:
        with _transcriber_lock:
            if _transcriber_singleton is None:
                _transcriber_singleton = FasterWhisperTranscriber()
    return _transcriber_singleton
