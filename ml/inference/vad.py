"""
Voice Activity Detection (VAD) for recitation audio.

Provides silence trimming and segmentation using either Silero VAD
(preferred) or an RMS-energy gate fallback. Ensures that only speech
segments are sent to the ASR pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_FRAME_MS = 30                       # 30ms frames
DEFAULT_THRESHOLD = 0.5                     # VAD probability threshold (Silero)
DEFAULT_RMS_THRESHOLD_DB = -40.0            # RMS energy threshold (fallback)
DEFAULT_MIN_SPEECH_MS = 250                 # Min speech segment duration
DEFAULT_MIN_SILENCE_MS = 500               # Min silence to split segments
DEFAULT_SPEECH_PAD_MS = 100                 # Padding around speech segments


@dataclass
class VADSegment:
    """A detected speech segment with start/end times."""
    start_ms: int
    end_ms: int
    start_sample: int
    end_sample: int
    confidence: float = 1.0


@dataclass
class VADResult:
    """VAD processing result."""
    segments: list[VADSegment] = field(default_factory=list)
    total_speech_ms: int = 0
    total_duration_ms: int = 0
    trimmed_audio: Optional[np.ndarray] = None
    sample_rate: int = DEFAULT_SAMPLE_RATE
    method: str = "rms"  # "silero" or "rms"

    @property
    def speech_ratio(self) -> float:
        """Ratio of speech to total duration."""
        if self.total_duration_ms == 0:
            return 0.0
        return self.total_speech_ms / self.total_duration_ms


# ── VAD implementation ───────────────────────────────────────────────────────

class VoiceActivityDetector:
    """
    Voice Activity Detector for recitation audio.

    Uses Silero VAD when available (neural network based, high accuracy),
    falls back to RMS energy gate for environments without torch/torchhub access.

    Parameters
    ----------
    sample_rate : int, default 16000
        Expected audio sample rate.
    threshold : float, default 0.5
        VAD probability threshold (Silero) or energy threshold (RMS).
    min_speech_ms : int, default 250
        Minimum duration of a speech segment to keep.
    min_silence_ms : int, default 500
        Minimum silence duration to split segments.
    speech_pad_ms : int, default 100
        Padding added around each speech segment.
    use_silero : bool, default True
        Whether to attempt Silero VAD first.
    """

    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        threshold: float = DEFAULT_THRESHOLD,
        min_speech_ms: int = DEFAULT_MIN_SPEECH_MS,
        min_silence_ms: int = DEFAULT_MIN_SILENCE_MS,
        speech_pad_ms: int = DEFAULT_SPEECH_PAD_MS,
        use_silero: bool = True,
    ) -> None:
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_ms = min_speech_ms
        self.min_silence_ms = min_silence_ms
        self.speech_pad_ms = speech_pad_ms
        self.use_silero = use_silero

        self._silero_model = None
        self._silero_utils = None
        self._silero_loaded = False

    def _load_silero(self) -> bool:
        """Attempt to load Silero VAD model from torch.hub."""
        if self._silero_loaded:
            return True
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                trust_repo=True,
            )
            self._silero_model = model
            self._silero_utils = utils
            self._silero_loaded = True
            logger.info("Silero VAD loaded successfully")
            return True
        except Exception as e:
            logger.warning("Could not load Silero VAD, falling back to RMS: %s", e)
            return False

    def detect(
        self,
        audio: np.ndarray,
        sample_rate: Optional[int] = None,
    ) -> VADResult:
        """
        Detect speech segments in audio.

        Parameters
        ----------
        audio : np.ndarray
            Mono audio signal. Shape: (n_samples,).
        sample_rate : int, optional
            Override sample rate. Defaults to self.sample_rate.

        Returns
        -------
        VADResult
            Detected speech segments and trimmed audio.
        """
        sr = sample_rate or self.sample_rate
        if audio.ndim > 1:
            audio = audio.mean(axis=0)  # Mix to mono

        total_ms = int(len(audio) / sr * 1000)

        if self.use_silero and self._load_silero():
            result = self._detect_silero(audio, sr)
        else:
            result = self._detect_rms(audio, sr)

        result.total_duration_ms = total_ms
        result.sample_rate = sr

        # Build trimmed audio from segments
        if result.segments:
            chunks = [audio[s.start_sample:s.end_sample] for s in result.segments]
            result.trimmed_audio = np.concatenate(chunks) if chunks else np.array([])
        else:
            result.trimmed_audio = np.array([])

        return result

    def _detect_silero(self, audio: np.ndarray, sr: int) -> VADResult:
        """Run Silero VAD detection."""
        import torch

        model = self._silero_model
        get_speech_timestamps = self._silero_utils[0]  # get_speech_timestamps

        # Silero expects 16kHz
        if sr != 16000:
            import torchaudio
            tensor = torch.from_numpy(audio).float()
            tensor = torchaudio.functional.resample(tensor, sr, 16000)
            audio = tensor.numpy()
            sr = 16000

        t = torch.from_numpy(audio).float()

        speech_timestamps = get_speech_timestamps(
            t,
            model,
            threshold=self.threshold,
            sampling_rate=sr,
            min_speech_duration_ms=self.min_speech_ms,
            min_silence_duration_ms=self.min_silence_ms,
            speech_pad_ms=self.speech_pad_ms,
            return_seconds=False,
        )

        segments: list[VADSegment] = []
        total_speech = 0
        for ts in speech_timestamps:
            start_s = ts["start"]
            end_s = ts["end"]
            start_ms = int(start_s / sr * 1000)
            end_ms = int(end_s / sr * 1000)
            segments.append(VADSegment(
                start_ms=start_ms,
                end_ms=end_ms,
                start_sample=start_s,
                end_sample=end_s,
                confidence=0.95,
            ))
            total_speech += end_ms - start_ms

        return VADResult(
            segments=segments,
            total_speech_ms=total_speech,
            method="silero",
        )

    def _detect_rms(self, audio: np.ndarray, sr: int) -> VADResult:
        """
        RMS energy-based VAD fallback.

        Computes frame-level RMS energy, converts to dB, and marks frames
        above threshold as speech. Applies minimum duration and merging.
        """
        frame_samples = int(sr * DEFAULT_FRAME_MS / 1000)
        hop_samples = frame_samples // 2  # 50% overlap

        if len(audio) < frame_samples:
            return VADResult(segments=[], method="rms")

        # Compute RMS energy per frame
        n_frames = max(1, (len(audio) - frame_samples) // hop_samples + 1)
        rms_db = np.zeros(n_frames)

        for i in range(n_frames):
            start = i * hop_samples
            end = start + frame_samples
            frame = audio[start:end]
            rms = np.sqrt(np.mean(frame.astype(np.float64) ** 2) + 1e-10)
            rms_db[i] = 20 * np.log10(rms + 1e-10)

        # Threshold frames
        is_speech = rms_db > DEFAULT_RMS_THRESHOLD_DB

        # Convert frame-level to segments
        frame_ms = DEFAULT_FRAME_MS
        hop_ms = int(hop_samples / sr * 1000)

        segments: list[VADSegment] = []
        in_speech = False
        seg_start_frame = 0

        for i, speech in enumerate(is_speech):
            if speech and not in_speech:
                in_speech = True
                seg_start_frame = i
            elif not speech and in_speech:
                in_speech = False
                self._add_segment(
                    segments, seg_start_frame, i - 1, hop_ms, frame_ms, sr, len(audio)
                )

        # Handle trailing speech
        if in_speech:
            self._add_segment(
                segments, seg_start_frame, n_frames - 1, hop_ms, frame_ms, sr, len(audio)
            )

        # Merge segments separated by short silence
        segments = self._merge_close_segments(segments)

        # Filter by minimum duration
        segments = [s for s in segments if (s.end_ms - s.start_ms) >= self.min_speech_ms]

        total_speech = sum(s.end_ms - s.start_ms for s in segments)

        return VADResult(
            segments=segments,
            total_speech_ms=total_speech,
            method="rms",
        )

    def _add_segment(
        self,
        segments: list[VADSegment],
        start_frame: int,
        end_frame: int,
        hop_ms: int,
        frame_ms: int,
        sr: int,
        n_samples: int,
    ) -> None:
        """Convert frame indices to a VADSegment and add to list."""
        start_ms = start_frame * hop_ms
        end_ms = end_frame * hop_ms + frame_ms
        start_sample = min(start_frame * hop_ms * sr // 1000, n_samples)
        end_sample = min(end_ms * sr // 1000, n_samples)

        # Add padding
        pad_samples = int(self.speech_pad_ms * sr / 1000)
        start_sample = max(0, start_sample - pad_samples)
        end_sample = min(n_samples, end_sample + pad_samples)
        start_ms = int(start_sample / sr * 1000)
        end_ms = int(end_sample / sr * 1000)

        segments.append(VADSegment(
            start_ms=start_ms,
            end_ms=end_ms,
            start_sample=start_sample,
            end_sample=end_sample,
            confidence=0.80,
        ))

    def _merge_close_segments(self, segments: list[VADSegment]) -> list[VADSegment]:
        """Merge segments separated by silence shorter than min_silence_ms."""
        if len(segments) <= 1:
            return segments

        merged: list[VADSegment] = [segments[0]]
        for seg in segments[1:]:
            prev = merged[-1]
            gap = seg.start_ms - prev.end_ms
            if gap < self.min_silence_ms:
                # Merge
                prev.end_ms = seg.end_ms
                prev.end_sample = seg.end_sample
            else:
                merged.append(seg)

        return merged

    def trim_silence(self, audio: np.ndarray, sample_rate: Optional[int] = None) -> np.ndarray:
        """
        Convenience: detect speech and return only the speech portions.

        Parameters
        ----------
        audio : np.ndarray
            Input audio.
        sample_rate : int, optional
            Sample rate override.

        Returns
        -------
        np.ndarray
            Audio with leading/trailing silence removed.
        """
        result = self.detect(audio, sample_rate)
        return result.trimmed_audio if result.trimmed_audio is not None and len(result.trimmed_audio) > 0 else audio
