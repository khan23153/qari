"""
Scoring module — computes fluency, tajweed, and overall scores.

Fluency = (correct words / expected words) * 100
Tajweed = (passed checks / total applicable checks) * 100
Overall = 0.7 * fluency + 0.3 * tajweed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..alignment.word_alignment import AlignmentResult, WordVerdict
from ..tajweed.checks import TajweedCheckSummary


# ── Scoring weights ──────────────────────────────────────────────────────────

FLUENCY_WEIGHT = 0.7
TAJWEED_WEIGHT = 0.3


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class ScoreBreakdown:
    """Detailed score breakdown for a recitation."""
    fluency: float = 0.0          # 0-100
    tajweed: float = 0.0         # 0-100
    overall: float = 0.0         # 0-100
    correct_words: int = 0
    expected_words: int = 0
    passed_checks: int = 0
    total_checks: int = 0
    omitted_words: int = 0
    mispronounced_words: int = 0
    inserted_words: int = 0
    low_confidence_words: int = 0
    surfaced_tajweed_failures: int = 0

    @property
    def grade(self) -> str:
        """Letter grade based on overall score."""
        if self.overall >= 90:
            return "A"
        elif self.overall >= 80:
            return "B"
        elif self.overall >= 70:
            return "C"
        elif self.overall >= 60:
            return "D"
        else:
            return "F"

    @property
    def grade_color(self) -> str:
        """Color associated with the grade for UI rendering."""
        if self.overall >= 80:
            return "green"
        elif self.overall >= 70:
            return "yellow"
        elif self.overall >= 60:
            return "orange"
        else:
            return "red"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "fluency": round(self.fluency, 2),
            "tajweed": round(self.tajweed, 2),
            "overall": round(self.overall, 2),
            "grade": self.grade,
            "grade_color": self.grade_color,
            "correct_words": self.correct_words,
            "expected_words": self.expected_words,
            "passed_checks": self.passed_checks,
            "total_checks": self.total_checks,
            "omitted_words": self.omitted_words,
            "mispronounced_words": self.mispronounced_words,
            "inserted_words": self.inserted_words,
            "low_confidence_words": self.low_confidence_words,
            "surfaced_tajweed_failures": self.surfaced_tajweed_failures,
        }


# ── Scoring functions ────────────────────────────────────────────────────────

def compute_scores(
    alignment: AlignmentResult,
    tajweed_summary: Optional[TajweedCheckSummary] = None,
    *,
    fluency_weight: float = FLUENCY_WEIGHT,
    tajweed_weight: float = TAJWEED_WEIGHT,
) -> ScoreBreakdown:
    """
    Compute fluency, tajweed, and overall scores from alignment and tajweed results.

    Fluency Score:
        (correct_words / expected_words) * 100
        Where correct_words = words with CORRECT verdict.
        expected_words = total reference words.
        Omissions and mispronunciations reduce fluency.
        Low-confidence words are counted as 0.5 correct (partial credit).

    Tajweed Score:
        (passed_checks / total_applicable_checks) * 100
        Where total_applicable_checks = passed + failed.
        Not-applicable and insufficient-data checks are excluded.

    Overall Score:
        fluency_weight * fluency + tajweed_weight * tajweed

    Parameters
    ----------
    alignment : AlignmentResult
        Word alignment result with verdicts.
    tajweed_summary : TajweedCheckSummary, optional
        Tajweed check summary. If None, tajweed score defaults to 100
        (no tajweed checks performed).
    fluency_weight : float, default 0.7
        Weight for fluency in overall score.
    tajweed_weight : float, default 0.3
        Weight for tajweed in overall score.

    Returns
    -------
    ScoreBreakdown
        Detailed score breakdown.
    """
    # ── Fluency ──────────────────────────────────────────────────────────────
    expected = len(alignment.reference_words)
    correct = alignment.match_count
    omitted = alignment.omission_count
    mispronounced = alignment.mismatch_count
    inserted = alignment.insertion_count
    low_conf = alignment.low_confidence_count

    if expected > 0:
        # Low-confidence words get partial credit (0.5)
        effective_correct = correct + (low_conf * 0.5)
        fluency = (effective_correct / expected) * 100.0
    else:
        fluency = 0.0

    # Cap at 100
    fluency = min(fluency, 100.0)

    # ── Tajweed ──────────────────────────────────────────────────────────────
    if tajweed_summary is not None:
        applicable = tajweed_summary.passed + tajweed_summary.failed
        if applicable > 0:
            tajweed = (tajweed_summary.passed / applicable) * 100.0
        else:
            tajweed = 100.0  # No applicable checks → perfect by default
        surfaced_failures = tajweed_summary.surfaced_failures
        passed_checks = tajweed_summary.passed
        total_checks = tajweed_summary.total_checks
    else:
        tajweed = 100.0
        surfaced_failures = 0
        passed_checks = 0
        total_checks = 0

    # ── Overall ──────────────────────────────────────────────────────────────
    overall = (fluency_weight * fluency) + (tajweed_weight * tajweed)
    overall = min(overall, 100.0)

    return ScoreBreakdown(
        fluency=fluency,
        tajweed=tajweed,
        overall=overall,
        correct_words=correct,
        expected_words=expected,
        passed_checks=passed_checks,
        total_checks=total_checks,
        omitted_words=omitted,
        mispronounced_words=mispronounced,
        inserted_words=inserted,
        low_confidence_words=low_conf,
        surfaced_tajweed_failures=surfaced_failures,
    )
