"""
Recitation Pipeline — orchestrates the full analysis flow.

Steps:
  1. Capture: load/validate audio (mono 16kHz 16-bit PCM WAV, 60s max)
  2. VAD: trim silence, segment speech
  3. ASR: Whisper-Quran transcription → normalized tokens
  4. Word alignment: Levenshtein DP against reference → verdicts
  5. Forced alignment: Wav2Vec2-CTC → per-word timestamps
  6. Tajweed checks: ghunnah, qalqalah, madd, ikhfa, idgham
  7. Scoring: fluency + tajweed → overall
  8. Render: structured JSON result for UI
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Any

import numpy as np

from .inference.asr import QuranASR, ASRResult, normalize_arabic, tokenize_words
from .inference.vad import VoiceActivityDetector, VADResult
from .alignment.word_alignment import WordAligner, AlignmentResult, WordVerdict, AlignedWord
from .alignment.forced_alignment import ForcedAligner, ForcedAlignmentResult
from .tajweed.checks import TajweedChecker, TajweedCheckSummary, TajweedResult, TajweedVerdict
from .tajweed.reference_store import ReferenceStore, AyahReference
from .evaluation.scoring import compute_scores, ScoreBreakdown

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

MAX_DURATION_S = 60          # 60 second max recording
TARGET_SAMPLE_RATE = 16000   # 16kHz
TARGET_BITS = 16             # 16-bit


# ── Result data structures ───────────────────────────────────────────────────

@dataclass
class WordResult:
    """Per-word result for UI rendering."""
    word: str
    verdict: str
    reference: Optional[str]
    hypothesis: Optional[str]
    start_ms: int
    end_ms: int
    confidence: float
    similarity: float
    tajweed_issues: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "verdict": self.verdict,
            "reference": self.reference,
            "hypothesis": self.hypothesis,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "confidence": round(self.confidence, 3),
            "similarity": round(self.similarity, 3),
            "tajweed_issues": self.tajweed_issues,
        }


@dataclass
class RecitationResult:
    """Complete result of a recitation analysis."""
    session_id: str
    surah: int
    ayah: int
    scores: ScoreBreakdown
    words: list[WordResult] = field(default_factory=list)
    asr_text: str = ""
    reference_text: str = ""
    processing_time_s: float = 0.0
    audio_duration_s: float = 0.0
    reference_audio_url: str = ""
    user_audio_url: str = ""
    tajweed_summary: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "surah": self.surah,
            "ayah": self.ayah,
            "scores": self.scores.to_dict(),
            "words": [w.to_dict() for w in self.words],
            "asr_text": self.asr_text,
            "reference_text": self.reference_text,
            "processing_time_s": round(self.processing_time_s, 3),
            "audio_duration_s": round(self.audio_duration_s, 3),
            "reference_audio_url": self.reference_audio_url,
            "user_audio_url": self.user_audio_url,
            "tajweed_summary": self.tajweed_summary,
            "metadata": self.metadata,
        }

    def to_json(self, **kwargs: Any) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)


# ── Pipeline ─────────────────────────────────────────────────────────────────

class RecitationPipeline:
    """
    Full recitation analysis pipeline orchestrator.

    Coordinates ASR, VAD, word alignment, forced alignment, tajweed checks,
    and scoring to produce a complete RecitationResult.

    Parameters
    ----------
    reference_store : ReferenceStore
        Store of reference Quran data (expected words, phonemes, tajweed positions).
    asr : QuranASR, optional
        ASR engine. Created lazily if not provided.
    vad : VoiceActivityDetector, optional
        VAD instance. Created with defaults if not provided.
    forced_aligner : ForcedAligner, optional
        Forced aligner. Created lazily if not provided.
    tajweed_checker : TajweedChecker, optional
        Tajweed checker. Created with defaults if not provided.
    word_aligner : WordAligner, optional
        Word aligner. Created with defaults if not provided.
    lazy_load : bool, default True
        Whether to defer model loading until first use.
    """

    def __init__(
        self,
        reference_store: ReferenceStore,
        asr: Optional[QuranASR] = None,
        vad: Optional[VoiceActivityDetector] = None,
        forced_aligner: Optional[ForcedAligner] = None,
        tajweed_checker: Optional[TajweedChecker] = None,
        word_aligner: Optional[WordAligner] = None,
        lazy_load: bool = True,
    ) -> None:
        self.reference_store = reference_store
        self._asr = asr
        self._vad = vad or VoiceActivityDetector()
        self._forced_aligner = forced_aligner
        self._tajweed_checker = tajweed_checker or TajweedChecker()
        self._word_aligner = word_aligner or WordAligner()
        self._lazy_load = lazy_load

    @property
    def asr(self) -> QuranASR:
        if self._asr is None:
            self._asr = QuranASR()
            if not self._lazy_load:
                self._asr.load()
        return self._asr

    @property
    def forced_aligner(self) -> ForcedAligner:
        if self._forced_aligner is None:
            self._forced_aligner = ForcedAligner()
            if not self._lazy_load:
                self._forced_aligner.load()
        return self._forced_aligner

    def analyze(
        self,
        audio: np.ndarray,
        sample_rate: int,
        surah: int,
        ayah: int,
        session_id: str,
        *,
        user_audio_url: str = "",
    ) -> RecitationResult:
        """
        Run the full recitation analysis pipeline.

        Parameters
        ----------
        audio : np.ndarray
            Mono audio signal.
        sample_rate : int
            Audio sample rate (will be resampled to 16kHz if needed).
        surah : int
            Surah number (1-114).
        ayah : int
            Ayah number within the surah.
        session_id : str
            Unique session identifier.
        user_audio_url : str, optional
            URL to the user's uploaded audio clip.

        Returns
        -------
        RecitationResult
            Complete analysis result with scores, word verdicts, and tajweed checks.
        """
        t0 = time.perf_counter()

        # ── Step 1: Validate audio ────────────────────────────────────────────
        audio = self._validate_audio(audio, sample_rate)
        duration_s = len(audio) / TARGET_SAMPLE_RATE
        logger.info("Session %s: audio validated, %.1fs", session_id, duration_s)

        # ── Step 2: VAD ───────────────────────────────────────────────────────
        vad_result = self._vad.detect(audio, TARGET_SAMPLE_RATE)
        trimmed = vad_result.trimmed_audio
        if trimmed is not None and len(trimmed) > 0:
            analysis_audio = trimmed
        else:
            analysis_audio = audio
        logger.info("Session %s: VAD done, %d segments", session_id, len(vad_result.segments))

        # ── Step 3: Get reference ─────────────────────────────────────────────
        ref = self.reference_store.get(surah, ayah)
        if ref is None:
            raise ValueError(f"No reference data for surah {surah}, ayah {ayah}")
        reference_words = ref.expected_words
        reference_text = ref.normalized_text
        reference_audio_url = ref.reference_audio_url

        # ── Step 4: ASR ───────────────────────────────────────────────────────
        asr_result = self.asr.transcribe(analysis_audio, TARGET_SAMPLE_RATE)
        hypothesis_words = asr_result.normalized_words
        confidences = [t.confidence for t in asr_result.tokens]
        logger.info("Session %s: ASR done, %d words", session_id, len(hypothesis_words))

        # ── Step 5: Word alignment ────────────────────────────────────────────
        alignment = self._word_aligner.align(
            reference_words,
            hypothesis_words,
            confidences=confidences,
        )
        logger.info("Session %s: alignment done, %d correct", session_id, alignment.match_count)

        # ── Step 6: Forced alignment ──────────────────────────────────────────
        try:
            fa_result = self.forced_aligner.align(
                analysis_audio, reference_words, TARGET_SAMPLE_RATE
            )
            word_timestamps = fa_result.word_timestamps
        except Exception as e:
            logger.warning("Forced alignment failed: %s — using estimated timestamps", e)
            word_timestamps = self._estimate_timestamps(
                reference_words, len(analysis_audio) / TARGET_SAMPLE_RATE
            )

        # ── Step 7: Tajweed checks ────────────────────────────────────────────
        word_starts = [wt.start_ms for wt in word_timestamps]
        word_ends = [wt.end_ms for wt in word_timestamps]
        tajweed_positions = ref.tajweed_positions
        reference_phonemes = [w.phonemes for w in ref.words]

        tajweed_summary = self._tajweed_checker.check_all(
            analysis_audio,
            reference_words,
            word_starts,
            word_ends,
            reference_phonemes=reference_phonemes,
            tajweed_positions=tajweed_positions,
        )
        logger.info("Session %s: tajweed done, %d failures surfaced",
                     session_id, tajweed_summary.surfaced_failures)

        # ── Step 8: Scoring ───────────────────────────────────────────────────
        scores = compute_scores(alignment, tajweed_summary)

        # ── Step 9: Build word results ────────────────────────────────────────
        word_results = self._build_word_results(
            alignment, word_timestamps, tajweed_summary
        )

        elapsed = time.perf_counter() - t0

        return RecitationResult(
            session_id=session_id,
            surah=surah,
            ayah=ayah,
            scores=scores,
            words=word_results,
            asr_text=asr_result.raw_text,
            reference_text=reference_text,
            processing_time_s=elapsed,
            audio_duration_s=duration_s,
            reference_audio_url=reference_audio_url,
            user_audio_url=user_audio_url,
            tajweed_summary={
                "total_checks": tajweed_summary.total_checks,
                "passed": tajweed_summary.passed,
                "failed": tajweed_summary.failed,
                "surfaced_failures": tajweed_summary.surfaced_failures,
                "tajweed_score": round(tajweed_summary.tajweed_score, 2),
            },
            metadata={
                "vad_method": vad_result.method,
                "vad_speech_ratio": round(vad_result.speech_ratio, 3),
                "asr_model": asr_result.model_id,
                "asr_processing_s": round(asr_result.processing_time_s, 3),
            },
        )

    def analyze_from_file(
        self,
        wav_path: str | Path,
        surah: int,
        ayah: int,
        session_id: str,
        *,
        user_audio_url: str = "",
    ) -> RecitationResult:
        """
        Load a WAV file and run the full analysis pipeline.

        Parameters
        ----------
        wav_path : str or Path
            Path to the WAV file (mono 16kHz 16-bit PCM preferred).
        surah, ayah : int
            Quran reference.
        session_id : str
            Unique session ID.
        user_audio_url : str, optional
            URL to the uploaded audio.

        Returns
        -------
        RecitationResult
        """
        import soundfile as sf
        audio, sr = sf.read(str(wav_path), dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)  # Mix to mono
        return self.analyze(audio, sr, surah, ayah, session_id, user_audio_url=user_audio_url)

    def _validate_audio(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Validate and prepare audio: mono, 16kHz, within duration limit.

        Parameters
        ----------
        audio : np.ndarray
            Input audio.
        sample_rate : int
            Sample rate.

        Returns
        -------
        np.ndarray
            Validated mono 16kHz audio.
        """
        # Mix to mono
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Resample to 16kHz
        if sample_rate != TARGET_SAMPLE_RATE:
            import torchaudio
            import torch
            tensor = torch.from_numpy(audio).float()
            tensor = torchaudio.functional.resample(tensor, sample_rate, TARGET_SAMPLE_RATE)
            audio = tensor.numpy()

        # Check duration
        duration = len(audio) / TARGET_SAMPLE_RATE
        if duration > MAX_DURATION_S:
            max_samples = MAX_DURATION_S * TARGET_SAMPLE_RATE
            audio = audio[:max_samples]
            logger.warning("Audio truncated to %ds", MAX_DURATION_S)

        # Normalize to [-1, 1] if needed
        max_val = np.max(np.abs(audio))
        if max_val > 1.0:
            audio = audio / max_val

        return audio.astype(np.float32)

    def _estimate_timestamps(
        self, words: list[str], total_duration_s: float
    ) -> list:
        """Estimate uniform word timestamps when forced alignment is unavailable."""
        from .alignment.forced_alignment import WordTimestamp
        if not words:
            return []
        word_duration = (total_duration_s * 1000) / len(words)
        timestamps = []
        for i, word in enumerate(words):
            start_ms = int(i * word_duration)
            end_ms = int((i + 1) * word_duration)
            timestamps.append(WordTimestamp(
                word=word, start_ms=start_ms, end_ms=end_ms, score=0.5
            ))
        return timestamps

    def _build_word_results(
        self,
        alignment: AlignmentResult,
        word_timestamps: list,
        tajweed_summary: TajweedCheckSummary,
    ) -> list[WordResult]:
        """
        Build per-word result objects for UI rendering.

        Merges alignment verdicts, forced alignment timestamps, and
        tajweed check results into a unified per-word result.
        """
        # Group tajweed results by word index
        tajweed_by_word: dict[int, list[dict]] = {}
        for tr in tajweed_summary.results:
            if tr.word_index is not None and tr.should_surface:
                tajweed_by_word.setdefault(tr.word_index, []).append({
                    "rule": tr.check_type.value,
                    "verdict": tr.verdict.value,
                    "confidence": round(tr.confidence, 3),
                    "detail": tr.detail,
                    "measured_value": round(tr.measured_value, 1),
                    "expected_range": tr.expected_range,
                })

        word_results: list[WordResult] = []
        ref_word_idx = 0

        for i, aw in enumerate(alignment.aligned_words):
            # Find corresponding timestamp
            start_ms = 0
            end_ms = 0
            confidence = aw.confidence

            if aw.ref_index is not None and aw.ref_index < len(word_timestamps):
                wt = word_timestamps[aw.ref_index]
                start_ms = wt.start_ms
                end_ms = wt.end_ms
                confidence = (confidence + wt.score) / 2

            # Tajweed issues for this word
            tajweed_issues = tajweed_by_word.get(aw.ref_index, []) if aw.ref_index is not None else []

            word_results.append(WordResult(
                word=aw.reference or aw.hypothesis or "",
                verdict=aw.verdict.value,
                reference=aw.reference,
                hypothesis=aw.hypothesis,
                start_ms=start_ms,
                end_ms=end_ms,
                confidence=round(confidence, 3),
                similarity=round(aw.similarity, 3),
                tajweed_issues=tajweed_issues,
            ))

        return word_results
