"""Fast production worker for uploaded Quran recitation analysis.

The original research pipeline lazily downloads/loads Hugging Face Whisper,
Silero VAD and a Wav2Vec2 forced aligner. On a CPU VPS that can take several
minutes (or stall completely when outbound model downloads are unavailable),
while the mobile client gives up polling after two minutes.

This worker keeps the same Redis job/result contract but uses the local
CTranslate2 INT8 model already deployed for live recitation. It also forces the
network-free RMS VAD path and uses the pipeline's estimated timestamps instead
of loading the prototype forced-alignment model.
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.workers.inference_worker import (
    InferenceWorker,
    _build_reference_audio_url,
    _build_result_dict,
    _describe_errors,
    _ensure_reference,
    _get_reference_store,
    _load_audio,
)

logger = get_logger(__name__)

# Leave enough headroom for a cold CT2 model load while still returning a
# terminal failed status before the mobile's 120-second polling window expires.
BATCH_ANALYSIS_TIMEOUT_SEC = int(
    os.environ.get("QARI_BATCH_ANALYSIS_TIMEOUT_SEC", "90")
)
MIN_SPEECH_RMS = float(os.environ.get("QARI_BATCH_MIN_SPEECH_RMS", "0.006"))
MIN_ACTIVE_SPEECH_SEC = float(
    os.environ.get("QARI_BATCH_MIN_ACTIVE_SPEECH_SEC", "0.25")
)


class FasterWhisperASRAdapter:
    """Expose the local Faster-Whisper model through ``QuranASR``'s interface."""

    def __init__(self) -> None:
        from ml.inference.faster_whisper_transcriber import get_transcriber

        self._transcriber = get_transcriber()

    def transcribe(self, audio, sample_rate: int = 16000):
        from ml.inference.asr import ASRResult, ASRToken, normalize_arabic

        started = time.perf_counter()
        words, confidences, starts, ends = self._transcriber.transcribe_with_timings(
            audio,
            sample_rate,
        )

        tokens: list[ASRToken] = []
        raw_words: list[str] = []
        normalized_words: list[str] = []
        for index, raw_word in enumerate(words):
            normalized = normalize_arabic(raw_word)
            if not normalized:
                continue
            confidence = (
                float(confidences[index])
                if index < len(confidences)
                else 1.0
            )
            start_ms = starts[index] if index < len(starts) else 0
            end_ms = ends[index] if index < len(ends) else start_ms

            # Whisper normally emits one lexical word per timestamp entry, but
            # normalization can occasionally leave whitespace. Preserve a
            # one-token-per-normalized-word contract for the aligner.
            for normalized_word in normalized.split():
                raw_words.append(raw_word.strip())
                normalized_words.append(normalized_word)
                tokens.append(
                    ASRToken(
                        text=raw_word.strip(),
                        normalized=normalized_word,
                        start_time=start_ms / 1000.0,
                        end_time=end_ms / 1000.0,
                        confidence=confidence,
                    )
                )

        return ASRResult(
            raw_text=" ".join(raw_words),
            normalized_text=" ".join(normalized_words),
            tokens=tokens,
            language="ar",
            model_id=self._transcriber.model_dir,
            processing_time_s=time.perf_counter() - started,
        )


class EstimatedTimestampsOnly:
    """Tell ``RecitationPipeline`` to use its cheap timestamp estimator."""

    def align(self, *_args, **_kwargs):
        raise RuntimeError("Forced alignment disabled in fast production worker")


_pipeline = None


def _get_fast_pipeline():
    global _pipeline
    if _pipeline is None:
        from ml.inference.vad import VoiceActivityDetector
        from ml.pipeline import RecitationPipeline

        store = _get_reference_store()
        if store is None:
            raise RuntimeError("Reference store unavailable — cannot run inference")

        _pipeline = RecitationPipeline(
            reference_store=store,
            asr=FasterWhisperASRAdapter(),
            vad=VoiceActivityDetector(use_silero=False),
            forced_aligner=EstimatedTimestampsOnly(),
        )
        logger.info(
            "fast_worker.pipeline_ready",
            model_dir=os.environ.get("QARI_FASTERWHISPER_MODEL_DIR"),
            vad="rms",
            forced_alignment="estimated",
        )
    return _pipeline


def _speech_activity(audio: np.ndarray, sample_rate: int) -> tuple[float, float]:
    """Return total active seconds and whole-clip RMS using 30 ms frames."""
    samples = np.asarray(audio, dtype=np.float32).reshape(-1)
    if samples.size == 0 or sample_rate <= 0:
        return 0.0, 0.0

    whole_rms = float(np.sqrt(np.mean(np.square(samples, dtype=np.float64))))
    frame_size = max(1, int(sample_rate * 0.03))
    active_frames = 0
    for start in range(0, samples.size, frame_size):
        frame = samples[start : start + frame_size]
        if frame.size < frame_size // 2:
            continue
        frame_rms = float(np.sqrt(np.mean(np.square(frame, dtype=np.float64))))
        if frame_rms >= MIN_SPEECH_RMS:
            active_frames += 1
    return active_frames * frame_size / sample_rate, whole_rms


def _public_user_audio_url(session_id: str, fallback: Optional[str]) -> Optional[str]:
    public_base = settings.recitation_api_public_url.rstrip("/")
    if public_base:
        return f"{public_base}/v1/recitations/{session_id}/audio"
    return fallback


