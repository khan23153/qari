"""
Tests for score computation (fluency, tajweed, overall).
"""

import pytest
from ml.alignment.word_alignment import (
    WordAligner,
    WordVerdict,
    AlignmentResult,
    AlignedWord,
)
from ml.tajweed.checks import (
    TajweedCheckSummary,
    TajweedResult,
    TajweedCheckType,
    TajweedVerdict,
)
from ml.evaluation.scoring import compute_scores, ScoreBreakdown


class TestFluencyScore:
    """Tests for fluency score computation."""

    def test_perfect_fluency(self):
        """All words correct → fluency = 100."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن", "الرحيم"]
        hyp = ["بسم", "الله", "الرحمن", "الرحيم"]
        alignment = aligner.align(ref, hyp)
        scores = compute_scores(alignment)

        assert scores.fluency == 100.0
        assert scores.correct_words == 4
        assert scores.expected_words == 4

    def test_zero_fluency(self):
        """All words omitted → fluency = 0."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن"]
        alignment = aligner.align(ref, [])
        scores = compute_scores(alignment)

        assert scores.fluency == 0.0
        assert scores.omitted_words == 3

    def test_partial_fluency(self):
        """Half words correct → fluency = 50."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن", "الرحيم"]
        hyp = ["بسم", "الله"]  # 2 of 4 correct
        alignment = aligner.align(ref, hyp)
        scores = compute_scores(alignment)

        assert scores.fluency == 50.0

    def test_fluency_with_mispronunciation(self):
        """Mispronounced words reduce fluency."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن", "الرحيم"]
        hyp = ["بسم", "ربي", "الرحمن", "الرحيم"]  # 3 correct, 1 mispronounced
        alignment = aligner.align(ref, hyp, confidences=[0.9, 0.9, 0.9, 0.9])
        scores = compute_scores(alignment)

        assert scores.fluency == 75.0  # 3/4 = 75%
        assert scores.mispronounced_words == 1

    def test_low_confidence_partial_credit(self):
        """Low-confidence words get 0.5 partial credit."""
        aligner = WordAligner(low_confidence_threshold=0.50)
        ref = ["بسم", "الله", "الرحمن", "الرحيم"]
        hyp = ["بسم", "ربي", "الرحمن", "الرحيم"]
        # Give second word low confidence → low_confidence (0.5 credit)
        alignment = aligner.align(ref, hyp, confidences=[0.9, 0.30, 0.9, 0.9])
        scores = compute_scores(alignment)

        # 3 correct + 0.5 low_conf = 3.5 / 4 = 87.5%
        assert scores.fluency == 87.5


class TestTajweedScore:
    """Tests for tajweed score computation."""

    def test_no_tajweed_checks(self):
        """No tajweed summary → tajweed score defaults to 100."""
        aligner = WordAligner()
        alignment = aligner.align(["بسم"], ["بسم"])
        scores = compute_scores(alignment, tajweed_summary=None)

        assert scores.tajweed == 100.0

    def test_all_tajweed_passed(self):
        """All tajweed checks pass → tajweed = 100."""
        aligner = WordAligner()
        alignment = aligner.align(["بسم"], ["بسم"])
        summary = TajweedCheckSummary(
            results=[
                TajweedResult(
                    check_type=TajweedCheckType.GHUNNAH,
                    verdict=TajweedVerdict.PASS,
                    confidence=0.9,
                ),
                TajweedResult(
                    check_type=TajweedCheckType.QALQALAH,
                    verdict=TajweedVerdict.PASS,
                    confidence=0.9,
                ),
            ],
            total_checks=2,
            passed=2,
            failed=0,
        )
        scores = compute_scores(alignment, summary)

        assert scores.tajweed == 100.0
        assert scores.passed_checks == 2

    def test_half_tajweed_failed(self):
        """Half of tajweed checks fail → tajweed = 50."""
        aligner = WordAligner()
        alignment = aligner.align(["بسم"], ["بسم"])
        summary = TajweedCheckSummary(
            results=[
                TajweedResult(
                    check_type=TajweedCheckType.GHUNNAH,
                    verdict=TajweedVerdict.PASS,
                    confidence=0.9,
                ),
                TajweedResult(
                    check_type=TajweedCheckType.QALQALAH,
                    verdict=TajweedVerdict.FAIL,
                    confidence=0.9,
                ),
            ],
            total_checks=2,
            passed=1,
            failed=1,
        )
        scores = compute_scores(alignment, summary)

        assert scores.tajweed == 50.0

    def test_not_applicable_excluded(self):
        """NOT_APPLICABLE and INSUFFICIENT_DATA checks are excluded from score."""
        aligner = WordAligner()
        alignment = aligner.align(["بسم"], ["بسم"])
        summary = TajweedCheckSummary(
            results=[
                TajweedResult(
                    check_type=TajweedCheckType.GHUNNAH,
                    verdict=TajweedVerdict.PASS,
                    confidence=0.9,
                ),
                TajweedResult(
                    check_type=TajweedCheckType.IKHFA,
                    verdict=TajweedVerdict.NOT_APPLICABLE,
                    confidence=0.0,
                ),
                TajweedResult(
                    check_type=TajweedCheckType.IDGHAM,
                    verdict=TajweedVerdict.INSUFFICIENT_DATA,
                    confidence=0.0,
                ),
            ],
            total_checks=3,
            passed=1,
            failed=0,
            not_applicable=1,
            insufficient_data=1,
        )
        scores = compute_scores(alignment, summary)

        # Only 1 applicable check (passed) → 100%
        assert scores.tajweed == 100.0


