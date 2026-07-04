"""Tajweed rule checking — duration rules and classifiers.

Phase 2 feature. Built on Phase 1 forced alignment plumbing.
Only surfaces 'fail' with confidence ≥ 0.85; otherwise stays silent.
"""
import numpy as np
from typing import Optional
import structlog

log = structlog.get_logger()

# Minimum confidence to surface a Tajweed fail verdict
MIN_CONFIDENCE = 0.85


def check_ghunnah(
    audio_segment: np.ndarray,
    expected_duration_ms: float,
    reference_duration_ms: float,
    sample_rate: int = 16000,
) -> dict:
    """Check ghunnah (nasalization) duration.

    Ghunnah should be ~2 harakah. Compare user's nasal segment
    duration against reference, tempo-normalized.

    Returns {"rule": "ghunnah", "pass": bool, "confidence": float}
    """
    user_duration_ms = len(audio_segment) / sample_rate * 1000

    # Tempo-normalized ratio
    if reference_duration_ms > 0:
        ratio = user_duration_ms / reference_duration_ms
    else:
        ratio = user_duration_ms / expected_duration_ms

    # Pass if within 0.5x to 2.0x of expected
    passed = 0.5 <= ratio <= 2.0
    confidence = 1.0 - min(abs(1.0 - ratio), 1.0)

    return {
        "rule": "ghunnah",
        "pass": passed,
        "confidence": confidence,
        "user_duration_ms": user_duration_ms,
        "expected_duration_ms": expected_duration_ms,
    }


def check_qalqalah(
    audio_segment: np.ndarray,
    sample_rate: int = 16000,
) -> dict:
    """Check qalqalah (echo/bounce) — detect burst + short vowel release.

    Uses simple energy-based detection. In production, use a trained
    binary classifier on log-mel features of the letter window.

    Returns {"rule": "qalqalah", "pass": bool, "confidence": float}
    """
    # Simple energy analysis: look for a burst followed by decay
    if len(audio_segment) == 0:
        return {"rule": "qalqalah", "pass": False, "confidence": 0.0}

    # Compute short-time energy
    frame_size = int(sample_rate * 0.01)  # 10ms frames
    n_frames = len(audio_segment) // frame_size
    if n_frames < 3:
        return {"rule": "qalqalah", "pass": False, "confidence": 0.3}

    energies = []
    for i in range(n_frames):
        frame = audio_segment[i * frame_size : (i + 1) * frame_size]
        energies.append(np.sqrt(np.mean(frame ** 2)))

    energies = np.array(energies)

    # Qalqalah pattern: burst (high energy) then quick decay
    peak_idx = np.argmax(energies)
    if peak_idx < n_frames - 1:
        decay_ratio = energies[-1] / (energies[peak_idx] + 1e-8)
        has_burst = energies[peak_idx] > 0.01
        has_decay = decay_ratio < 0.5
        passed = has_burst and has_decay
        confidence = min(0.9, energies[peak_idx] * 10)
    else:
        passed = False
        confidence = 0.3

    return {
        "rule": "qalqalah",
        "pass": passed,
        "confidence": confidence,
    }


def check_tajweed_rule(
    rule: str,
    audio_segment: np.ndarray,
    expected_duration_ms: float = 0,
    reference_duration_ms: float = 0,
    sample_rate: int = 16000,
) -> Optional[dict]:
    """Dispatch to the appropriate tajweed check.

    Only returns a result if confidence >= MIN_CONFIDENCE.
    Otherwise returns None (stay silent — trust principle).
    """
    result = None

    if rule == "ghunnah":
        result = check_ghunnah(audio_segment, expected_duration_ms,
                               reference_duration_ms, sample_rate)
    elif rule == "qalqalah":
        result = check_qalqalah(audio_segment, sample_rate)
    elif rule in ("ikhfa", "idgham", "iqlab"):
        # TODO: Train classifiers for these rules
        result = {"rule": rule, "pass": True, "confidence": 0.5}
    elif rule.startswith("madd"):
        # Madd = elongation, check duration
        result = check_ghunnah(audio_segment, expected_duration_ms,
                               reference_duration_ms, sample_rate)
        result["rule"] = rule
    else:
        return None

    # Trust principle: only surface fails with high confidence
    if not result["pass"] and result["confidence"] < MIN_CONFIDENCE:
        return None

    return result