async def run_fast_ml_inference(job: dict) -> dict:
    """Analyze one uploaded recording with the local CT2 model."""
    session_id = job.get("session_id", "")
    surah = int(job.get("surah_number", 1))
    ayah_from = int(job.get("ayah_from", 1))
    ayah_to = int(job.get("ayah_to", ayah_from))
    qari_id = job.get("qari_id")
    audio_path = job.get("audio_path")
    duration_sec = int(round(float(job.get("audio_duration_sec", 0))))
    user_audio_url = _public_user_audio_url(session_id, audio_path)

    if not audio_path or not os.path.exists(audio_path):
        raise ValueError(f"Audio file missing for session {session_id}")

    audio, sample_rate = _load_audio(audio_path)
    active_seconds, rms = _speech_activity(audio, sample_rate)
    if active_seconds < MIN_ACTIVE_SPEECH_SEC:
        logger.info(
            "fast_worker.no_speech",
            session_id=session_id,
            active_seconds=round(active_seconds, 3),
            rms=round(rms, 6),
        )
        return _build_result_dict(
            job=job,
            session_id=session_id,
            surah=surah,
            ayah=ayah_from,
            overall=0.0,
            pronunciation=0.0,
            tajweed=0.0,
            fluency=0.0,
            accuracy=0.0,
            word_verdicts=[],
            reference_audio_url=None,
            user_audio_url=user_audio_url,
            feedback="No recitation was detected. Move closer to the microphone and try again.",
            feedback_urdu=None,
            duration_seconds=duration_sec,
            confidence=0.0,
        )

    pipeline = _get_fast_pipeline()
    word_verdicts: list[dict] = []
    global_index = 0
    overall_total = 0.0
    fluency_total = 0.0
    tajweed_total = 0.0
    evaluated_ayahs = 0
    result_confidences: list[float] = []
    reference_audio_url: Optional[str] = None

    for ayah in range(ayah_from, ayah_to + 1):
        if not _ensure_reference(surah, ayah, qari_id):
            logger.warning(
                "fast_worker.skip_ayah_no_ref",
                session_id=session_id,
                surah=surah,
                ayah=ayah,
            )
            continue

        try:
            ml_result = await asyncio.wait_for(
                asyncio.to_thread(
                    pipeline.analyze,
                    audio,
                    sample_rate,
                    surah,
                    ayah,
                    session_id,
                    user_audio_url=user_audio_url or "",
                ),
                timeout=BATCH_ANALYSIS_TIMEOUT_SEC,
            )
        except asyncio.TimeoutError as exc:
            raise TimeoutError(
                f"Analysis exceeded {BATCH_ANALYSIS_TIMEOUT_SEC}s for {surah}:{ayah}"
            ) from exc

        evaluated_ayahs += 1
        overall_total += ml_result.scores.overall
        fluency_total += ml_result.scores.fluency
        tajweed_total += ml_result.scores.tajweed
        if reference_audio_url is None:
            reference_audio_url = (
                ml_result.reference_audio_url
                or _build_reference_audio_url(surah, ayah)
            )

        ayah_reference_url = (
            ml_result.reference_audio_url
            or _build_reference_audio_url(surah, ayah)
        )
        for word_result in ml_result.words:
            confidence = float(word_result.confidence)
            result_confidences.append(confidence)
            is_correct = word_result.verdict == "correct"
            word_verdicts.append(
                {
                    "word": word_result.word or word_result.reference or "",
                    "word_index": global_index,
                    "is_correct": is_correct,
                    "confidence": confidence,
                    "expected_text": word_result.reference,
                    "actual_text": word_result.hypothesis,
                    "error_type": None if is_correct else word_result.verdict,
                    "error_description": (
                        None
                        if is_correct
                        else _describe_errors(word_result.tajweed_issues)
                    ),
                    "reference_audio_url": ayah_reference_url,
                    "user_audio_url": user_audio_url,
                    "phoneme_errors": [],
                }
            )
            global_index += 1

    if evaluated_ayahs == 0:
        return _build_result_dict(
            job=job,
            session_id=session_id,
            surah=surah,
            ayah=ayah_from,
            overall=0.0,
            pronunciation=0.0,
            tajweed=0.0,
            fluency=0.0,
            accuracy=0.0,
            word_verdicts=[],
            reference_audio_url=None,
            user_audio_url=user_audio_url,
            feedback="We couldn't analyse this recitation with enough confidence.",
            feedback_urdu=None,
            duration_seconds=duration_sec,
            confidence=0.0,
        )

    average_confidence = (
        sum(result_confidences) / len(result_confidences)
        if result_confidences
        else 0.0
    )
    if average_confidence < 0.5:
        # Never surface red mistakes from an uncertain transcription.
        word_verdicts = []

    divisor = float(evaluated_ayahs)
    return _build_result_dict(
        job=job,
        session_id=session_id,
        surah=surah,
        ayah=ayah_from,
        overall=overall_total / divisor / 100.0,
        pronunciation=fluency_total / divisor / 100.0,
        tajweed=tajweed_total / divisor / 100.0,
        fluency=fluency_total / divisor / 100.0,
        accuracy=fluency_total / divisor / 100.0,
        word_verdicts=word_verdicts,
        reference_audio_url=reference_audio_url,
        user_audio_url=user_audio_url,
        feedback=(
            "AI feedback complete. Tap red words to compare your recitation."
            if word_verdicts
            else "We couldn't analyse this recitation with enough confidence."
        ),
        feedback_urdu=None,
        duration_seconds=duration_sec,
        confidence=average_confidence,
    )


async def run_worker() -> None:
    worker = InferenceWorker(inference_callback=run_fast_ml_inference)
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(run_worker())
