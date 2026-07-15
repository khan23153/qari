"""Faster-Whisper (CTranslate2, INT8) transcriber for real-time CPU recitation.

This replaces the heavy transformers/PyTorch Whisper on the **live streaming**
path. ``faster-whisper`` runs the CTranslate2 runtime, which is ~2–4x faster on
CPU than vanilla PyTorch Whisper and, with **INT8 quantization**, halves memory
footprint — so the live recitation engine can track a user's voice in near
real-time on a standard CPU-only VPS (the latency ceiling the default PyTorch
engine cannot meet).

ASR model
---------
``tarteel-ai/whisper-tiny-ar-quran`` — a Whisper-tiny variant fine-tuned by
Tarteel specifically on Quranic Arabic recitation (NOT conversational Arabic).
It must be **converted to the CTranslate2 format** before use:

    ct2-transformers-converter \\
        --model tarteel-ai/whisper-tiny-ar-quran \\
        --output_dir tarteel-ct2-tiny --quantization int8

See ``scripts/convert_tarteel_model.py`` for a one-command helper. The resulting
folder is mounted into the container at ``/app/models/tarteel-ct2-tiny`` and its
location is overridable via ``QARI_FASTERWHISPER_MODEL_DIR``.

The transcriber returns **raw** Arabic word tokens (not yet normalized). The
caller (``streaming_session._real_transcriber``) normalizes them with the exact
same ``_normalize`` used for the reference words so the ``StreamingMatcher`` can
compare hypothesis ↔ reference consistently.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default location of the converted CTranslate2 model inside the container.
# Override with the QARI_FASTERWHISPER_MODEL_DIR environment variable.
DEFAULT_MODEL_DIR = "/app/models/tarteel-ct2-tiny"
ENV_MODEL_DIR = "QARI_FASTERWHISPER_MODEL_DIR"


def resolve_model_dir(explicit: Optional[str] = None) -> str:
    """Resolve the CT2 model directory: explicit arg > env > default."""
    return explicit or os.environ.get(ENV_MODEL_DIR, DEFAULT_MODEL_DIR)


class FasterWhisperTranscriber:
    """Thin wrapper around ``faster_whisper.WhisperModel`` (lazy, thread-safe)."""

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
        """Load the CT2 model into memory (idempotent, thread-safe)."""
        if self._model is not None:
            return
        from faster_whisper import WhisperModel

        logger.info(
            "Loading Faster-Whisper (CT2 %s, %d threads) from %s",
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
        logger.info("Faster-Whisper model loaded.")

    def is_loaded(self) -> bool:
        return self._model is not None

    def transcribe(
        self, audio, sample_rate: int = 16000
    ) -> Tuple[List[str], List[float]]:
        """Transcribe a mono float32 signal and return ``(words, confidences)``.

        Words are the **raw** Arabic tokens (whitespace-split from word-level
        timestamps). Normalization is left to the caller so it can reuse the
        reference-word normalizer. Returns ``([], [])`` for empty / silent input.
        """
        import numpy as np

        self.load()
        if audio is None or len(audio) == 0:
            return [], []

        samples = np.asarray(audio, dtype=np.float32)
        if samples.dtype != np.float32:
            samples = samples.astype(np.float32)

        if sample_rate != 16000:
            try:
                import librosa

                samples = librosa.resample(
                    samples, orig_sr=sample_rate, target_sr=16000
                )
            except Exception as exc:  # pragma: no cover - resample edge case
                logger.warning("fw.resample_failed", error=str(exc))

        segments, _info = self._model.transcribe(
            samples,
            language="ar",
            task="transcribe",
            beam_size=1,
            word_timestamps=True,
            vad_filter=False,
            temperature=0.0,
            condition_on_previous_text=False,
        )

        words: List[str] = []
        confs: List[float] = []
        for seg in segments:
            for w in getattr(seg, "words", None) or []:
                text = (getattr(w, "word", None) or "").strip()
                if text:
                    words.append(text)
                    confs.append(float(getattr(w, "probability", 1.0) or 1.0))
        return words, confs


_transcriber_singleton: Optional[FasterWhisperTranscriber] = None
_transcriber_lock = threading.Lock()


def get_transcriber() -> FasterWhisperTranscriber:
    """Process-wide singleton (avoids re-loading the model per session)."""
    global _transcriber_singleton
    if _transcriber_singleton is None:
        with _transcriber_lock:
            if _transcriber_singleton is None:
                _transcriber_singleton = FasterWhisperTranscriber()
    return _transcriber_singleton
