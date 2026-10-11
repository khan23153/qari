"""Optional independent Arabic FastConformer PCD RNNT recognition.

The decoder never receives expected text. Only complete native token scores
and timestamps can produce evidence; failures raise instead of substituting a
prompted model or inventing confidence. Sherpa and NumPy remain lazy imports.
"""

from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import threading

from .transcript import TimedTranscript


DEFAULT_MODEL_DIR = '/app/models/qari-fastconformer-pcd-rnnt-int8'
# Synthesium/quran-recitation-v2-onnx at
# a57907844f7c72969b40bc526a57e9c9dbc8bf3f. These hashes identify NVIDIA's PCD
# export, whose encoder metadata names stt_ar_fastconformer_hybrid_large_pcd_v1.0.
# Validating identity avoids an optional ONNX parser dependency and prevents
# accidentally loading the similarly named plain-PC model.
MODEL_SHA256 = {
    'encoder.int8.onnx': '583d152c5bfd7dbfaa573319043fed4f1ef448add3f769d31b3dddf31e4e533f',
    'decoder.int8.onnx': '9ee2286747a5bd5cfeb1808af7eca42a763cd057e1ebb78cb3cb93a48e559a90',
    'joiner.int8.onnx': '5015e28f1ea3b8b56d25212a69629d7e49d750ce2a56d181dbd53a23b3b5dec2',
    'tokens.txt': '9b938381a19a69bb279cdcfc299419f25a049ea1de192e0d10317274a0f20074',
}


def resolve_model_dir(model_dir: str | None = None) -> str:
    return model_dir or os.environ.get('QARI_FASTCONFORMER_MODEL_DIR') or DEFAULT_MODEL_DIR


def decode_result(result) -> TimedTranscript:
    """Group native BPE tokens without changing posterior scores or times."""
    try:
        tokens = list(result.tokens)
        scores = list(result.ys_log_probs)
        timestamps = list(result.timestamps)
    except (AttributeError, TypeError) as exc:
        raise ValueError('RNNT result lacks complete token evidence') from exc
    if not len(tokens) == len(scores) == len(timestamps):
        raise ValueError('RNNT tokens, log probabilities and timestamps must align')

    validated = []
    previous_time = 0.0
    for token, score, timestamp in zip(tokens, scores, timestamps):
        try:
            log_probability = float(score)
            stamp = float(timestamp)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('Invalid RNNT score or timestamp') from exc
        if not isinstance(token, str):
            raise ValueError('Invalid RNNT token')
        if not math.isfinite(log_probability) or log_probability > 0.0:
            raise ValueError('RNNT log probability must be finite and nonpositive')
        if not math.isfinite(stamp) or stamp < previous_time:
            raise ValueError('RNNT timestamps must be finite, nonnegative and monotonic')
        previous_time = stamp
        validated.append((token, log_probability, stamp))

    words: list[str] = []
    confidences: list[float] = []
    timings: list[tuple[float, float]] = []
    pieces: list[str] = []
    log_parts: list[float] = []
    time_parts: list[float] = []

    def flush() -> None:
        if pieces:
            probability = math.exp(sum(log_parts) / len(log_parts))
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                raise ValueError('Invalid RNNT word probability')
            words.append(''.join(pieces))
            confidences.append(probability)
            timings.append((min(time_parts), max(time_parts)))
        pieces.clear()
        log_parts.clear()
        time_parts.clear()

    for token, score, stamp in validated:
        for index, piece in enumerate(token.replace('▁', ' ').split(' ')):
            if index:
                flush()
            if piece:
                pieces.append(piece)
                log_parts.append(score)
                time_parts.append(stamp)
    flush()
    return TimedTranscript(words, confidences, timings)


class FastConformerTranscriber:
    """One lazily loaded RNNT decoder, serialized across worker threads."""

    def __init__(self, model_dir: str | None = None) -> None:
        self.model_dir = resolve_model_dir(model_dir)
        self._recognizer = None
        self._lock = threading.RLock()

    def load(self) -> None:
        with self._lock:
            if self._recognizer is not None:
                return
            directory = Path(self.model_dir)
            for filename, expected in MODEL_SHA256.items():
                with (directory / filename).open('rb') as asset:
                    actual = hashlib.file_digest(asset, 'sha256').hexdigest()
                if actual != expected:
                    raise ValueError(f'Unpinned or corrupt FastConformer asset: {filename}')
            import sherpa_onnx

            self._recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                encoder=str(directory / 'encoder.int8.onnx'),
                decoder=str(directory / 'decoder.int8.onnx'),
                joiner=str(directory / 'joiner.int8.onnx'),
                tokens=str(directory / 'tokens.txt'),
                num_threads=2,
                sample_rate=16000,
                feature_dim=80,
                decoding_method='greedy_search',
                model_type='nemo_transducer',
            )

    def transcribe(self, audio, sample_rate: int = 16000) -> TimedTranscript:
        """Decode normalized mono PCM as-is; accept no reference/prompt input."""
        if sample_rate != 16000 or audio is None:
            raise ValueError('FastConformer requires 16000 Hz mono float PCM')
        import numpy as np

        try:
            samples = np.asarray(audio, dtype=np.float32)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('Invalid mono float PCM') from exc
        if samples.ndim != 1 or not np.isfinite(samples).all():
            raise ValueError('PCM must be one-dimensional and finite')
        if samples.size and (samples.min() < -1.0 or samples.max() > 1.0):
            raise ValueError('Float PCM must be within [-1, 1]')
        if not samples.size:
            return TimedTranscript([], [], [])
        with self._lock:
            self.load()
            stream = self._recognizer.create_stream()
            stream.accept_waveform(sample_rate, samples)
            self._recognizer.decode_stream(stream)
            return decode_result(stream.result)


_transcriber_singleton: FastConformerTranscriber | None = None
_singleton_lock = threading.Lock()


def get_transcriber() -> FastConformerTranscriber:
    global _transcriber_singleton
    with _singleton_lock:
        if _transcriber_singleton is None:
            _transcriber_singleton = FastConformerTranscriber()
        return _transcriber_singleton
