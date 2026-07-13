"""
Tajweed rule checks using real audio analysis.

Each check operates on the forced-aligned word timestamps and the raw audio
signal to detect specific tajweed rules:

  - Ghunnah (nasalization) duration check: measures nasal resonance duration
    at noon/meem with shadda; must be >= minimum threshold.
  - Qalqalah (echoing burst) detection: detects abrupt energy burst at the
    end of qalqalah letters (ق ط ب ج د) when sakin.
  - Madd (elongation) duration check: measures vowel elongation duration
    for madd letters (ا و ي); must be 2-6 harakat (≈ 2-6 vowel durations).
  - Ikhfa (concealment) classifier: detects nasalization + tongue concealment
    after noon sakin before 15 specific letters.
  - Idgham (merging) classifier: detects merging of noon sakin into
    following ya/ra/meem/noon/lam/waw.

All checks only surface 'fail' verdicts when confidence >= 0.85.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

CONFIDENCE_THRESHOLD = 0.85  # Only surface 'fail' with confidence >= this

# Qalqalah letters (ق ط ب ج د) — sakin (no vowel) letters that produce a bounce
QALQALAH_LETTERS = frozenset("قطبجد")

# Ghunnah letters — noon (ن) and meem (م) with shadda
GHUNNAH_LETTERS = frozenset("نم")

# Madd letters — alef (ا), waw (و), ya (ي) for elongation
MADD_LETTERS = frozenset("اوي")

# Ikhfa letters — 15 letters that cause concealment after noon sakin
IKHFA_LETTERS = frozenset("تثجدذزسشصضطظفقكلمن")

# Idgham letters — 6 letters that cause merging after noon sakin
IDGHAM_LETTERS = frozenset("يرومنل")

# Duration thresholds (in milliseconds) — based on typical recitation timing
# At moderate pace, 1 harakah (vowel duration) ≈ 200-300ms
GHUNNAH_MIN_MS = 200       # Minimum nasalization duration
GHUNNAH_MAX_MS = 600       # Maximum before it's considered excessive
MADD_MIN_MS = 400           # Minimum elongation (2 harakat)
MADD_MAX_MS = 1200          # Maximum elongation (6 harakat)
MADD_EXCESSIVE_MS = 1800    # Beyond this is excessive

# Energy thresholds
QALQALAH_BURST_RATIO = 1.5  # Peak energy / surrounding energy ratio
IKHFA_NASAL_RATIO = 0.3     # Minimum nasal energy ratio for ikhfa
IDGHAM_MERGE_RATIO = 0.5    # Energy merge ratio for idgham

# ── Enums ────────────────────────────────────────────────────────────────────

class TajweedCheckType(str, Enum):
    """Types of tajweed checks."""
    GHUNNAH = "ghunnah"
    QALQALAH = "qalqalah"
    MADD = "madd"
    IKHFA = "ikhfa"
    IDGHAM = "idgham"


class TajweedVerdict(str, Enum):
    """Verdict for a tajweed check."""
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"
    INSUFFICIENT_DATA = "insufficient_data"


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class TajweedResult:
    """Result of a single tajweed check."""
    check_type: TajweedCheckType
    verdict: TajweedVerdict
    confidence: float                           # [0, 1]
    word_index: Optional[int] = None            # Index of the word being checked
    letter: Optional[str] = None                # The tajweed letter
    measured_value: float = 0.0                 # Measured duration (ms) or energy ratio
    expected_range: str = ""                    # Expected range description
    detail: str = ""                            # Human-readable detail
    start_ms: int = 0                           # Time range of the check
    end_ms: int = 0

    @property
    def should_surface(self) -> bool:
        """Whether this result should be surfaced to the user (fail + high confidence)."""
        return (
            self.verdict == TajweedVerdict.FAIL
            and self.confidence >= CONFIDENCE_THRESHOLD
        )


@dataclass
class TajweedCheckSummary:
    """Summary of all tajweed checks for a recitation."""
    results: list[TajweedResult] = field(default_factory=list)
    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    not_applicable: int = 0
    insufficient_data: int = 0
    surfaced_failures: int = 0  # Failures with confidence >= threshold

    @property
    def tajweed_score(self) -> float:
        """Percentage of passed checks out of total applicable checks."""
        applicable = self.passed + self.failed
        if applicable == 0:
            return 100.0
        return (self.passed / applicable) * 100.0


# ── Audio analysis utilities ─────────────────────────────────────────────────

def _rms_energy(audio: np.ndarray, start_sample: int, end_sample: int) -> float:
    """Compute RMS energy of an audio segment."""
    segment = audio[start_sample:end_sample]
    if len(segment) == 0:
        return 0.0
    return float(np.sqrt(np.mean(segment.astype(np.float64) ** 2)))


def _spectral_centroid(audio: np.ndarray, sr: int, start_sample: int, end_sample: int) -> float:
    """
    Compute spectral centroid of an audio segment.

    Higher spectral centroid → brighter sound (less nasal).
    Lower spectral centroid → darker sound (more nasal).
    Used for nasalization detection.
    """
    segment = audio[start_sample:end_sample]
    if len(segment) < 4:
        return 0.0

    # Simple FFT-based spectral centroid
    fft = np.fft.rfft(segment.astype(np.float64))
    magnitude = np.abs(fft)
    freqs = np.fft.rfftfreq(len(segment), 1.0 / sr)

    if magnitude.sum() == 0:
        return 0.0

    return float(np.sum(freqs * magnitude) / np.sum(magnitude))


def _zero_crossing_rate(audio: np.ndarray, start_sample: int, end_sample: int) -> float:
    """Compute zero-crossing rate of an audio segment."""
    segment = audio[start_sample:end_sample]
    if len(segment) < 2:
        return 0.0
    signs = np.sign(segment)
    zcr = np.mean(np.abs(np.diff(signs)) > 0)
    return float(zcr)


def _energy_envelope(audio: np.ndarray, sr: int, start_ms: int, end_ms: int, frame_ms: int = 10) -> np.ndarray:
    """
    Compute energy envelope (per-frame RMS) for a time range.

    Returns array of RMS values per frame.
    """
    start_s = int(start_ms * sr / 1000)
    end_s = int(end_ms * sr / 1000)
    segment = audio[start_s:end_s]
    if len(segment) == 0:
        return np.array([])

    frame_size = int(sr * frame_ms / 1000)
    n_frames = max(1, len(segment) // frame_size)

    envelope = np.zeros(n_frames)
    for i in range(n_frames):
        s = i * frame_size
        e = s + frame_size
        envelope[i] = np.sqrt(np.mean(segment[s:e].astype(np.float64) ** 2) + 1e-10)

    return envelope


# ── Tajweed Checker ──────────────────────────────────────────────────────────

class TajweedChecker:
    """
    Tajweed rule checker using audio analysis.

    Performs energy-based and duration-based checks on aligned word segments
    to detect tajweed rule violations. Only surfaces 'fail' verdicts when
    confidence >= 0.85.

    Parameters
    ----------
    sample_rate : int, default 16000
        Audio sample rate.
    confidence_threshold : float, default 0.85
        Minimum confidence to surface a 'fail' verdict.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ) -> None:
        self.sample_rate = sample_rate
        self.confidence_threshold = confidence_threshold

    def check_all(
        self,
        audio: np.ndarray,
        word_texts: list[str],
        word_starts_ms: list[int],
        word_ends_ms: list[int],
        *,
        reference_phonemes: Optional[list[list[str]]] = None,
        tajweed_positions: Optional[list[dict]] = None,
    ) -> TajweedCheckSummary:
        """
        Run all applicable tajweed checks on the recitation.

        Parameters
        ----------
        audio : np.ndarray
            Mono audio signal.
        word_texts : list[str]
            Words (normalized, no diacritics) in order.
        word_starts_ms, word_ends_ms : list[int]
            Per-word start/end times in milliseconds.
        reference_phonemes : list[list[str]], optional
            Expected phoneme sequences per word from the reference store.
        tajweed_positions : list[dict], optional
            Per-word tajweed annotations from the reference store.
            Each dict has keys like {"rule": "ghunnah", "letter": "ن", "position": 2}.

        Returns
        -------
        TajweedCheckSummary
            Summary of all checks with pass/fail verdicts.
        """
        results: list[TajweedResult] = []

        for i, word in enumerate(word_texts):
            if i >= len(word_starts_ms) or i >= len(word_ends_ms):
                continue

            start_ms = word_starts_ms[i]
            end_ms = word_ends_ms[i]

            # Use authoritative tajweed_positions when present, otherwise infer
            # the likely positions from the word text. A reference entry of
            # {"checks": []} must NOT suppress inference — otherwise no checks
            # run, nothing is ever evaluated, and the tajweed score defaults
            # to 100% (see compute_scores). This was the cause of tajweed
            # always showing 100% for ayahs whose reference data had no spans.
            provided = []
            if tajweed_positions and i < len(tajweed_positions) and tajweed_positions[i]:
                provided = tajweed_positions[i].get("checks", [])
            positions = provided if provided else self._infer_tajweed_positions(word)

            for pos in positions:
                rule = pos.get("rule", "")
                letter = pos.get("letter", "")
                char_pos = pos.get("position", 0)

                # Estimate the time window for this letter within the word
                letter_start, letter_end = self._estimate_letter_window(
                    start_ms, end_ms, char_pos, len(word)
                )

                if rule == "ghunnah":
                    results.append(self._check_ghunnah(
                        audio, letter, letter_start, letter_end, i
                    ))
                elif rule == "qalqalah":
                    results.append(self._check_qalqalah(
                        audio, letter, letter_start, letter_end, i
                    ))
                elif rule == "madd":
                    results.append(self._check_madd(
                        audio, letter, letter_start, letter_end, i
                    ))
                elif rule == "ikhfa":
                    results.append(self._check_ikhfa(
                        audio, letter, letter_start, letter_end, i, word, char_pos
                    ))
                elif rule == "idgham":
                    results.append(self._check_idgham(
                        audio, letter, letter_start, letter_end, i, word, char_pos
                    ))

        # Build summary
        summary = TajweedCheckSummary(results=results)
        summary.total_checks = len(results)
        summary.passed = sum(1 for r in results if r.verdict == TajweedVerdict.PASS)
        summary.failed = sum(1 for r in results if r.verdict == TajweedVerdict.FAIL)
        summary.not_applicable = sum(1 for r in results if r.verdict == TajweedVerdict.NOT_APPLICABLE)
        summary.insufficient_data = sum(1 for r in results if r.verdict == TajweedVerdict.INSUFFICIENT_DATA)
        summary.surfaced_failures = sum(1 for r in results if r.should_surface)

        return summary

    def _infer_tajweed_positions(self, word: str) -> list[dict]:
        """
        Infer potential tajweed rule positions from word text.

        Since the normalized word has no diacritics, we look for letters
        that commonly trigger tajweed rules. This is a heuristic — the
        reference store provides authoritative positions when available.
        """
        positions: list[dict] = []

        for idx, char in enumerate(word):
            if char in QALQALAH_LETTERS:
                positions.append({
                    "rule": "qalqalah",
                    "letter": char,
                    "position": idx,
                })
            if char in GHUNNAH_LETTERS:
                positions.append({
                    "rule": "ghunnah",
                    "letter": char,
                    "position": idx,
                })
            if char in MADD_LETTERS:
                positions.append({
                    "rule": "madd",
                    "letter": char,
                    "position": idx,
                })

        # Check for ikhfa/idgham patterns (noon followed by specific letters)
        for idx, char in enumerate(word):
            if char == "ن" and idx + 1 < len(word):
                next_char = word[idx + 1]
                if next_char in IKHFA_LETTERS and next_char not in IDGHAM_LETTERS:
                    positions.append({
                        "rule": "ikhfa",
                        "letter": char,
                        "position": idx,
                    })
                if next_char in IDGHAM_LETTERS:
                    positions.append({
                        "rule": "idgham",
                        "letter": char,
                        "position": idx,
                    })

        return positions

    def _estimate_letter_window(
        self, word_start_ms: int, word_end_ms: int, char_pos: int, word_len: int
    ) -> tuple[int, int]:
        """
        Estimate the time window for a specific character position within a word.

        Assumes uniform time distribution across characters (approximation).
        """
        if word_len <= 1:
            return word_start_ms, word_end_ms

        char_duration = (word_end_ms - word_start_ms) / word_len
        letter_start = int(word_start_ms + char_pos * char_duration)
        letter_end = int(word_start_ms + (char_pos + 1) * char_duration)
        return letter_start, letter_end

    # ── Individual checks ─────────────────────────────────────────────────────

    def _check_ghunnah(
        self,
        audio: np.ndarray,
        letter: str,
        start_ms: int,
        end_ms: int,
        word_index: int,
    ) -> TajweedResult:
        """
        Check ghunnah (nasalization) duration.

        Ghunnah occurs with noon (ن) or meem (م) with shadda. The nasal
        sound should be held for a minimum duration (≈200-400ms).

        Detection: measure the duration of sustained low spectral centroid
        (nasal resonance) around the letter position.
        """
        sr = self.sample_rate
        start_s = int(start_ms * sr / 1000)
        end_s = int(end_ms * sr / 1000)

        # Extend window slightly to capture the nasalization tail
        ext_start = max(0, start_s - int(0.02 * sr))
        ext_end = min(len(audio), end_s + int(0.15 * sr))

        if ext_end <= ext_start:
            return TajweedResult(
                check_type=TajweedCheckType.GHUNNAH,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Measure nasalization duration using spectral centroid
        # Nasal sounds have lower spectral centroid
        frame_ms = 10
        envelope = _energy_envelope(audio, sr, start_ms, end_ms + 150, frame_ms)

        if len(envelope) < 3:
            return TajweedResult(
                check_type=TajweedCheckType.GHUNNAH,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Detect sustained energy (nasalization) — frames with energy above
        # a threshold relative to peak
        peak_energy = envelope.max()
        if peak_energy < 1e-3:
            return TajweedResult(
                check_type=TajweedCheckType.GHUNNAH,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        threshold = peak_energy * 0.3
        sustained_frames = np.sum(envelope > threshold)
        nasal_duration_ms = sustained_frames * frame_ms

        # Also check spectral centroid for nasalization quality
        centroid = _spectral_centroid(audio, sr, ext_start, ext_end)
        # Lower centroid → more nasal. Typical speech: ~2000-4000 Hz
        # Nasal: ~800-1500 Hz
        is_nasal = centroid < 2000 if centroid > 0 else False

        # Confidence based on how clear the nasalization signal is
        if is_nasal:
            confidence = 0.90
        else:
            confidence = 0.88

        # Verdict
        # Ghunnah IS nasalization. If the nasal quality is absent at a noon/meem
        # position, the rule was not applied — this is the core failure mode
        # (reciting without ghunnah). Previously this only checked the gross
        # sustained duration, which any spoken sound satisfies, so ghunnah
        # always passed.
        if not is_nasal:
            verdict = TajweedVerdict.FAIL
            detail = f"No ghunnah (nasalization) detected: centroid={centroid:.0f}Hz"
        elif nasal_duration_ms < GHUNNAH_MIN_MS:
            verdict = TajweedVerdict.FAIL
            detail = f"Ghunnah too short: {nasal_duration_ms:.0f}ms (min {GHUNNAH_MIN_MS}ms)"
        elif nasal_duration_ms > GHUNNAH_MAX_MS:
            verdict = TajweedVerdict.FAIL
            detail = f"Ghunnah too long: {nasal_duration_ms:.0f}ms (max {GHUNNAH_MAX_MS}ms)"
            confidence = min(confidence + 0.05, 1.0)
        else:
            verdict = TajweedVerdict.PASS
            detail = f"Ghunnah OK: {nasal_duration_ms:.0f}ms, centroid={centroid:.0f}Hz"

        return TajweedResult(
            check_type=TajweedCheckType.GHUNNAH,
            verdict=verdict,
            confidence=confidence,
            word_index=word_index,
            letter=letter,
            measured_value=nasal_duration_ms,
            expected_range=f"{GHUNNAH_MIN_MS}-{GHUNNAH_MAX_MS}ms",
            detail=detail,
            start_ms=start_ms,
            end_ms=end_ms,
        )

    def _check_qalqalah(
        self,
        audio: np.ndarray,
        letter: str,
        start_ms: int,
        end_ms: int,
        word_index: int,
    ) -> TajweedResult:
        """
        Check qalqalah (echoing burst) detection.

        Qalqalah occurs when one of ق ط ب ج د is sakin (no vowel).
        It produces a brief echoing bounce. Detection: look for an abrupt
        energy burst at the end of the letter's time window, with a
        rapid decay.

        The burst is characterized by:
        1. A sharp energy peak at the release
        2. Rapid decay after the peak
        3. The peak energy is significantly higher than the surrounding energy
        """
        sr = self.sample_rate

        # Focus on the end portion of the letter (where the burst occurs)
        burst_start_ms = start_ms + int((end_ms - start_ms) * 0.5)
        burst_end_ms = end_ms + int(0.08 * 1000)  # 80ms after letter end

        burst_start_s = int(burst_start_ms * sr / 1000)
        burst_end_s = min(len(audio), int(burst_end_ms * sr / 1000))

        if burst_end_s <= burst_start_s:
            return TajweedResult(
                check_type=TajweedCheckType.QALQALAH,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Compute energy envelope in the burst region
        envelope = _energy_envelope(audio, sr, burst_start_ms, burst_end_ms, frame_ms=5)

        if len(envelope) < 3:
            return TajweedResult(
                check_type=TajweedCheckType.QALQALAH,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Detect burst: peak energy / surrounding energy ratio
        peak_idx = int(np.argmax(envelope))
        peak_energy = envelope[peak_idx]

        # Absolute energy check — if signal is too weak, can't determine
        if peak_energy < 1e-3:
            return TajweedResult(
                check_type=TajweedCheckType.QALQALAH,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Surrounding energy (before the peak)
        if peak_idx > 0:
            pre_energy = np.mean(envelope[:peak_idx])
        else:
            pre_energy = envelope[0] if len(envelope) > 0 else 0.0

        # Post-peak decay
        if peak_idx < len(envelope) - 1:
            post_energy = np.mean(envelope[peak_idx + 1:])
            decay_ratio = (peak_energy - post_energy) / (peak_energy + 1e-10)
        else:
            post_energy = 0.0
            decay_ratio = 1.0

        if pre_energy < 1e-8:
            burst_ratio = peak_energy / 1e-8
        else:
            burst_ratio = peak_energy / pre_energy

        # Confidence: higher burst ratio + clear decay → higher confidence
        if burst_ratio >= QALQALAH_BURST_RATIO and decay_ratio > 0.3:
            confidence = min(0.90 + (burst_ratio - QALQALAH_BURST_RATIO) * 0.05, 0.98)
            verdict = TajweedVerdict.PASS
            detail = f"Qalqalah burst detected: ratio={burst_ratio:.2f}, decay={decay_ratio:.2f}"
        elif burst_ratio < 0.8:
            # Very low burst — likely missing qalqalah
            confidence = 0.88
            verdict = TajweedVerdict.FAIL
            detail = f"No qalqalah burst: ratio={burst_ratio:.2f} (expected >= {QALQALAH_BURST_RATIO})"
        else:
            # Ambiguous
            confidence = 0.75
            verdict = TajweedVerdict.PASS
            detail = f"Weak qalqalah: ratio={burst_ratio:.2f}"

        return TajweedResult(
            check_type=TajweedCheckType.QALQALAH,
            verdict=verdict,
            confidence=confidence,
            word_index=word_index,
            letter=letter,
            measured_value=burst_ratio,
            expected_range=f"burst ratio >= {QALQALAH_BURST_RATIO}",
            detail=detail,
            start_ms=burst_start_ms,
            end_ms=burst_end_ms,
        )

    def _check_madd(
        self,
        audio: np.ndarray,
        letter: str,
        start_ms: int,
        end_ms: int,
        word_index: int,
    ) -> TajweedResult:
        """
        Check madd (elongation) duration.

        Madd letters (ا و ي) produce elongated vowel sounds. The duration
        should be between 2 and 6 harakat (≈ 400-1200ms at moderate pace).

        Detection: measure the sustained voiced duration at the letter position.
        Uses energy envelope to find the steady-state vowel portion.
        """
        sr = self.sample_rate
        frame_ms = 10

        # Extend window to capture the full elongation
        ext_end_ms = end_ms + 200  # 200ms extra
        ext_end_s = min(len(audio), int(ext_end_ms * sr / 1000))

        envelope = _energy_envelope(audio, sr, start_ms, ext_end_ms, frame_ms)

        if len(envelope) < 4:
            return TajweedResult(
                check_type=TajweedCheckType.MADD,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        peak_energy = envelope.max()
        if peak_energy < 1e-3:
            return TajweedResult(
                check_type=TajweedCheckType.MADD,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Measure sustained vowel duration: consecutive frames above 40% peak
        threshold = peak_energy * 0.4
        sustained_frames = 0
        in_sustained = False

        for val in envelope:
            if val > threshold:
                sustained_frames += 1
                in_sustained = True
            elif in_sustained and val < threshold * 0.5:
                # Energy dropped significantly — end of sustained portion
                break

        madd_duration_ms = sustained_frames * frame_ms

        # Confidence based on clarity of sustained portion
        if sustained_frames > 10:
            confidence = 0.92
        elif sustained_frames > 5:
            confidence = 0.85
        else:
            confidence = 0.70

        # Verdict
        if madd_duration_ms < MADD_MIN_MS:
            verdict = TajweedVerdict.FAIL
            detail = f"Madd too short: {madd_duration_ms:.0f}ms (min {MADD_MIN_MS}ms)"
        elif madd_duration_ms > MADD_EXCESSIVE_MS:
            verdict = TajweedVerdict.FAIL
            detail = f"Madd excessive: {madd_duration_ms:.0f}ms (max {MADD_EXCESSIVE_MS}ms)"
            confidence = min(confidence + 0.05, 1.0)
        else:
            verdict = TajweedVerdict.PASS
            detail = f"Madd duration OK: {madd_duration_ms:.0f}ms"

        return TajweedResult(
            check_type=TajweedCheckType.MADD,
            verdict=verdict,
            confidence=confidence,
            word_index=word_index,
            letter=letter,
            measured_value=madd_duration_ms,
            expected_range=f"{MADD_MIN_MS}-{MADD_MAX_MS}ms",
            detail=detail,
            start_ms=start_ms,
            end_ms=end_ms,
        )

    def _check_ikhfa(
        self,
        audio: np.ndarray,
        letter: str,
        start_ms: int,
        end_ms: int,
        word_index: int,
        word: str,
        char_pos: int,
    ) -> TajweedResult:
        """
        Check ikhfa (concealment) — nasalization with tongue concealment.

        Ikhfa occurs when noon sakin is followed by one of 15 specific letters.
        The noon sound is partially concealed with nasalization.

        Detection: check for nasalization (lower spectral centroid) combined
        with a smooth transition to the following letter (no hard stop).
        """
        sr = self.sample_rate

        # Window covering the noon and transition to next letter
        trans_start_ms = start_ms
        trans_end_ms = end_ms + int(0.1 * 1000)  # 100ms into next letter

        trans_start_s = int(trans_start_ms * sr / 1000)
        trans_end_s = min(len(audio), int(trans_end_ms * sr / 1000))

        if trans_end_s <= trans_start_s:
            return TajweedResult(
                check_type=TajweedCheckType.IKHFA,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Measure nasalization: spectral centroid should be lower (nasal)
        centroid = _spectral_centroid(audio, sr, trans_start_s, trans_end_s)

        # Measure energy continuity (no hard stop between noon and next letter)
        envelope = _energy_envelope(audio, sr, trans_start_ms, trans_end_ms, frame_ms=10)

        if len(envelope) < 3:
            return TajweedResult(
                check_type=TajweedCheckType.IKHFA,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Absolute energy check — if signal is too weak, can't determine
        if envelope.max() < 1e-3:
            return TajweedResult(
                check_type=TajweedCheckType.IKHFA,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Energy continuity: low variance in envelope → smooth transition
        energy_cv = float(np.std(envelope) / (np.mean(envelope) + 1e-10))

        # Nasalization quality
        is_nasal = centroid < 2500 if centroid > 0 else False
        is_smooth = energy_cv < 0.5

        if is_nasal and is_smooth:
            confidence = 0.90
            verdict = TajweedVerdict.PASS
            detail = f"Ikhfa detected: nasal={is_nasal}, centroid={centroid:.0f}Hz, smooth={is_smooth}"
        elif not is_nasal and energy_cv > 0.8:
            # Hard stop + no nasalization → ikhfa not performed
            confidence = 0.87
            verdict = TajweedVerdict.FAIL
            detail = f"No ikhfa: hard stop detected, centroid={centroid:.0f}Hz, cv={energy_cv:.2f}"
        else:
            confidence = 0.75
            verdict = TajweedVerdict.PASS
            detail = f"Partial ikhfa: nasal={is_nasal}, centroid={centroid:.0f}Hz"

        return TajweedResult(
            check_type=TajweedCheckType.IKHFA,
            verdict=verdict,
            confidence=confidence,
            word_index=word_index,
            letter=letter,
            measured_value=centroid,
            expected_range="low spectral centroid + smooth transition",
            detail=detail,
            start_ms=trans_start_ms,
            end_ms=trans_end_ms,
        )

    def _check_idgham(
        self,
        audio: np.ndarray,
        letter: str,
        start_ms: int,
        end_ms: int,
        word_index: int,
        word: str,
        char_pos: int,
    ) -> TajweedResult:
        """
        Check idgham (merging) — noon sakin merges into following letter.

        Idgham occurs when noon sakin is followed by one of ي ر و م ن ل.
        The noon sound merges into the following letter, becoming geminated.

        Detection: check for absence of a distinct noon sound and presence
        of a geminated (doubled) following letter. Energy should show a
        single sustained segment rather than two distinct segments.
        """
        sr = self.sample_rate

        # Window covering noon + following letter
        merge_start_ms = start_ms
        merge_end_ms = end_ms + int(0.15 * 1000)  # 150ms into next letter

        merge_start_s = int(merge_start_ms * sr / 1000)
        merge_end_s = min(len(audio), int(merge_end_ms * sr / 1000))

        if merge_end_s <= merge_start_s:
            return TajweedResult(
                check_type=TajweedCheckType.IDGHAM,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        envelope = _energy_envelope(audio, sr, merge_start_ms, merge_end_ms, frame_ms=10)

        if len(envelope) < 4:
            return TajweedResult(
                check_type=TajweedCheckType.IDGHAM,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        # Check for single sustained segment (merged) vs two segments (not merged)
        peak = envelope.max()
        if peak < 1e-3:
            return TajweedResult(
                check_type=TajweedCheckType.IDGHAM,
                verdict=TajweedVerdict.INSUFFICIENT_DATA,
                confidence=0.0,
                word_index=word_index,
                letter=letter,
                start_ms=start_ms,
                end_ms=end_ms,
            )

        threshold = peak * 0.3
        above = envelope > threshold

        # Count distinct segments (groups of consecutive above-threshold frames)
        segments = 0
        in_seg = False
        for a in above:
            if a and not in_seg:
                segments += 1
                in_seg = True
            elif not a:
                in_seg = False

        # Also check zero-crossing rate for gemination (doubled consonant
        # has different ZCR pattern)
        zcr = _zero_crossing_rate(audio, merge_start_s, merge_end_s)

        if segments <= 1:
            # Single segment → merged (idgham performed)
            confidence = 0.89
            verdict = TajweedVerdict.PASS
            detail = f"Idgham detected: {segments} segment (merged), zcr={zcr:.3f}"
        elif segments >= 2:
            # Two distinct segments → not merged (noon pronounced separately)
            confidence = 0.86
            verdict = TajweedVerdict.FAIL
            detail = f"No idgham: {segments} segments (not merged), zcr={zcr:.3f}"
        else:
            confidence = 0.70
            verdict = TajweedVerdict.PASS
            detail = f"Ambiguous idgham: {segments} segments"

        return TajweedResult(
            check_type=TajweedCheckType.IDGHAM,
            verdict=verdict,
            confidence=confidence,
            word_index=word_index,
            letter=letter,
            measured_value=segments,
            expected_range="1 merged segment",
            detail=detail,
            start_ms=merge_start_ms,
            end_ms=merge_end_ms,
        )