class TestOverallScore:
    """Tests for overall score computation."""

    def test_perfect_scores(self):
        """Perfect fluency + perfect tajweed → overall = 100."""
        aligner = WordAligner()
        alignment = aligner.align(["بسم", "الله"], ["بسم", "الله"])
        scores = compute_scores(alignment)

        assert scores.overall == 100.0
        assert scores.grade == "A"

    def test_weighting(self):
        """Verify 0.7 * fluency + 0.3 * tajweed weighting."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن", "الرحيم"]
        hyp = ["بسم", "الله"]  # 50% fluency
        alignment = aligner.align(ref, hyp)
        summary = TajweedCheckSummary(
            results=[
                TajweedResult(
                    check_type=TajweedCheckType.GHUNNAH,
                    verdict=TajweedVerdict.PASS,
                    confidence=0.9,
                ),
                TajweedResult(
                    check_type=TajweedCheckType.QALQALAH,
                    verdict=TajweedVerdict.FAIL,
                    confidence=0.9,
                ),
            ],
            total_checks=2,
            passed=1,
            failed=1,
        )
        scores = compute_scores(alignment, summary)

        # fluency = 50, tajweed = 50
        # overall = 0.7 * 50 + 0.3 * 50 = 50
        assert scores.overall == 50.0

    def test_custom_weights(self):
        """Test with custom weights."""
        aligner = WordAligner()
        ref = ["بسم", "الله"]
        hyp = ["بسم"]  # 50% fluency
        alignment = aligner.align(ref, hyp)
        scores = compute_scores(
            alignment, tajweed_summary=None,
            fluency_weight=0.5, tajweed_weight=0.5,
        )

        # fluency = 50, tajweed = 100 (no checks)
        # overall = 0.5 * 50 + 0.5 * 100 = 75
        assert scores.overall == 75.0


class TestGrading:
    """Tests for letter grade assignment."""

    def test_grade_a(self):
        """Score >= 90 → A."""
        scores = ScoreBreakdown(overall=95.0)
        assert scores.grade == "A"
        assert scores.grade_color == "green"

    def test_grade_b(self):
        scores = ScoreBreakdown(overall=85.0)
        assert scores.grade == "B"
        assert scores.grade_color == "green"

    def test_grade_c(self):
        scores = ScoreBreakdown(overall=75.0)
        assert scores.grade == "C"
        assert scores.grade_color == "yellow"

    def test_grade_d(self):
        scores = ScoreBreakdown(overall=65.0)
        assert scores.grade == "D"
        assert scores.grade_color == "orange"

    def test_grade_f(self):
        scores = ScoreBreakdown(overall=50.0)
        assert scores.grade == "F"
        assert scores.grade_color == "red"

    def test_to_dict(self):
        """Test serialization to dict."""
        scores = ScoreBreakdown(
            fluency=80.0, tajweed=90.0, overall=83.0,
            correct_words=8, expected_words=10,
        )
        d = scores.to_dict()
        assert d["fluency"] == 80.0
        assert d["overall"] == 83.0
        assert d["grade"] == "B"
        assert d["correct_words"] == 8
