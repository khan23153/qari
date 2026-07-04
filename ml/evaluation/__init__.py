"""Evaluation sub-package: scoring and precision evaluation."""

from .scoring import compute_scores, ScoreBreakdown
from .evaluate import PrecisionEvaluator, EvaluationReport, CohortResult

__all__ = [
    "compute_scores",
    "ScoreBreakdown",
    "PrecisionEvaluator",
    "EvaluationReport",
    "CohortResult",
]
