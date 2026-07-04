"""Inference sub-package: ASR transcription and voice activity detection."""

from .asr import QuranASR, ASRResult
from .vad import VoiceActivityDetector, VADResult

__all__ = ["QuranASR", "ASRResult", "VoiceActivityDetector", "VADResult"]
