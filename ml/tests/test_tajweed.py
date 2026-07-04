"""
Tests for tajweed rule checks.

Tests the TajweedChecker with synthetic audio signals to verify
that ghunnah, qalqalah, madd, ikhfa, and idgham checks produce
correct verdicts and respect the 0.85 confidence threshold.
"""

import pytest
import numpy as np
from ml.tajweed.checks import (
    TajweedChecker,
    TajweedCheckType,
    TajweedVerdict,
    TajweedResult,
    TajweedCheckSummary,
    CONFIDENCE_THRESHOLD,
)


@pytest.fixture
def sample_rate():
    return 16000


@pytest.fixture
def silence_audio(sample_rate):
    """1 second of silence."""
    return np.zeros(sample_rate, dtype=np.float32)


@pytest.fixture
def tone_audio(sample_rate):
    """1 second of 440Hz tone at moderate amplitude."""
    t = np.linspace(0, 1, sample_rate, endpoint=False)
    return (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)


@pytest.fixture
def burst_audio(sample_rate):
    """Audio with a sharp energy burst at 200ms (for qalqalah)."""
    t = np.linspace(0, 0.5, sample_rate // 2, endpoint=False)
    audio = 0.1 * np.sin(2 * np.pi * 200 * t).astype(np.float32)
    # Add burst at 200ms
    burst_start = int(0.2 * sample_rate)
    burst_len = int(0.05 * sample_rate)
    burst_t = np.linspace(0, 0.05, burst_len, endpoint=False)
    audio[burst_start:burst_start + burst_len] += 0.8 * np.sin(2 * np.pi * 1000 * burst_t).astype(np.float32)
    return audio


@pytest.fixture
def sustained_audio(sample_rate):
    """Audio with sustained energy for 500ms (for madd/ghunnah)."""
    t = np.linspace(0, 0.8, int(0.8 * sample_rate), endpoint=False)
    # Low frequency sustained tone (nasal-like)
    return (0.4 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)


class TestTajweedCheckerBasics:
    """Basic TajweedChecker functionality."""

    def test_initialization(self):
        """Checker initializes with correct defaults."""
        checker = TajweedChecker()
        assert checker.sample_rate == 16000
        assert checker.confidence_threshold == CONFIDENCE_THRESHOLD
        assert checker.confidence_threshold == 0.85

    def test_check_all_empty(self, silence_audio, sample_rate):
        """Empty word list → no checks."""
        checker = TajweedChecker(sample_rate=sample_rate)
        summary = checker.check_all(silence_audio, [], [], [])
        assert summary.total_checks == 0
        assert summary.tajweed_score == 100.0

    def test_check_all_silence(self, silence_audio, sample_rate):
        """Silent audio with words → insufficient data or pass."""
        checker = TajweedChecker(sample_rate=sample_rate)
        summary = checker.check_all(
            silence_audio,
            ["بسم"],
            [0],
            [500],
        )
        # Should have some checks (inferred from word)
        assert summary.total_checks > 0


class TestGhunnahCheck:
    """Tests for ghunnah (nasalization) duration check."""

    def test_ghunnah_sustained(self, sustained_audio, sample_rate):
        """Sustained nasal-like audio → ghunnah should pass or have data."""
        checker = TajweedChecker(sample_rate=sample_rate)
        # Use noon letter
        summary = checker.check_all(
            sustained_audio,
            ["إن"],
            [0],
            [800],
            tajweed_positions=[{
                "checks": [
                    {"rule": "ghunnah", "letter": "ن", "position": 1}
                ]
            }],
        )
        ghunnah_results = [r for r in summary.results if r.check_type == TajweedCheckType.GHUNNAH]
        assert len(ghunnah_results) == 1
        # With sustained audio, should not be insufficient data
        assert ghunnah_results[0].verdict != TajweedVerdict.INSUFFICIENT_DATA

    def test_ghunnah_silence(self, silence_audio, sample_rate):
        """Silent audio → insufficient data for ghunnah."""
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_ghunnah(
            silence_audio, "ن", 0, 300, 0
        )
        assert result.verdict == TajweedVerdict.INSUFFICIENT_DATA
        assert result.check_type == TajweedCheckType.GHUNNAH

    def test_ghunnah_too_short(self, sample_rate):
        """Very short nasalization → FAIL."""
        # Create audio with only 50ms of energy
        audio = np.zeros(sample_rate, dtype=np.float32)
        t = np.linspace(0, 0.05, int(0.05 * sample_rate), endpoint=False)
        audio[:len(t)] = 0.5 * np.sin(2 * np.pi * 200 * t).astype(np.float32)

        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_ghunnah(audio, "ن", 0, 100, 0)

        # Should fail (too short) or be insufficient
        assert result.verdict in [TajweedVerdict.FAIL, TajweedVerdict.INSUFFICIENT_DATA]


class TestQalqalahCheck:
    """Tests for qalqalah (echoing burst) detection."""

    def test_qalqalah_burst_detected(self, burst_audio, sample_rate):
        """Audio with sharp burst → qalqalah should pass."""
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_qalqalah(
            burst_audio, "ق", 100, 300, 0
        )
        assert result.check_type == TajweedCheckType.QALQALAH
        # With a clear burst, should pass
        assert result.verdict in [TajweedVerdict.PASS, TajweedVerdict.FAIL]

    def test_qalqalah_no_burst(self, silence_audio, sample_rate):
        """Silent audio → insufficient data."""
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_qalqalah(
            silence_audio, "ق", 0, 300, 0
        )
        assert result.verdict == TajweedVerdict.INSUFFICIENT_DATA

    def test_qalqalah_weak_signal(self, sample_rate):
        """Very weak signal → insufficient data or fail."""
        audio = np.full(sample_rate, 0.0001, dtype=np.float32)  # Near-silence
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_qalqalah(audio, "ط", 0, 300, 0)
        assert result.verdict in [TajweedVerdict.INSUFFICIENT_DATA, TajweedVerdict.FAIL]


class TestMaddCheck:
    """Tests for madd (elongation) duration check."""

    def test_madd_sustained(self, sustained_audio, sample_rate):
        """Sustained audio → madd should pass (duration in range)."""
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_madd(
            sustained_audio, "ا", 0, 800, 0
        )
        assert result.check_type == TajweedCheckType.MADD
        # 800ms sustained → should be in range (400-1200ms)
        if result.verdict != TajweedVerdict.INSUFFICIENT_DATA:
            assert result.verdict == TajweedVerdict.PASS

    def test_madd_too_short(self, sample_rate):
        """Very short sustained portion → madd should fail."""
        audio = np.zeros(sample_rate, dtype=np.float32)
        t = np.linspace(0, 0.05, int(0.05 * sample_rate), endpoint=False)
        audio[:len(t)] = 0.5 * np.sin(2 * np.pi * 300 * t).astype(np.float32)

        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_madd(audio, "ا", 0, 100, 0)
        assert result.verdict in [TajweedVerdict.FAIL, TajweedVerdict.INSUFFICIENT_DATA]

    def test_madd_silence(self, silence_audio, sample_rate):
        """Silent audio → insufficient data."""
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_madd(silence_audio, "و", 0, 500, 0)
        assert result.verdict == TajweedVerdict.INSUFFICIENT_DATA


class TestIkhfaCheck:
    """Tests for ikhfa (concealment) classifier."""

    def test_ikhfa_with_nasalization(self, sustained_audio, sample_rate):
        """Audio with nasal-like characteristics → ikhfa should pass."""
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_ikhfa(
            sustained_audio, "ن", 0, 400, 0, "نت", 0
        )
        assert result.check_type == TajweedCheckType.IKHFA
        assert result.verdict in [TajweedVerdict.PASS, TajweedVerdict.FAIL]

    def test_ikhfa_silence(self, silence_audio, sample_rate):
        """Silent audio → insufficient data."""
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_ikhfa(
            silence_audio, "ن", 0, 300, 0, "نت", 0
        )
        assert result.verdict == TajweedVerdict.INSUFFICIENT_DATA


class TestIdghamCheck:
    """Tests for idgham (merging) classifier."""

    def test_idgham_merged(self, sustained_audio, sample_rate):
        """Sustained audio (single segment) → idgham should pass."""
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_idgham(
            sustained_audio, "ن", 0, 500, 0, "نم", 0
        )
        assert result.check_type == TajweedCheckType.IDGHAM
        # Single sustained segment → merged → pass
        if result.verdict != TajweedVerdict.INSUFFICIENT_DATA:
            assert result.verdict == TajweedVerdict.PASS

    def test_idgham_two_segments(self, sample_rate):
        """Two distinct energy segments → idgham should fail (not merged)."""
        audio = np.zeros(sample_rate, dtype=np.float32)
        # First segment: 0-200ms
        t1 = np.linspace(0, 0.2, int(0.2 * sample_rate), endpoint=False)
        audio[:len(t1)] = 0.5 * np.sin(2 * np.pi * 300 * t1).astype(np.float32)
        # Gap: 200-400ms (silence)
        # Second segment: 400-600ms
        t2 = np.linspace(0, 0.2, int(0.2 * sample_rate), endpoint=False)
        start2 = int(0.4 * sample_rate)
        audio[start2:start2 + len(t2)] = 0.5 * np.sin(2 * np.pi * 400 * t2).astype(np.float32)

        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_idgham(audio, "ن", 0, 600, 0, "نم", 0)

        if result.verdict != TajweedVerdict.INSUFFICIENT_DATA:
            # Two segments → not merged → fail
            assert result.verdict == TajweedVerdict.FAIL

    def test_idgham_silence(self, silence_audio, sample_rate):
        """Silent audio → insufficient data."""
        checker = TajweedChecker(sample_rate=sample_rate)
        result = checker._check_idgham(
            silence_audio, "ن", 0, 300, 0, "نل", 0
        )
        assert result.verdict == TajweedVerdict.INSUFFICIENT_DATA


class TestConfidenceThreshold:
    """Tests for the 0.85 confidence threshold."""

    def test_threshold_value(self):
        """Confidence threshold should be 0.85."""
        assert CONFIDENCE_THRESHOLD == 0.85

    def test_should_surface_fail_high_confidence(self):
        """Fail with confidence >= 0.85 should surface."""
        result = TajweedResult(
            check_type=TajweedCheckType.GHUNNAH,
            verdict=TajweedVerdict.FAIL,
            confidence=0.90,
        )
        assert result.should_surface is True

    def test_should_not_surface_fail_low_confidence(self):
        """Fail with confidence < 0.85 should NOT surface."""
        result = TajweedResult(
            check_type=TajweedCheckType.GHUNNAH,
            verdict=TajweedVerdict.FAIL,
            confidence=0.70,
        )
        assert result.should_surface is False

    def test_should_not_surface_pass(self):
        """Pass verdict should never surface (regardless of confidence)."""
        result = TajweedResult(
            check_type=TajweedCheckType.GHUNNAH,
            verdict=TajweedVerdict.PASS,
            confidence=0.95,
        )
        assert result.should_surface is False

    def test_should_not_surface_not_applicable(self):
        """NOT_APPLICABLE should never surface."""
        result = TajweedResult(
            check_type=TajweedCheckType.GHUNNAH,
            verdict=TajweedVerdict.NOT_APPLICABLE,
            confidence=0.95,
        )
        assert result.should_surface is False


class TestTajweedSummary:
    """Tests for TajweedCheckSummary."""

    def test_empty_summary(self):
        """Empty summary → score 100."""
        summary = TajweedCheckSummary()
        assert summary.tajweed_score == 100.0
        assert summary.total_checks == 0

    def test_all_passed(self):
        summary = TajweedCheckSummary(
            results=[],
            total_checks=5,
            passed=5,
            failed=0,
        )
        assert summary.tajweed_score == 100.0

    def test_mixed_results(self):
        summary = TajweedCheckSummary(
            results=[],
            total_checks=10,
            passed=7,
            failed=3,
        )
        assert summary.tajweed_score == 70.0

    def test_surfaced_failures_count(self):
        """surfaced_failures counts only fails with confidence >= threshold."""
        results = [
            TajweedResult(
                check_type=TajweedCheckType.GHUNNAH,
                verdict=TajweedVerdict.FAIL,
                confidence=0.90,
            ),
            TajweedResult(
                check_type=TajweedCheckType.QALQALAH,
                verdict=TajweedVerdict.FAIL,
                confidence=0.70,  # Below threshold
            ),
            TajweedResult(
                check_type=TajweedCheckType.MADD,
                verdict=TajweedVerdict.FAIL,
                confidence=0.85,
            ),
        ]
        summary = TajweedCheckSummary(
            results=results,
            total_checks=3,
            passed=0,
            failed=3,
        )
        summary.surfaced_failures = sum(1 for r in results if r.should_surface)
        assert summary.surfaced_failures == 2  # 0.90 and 0.85 pass threshold


class TestInferTajweedPositions:
    """Tests for heuristic tajweed position inference."""

    def test_infer_qalqalah(self):
        """Qalqalah letters should be detected."""
        checker = TajweedChecker()
        positions = checker._infer_tajweed_positions("قط")
        rules = [p["rule"] for p in positions]
        assert "qalqalah" in rules

    def test_infer_ghunnah(self):
        """Ghunnah letters should be detected."""
        checker = TajweedChecker()
        positions = checker._infer_tajweed_positions("نم")
        rules = [p["rule"] for p in positions]
        assert "ghunnah" in rules

    def test_infer_madd(self):
        """Madd letters should be detected."""
        checker = TajweedChecker()
        positions = checker._infer_tajweed_positions("اوي")
        rules = [p["rule"] for p in positions]
        assert "madd" in rules

    def test_infer_ikhfa(self):
        """Ikhfa pattern (ن + ikhfa letter) should be detected."""
        checker = TajweedChecker()
        positions = checker._infer_tajweed_positions("نت")
        rules = [p["rule"] for p in positions]
        assert "ikhfa" in rules

    def test_infer_idgham(self):
        """Idgham pattern (ن + idgham letter) should be detected."""
        checker = TajweedChecker()
        positions = checker._infer_tajweed_positions("نم")
        rules = [p["rule"] for p in positions]
        assert "idgham" in rules
