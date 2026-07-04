"""Scoring and result aggregation for recitation sessions."""
from typing import Optional
import structlog

log = structlog.get_logger()


def compute_scores(
    word_verdicts: list[dict],
    tajweed_results: list[dict] | None = None,
) -> dict:
    """Compute fluency, tajweed, and overall scores.

    fluency_score = correct words / expected words × 100
    tajweed_score = passed checks / total checks × 100 (null in Phase 1)
    overall = 0.7 * fluency + 0.3 * tajweed
    """
    expected_words = [v for v in word_verdicts if v.get("expected_idx") is not None]
    correct_words = [v for v in word_verdicts if v["verdict"] == "correct"]

    if expected_words:
        fluency_score = int(len(correct_words) / len(expected_words) * 100)
    else:
        fluency_score = 0

    tajweed_score = None
    if tajweed_results:
        passed = sum(1 for t in tajweed_results if t.get("pass"))
        total = len(tajweed_results)
        tajweed_score = int(passed / total * 100) if total > 0 else None

    if tajweed_score is not None:
        overall = int(0.7 * fluency_score + 0.3 * tajweed_score)
    else:
        overall = fluency_score

    return {
        "overall_score": overall,
        "fluency_score": fluency_score,
        "tajweed_score": tajweed_score,
    }
