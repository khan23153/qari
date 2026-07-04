"""
Precision evaluation framework for the Qari ML engine.

Measures word-verdict precision across cohorts (beginner, intermediate,
advanced) and checks against the 90% precision gate required by the spec.

Precision = (correctly classified verdicts / total verdicts made) * 100

A "correctly classified verdict" means the system's verdict matches the
human-annotated ground truth label for that word.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from ..alignment.word_alignment import AlignmentResult, WordVerdict

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

PRECISION_GATE = 0.90  # 90% word-verdict precision gate
MIN_EVALUATION_SET_SIZE = 500  # Minimum number of recordings in evaluation set


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class WordEvaluation:
    """A single word-level evaluation entry with ground truth."""
    system_verdict: WordVerdict
    ground_truth: WordVerdict
    word: str
    is_correct: bool

    @property
    def verdict_match(self) -> bool:
        return self.system_verdict == self.ground_truth


@dataclass
class CohortResult:
    """Evaluation results for a single cohort (e.g., beginner)."""
    cohort_name: str
    total_recordings: int = 0
    total_words: int = 0
    correct_verdicts: int = 0
    word_verdict_precision: float = 0.0
    per_verdict_precision: dict[str, float] = field(default_factory=dict)
    confusion_matrix: dict[str, dict[str, int]] = field(default_factory=dict)

    def compute_precision(self) -> None:
        """Compute precision from correct_verdicts and total_words."""
        if self.total_words > 0:
            self.word_verdict_precision = self.correct_verdicts / self.total_words
        else:
            self.word_verdict_precision = 0.0

    def compute_per_verdict_precision(self, evaluations: list[WordEvaluation]) -> None:
        """Compute precision for each verdict type."""
        verdict_counts: dict[str, int] = {}
        verdict_correct: dict[str, int] = {}

        for ev in evaluations:
            gt = ev.ground_truth.value
            verdict_counts[gt] = verdict_counts.get(gt, 0) + 1
            if ev.is_correct:
                verdict_correct[gt] = verdict_correct.get(gt, 0) + 1

        self.per_verdict_precision = {}
        for v, count in verdict_counts.items():
            correct = verdict_correct.get(v, 0)
            self.per_verdict_precision[v] = correct / count if count > 0 else 0.0

    def compute_confusion_matrix(self, evaluations: list[WordEvaluation]) -> None:
        """Build a confusion matrix from evaluations."""
        self.confusion_matrix = {}
        for ev in evaluations:
            gt = ev.ground_truth.value
            sys_v = ev.system_verdict.value
            if gt not in self.confusion_matrix:
                self.confusion_matrix[gt] = {}
            self.confusion_matrix[gt][sys_v] = self.confusion_matrix[gt].get(sys_v, 0) + 1


@dataclass
class EvaluationReport:
    """Full evaluation report across all cohorts."""
    cohorts: list[CohortResult] = field(default_factory=list)
    total_recordings: int = 0
    total_words: int = 0
    overall_precision: float = 0.0
    passes_gate: bool = False
    gate_threshold: float = PRECISION_GATE
    meets_size_requirement: bool = False
    min_size: int = MIN_EVALUATION_SET_SIZE

    def compute_overall(self) -> None:
        """Compute overall precision and gate status."""
        self.total_recordings = sum(c.total_recordings for c in self.cohorts)
        self.total_words = sum(c.total_words for c in self.cohorts)
        total_correct = sum(c.correct_verdicts for c in self.cohorts)

        if self.total_words > 0:
            self.overall_precision = total_correct / self.total_words
        else:
            self.overall_precision = 0.0

        self.passes_gate = self.overall_precision >= self.gate_threshold
        self.meets_size_requirement = self.total_recordings >= self.min_size

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_recordings": self.total_recordings,
            "total_words": self.total_words,
            "overall_precision": round(self.overall_precision, 4),
            "passes_gate": self.passes_gate,
            "gate_threshold": self.gate_threshold,
            "meets_size_requirement": self.meets_size_requirement,
            "min_size": self.min_size,
            "cohorts": [
                {
                    "cohort_name": c.cohort_name,
                    "total_recordings": c.total_recordings,
                    "total_words": c.total_words,
                    "correct_verdicts": c.correct_verdicts,
                    "word_verdict_precision": round(c.word_verdict_precision, 4),
                    "per_verdict_precision": {
                        k: round(v, 4) for k, v in c.per_verdict_precision.items()
                    },
                    "confusion_matrix": c.confusion_matrix,
                }
                for c in self.cohorts
            ],
        }

    def summary(self) -> str:
        """Human-readable summary of the evaluation."""
        status = "PASS" if self.passes_gate else "FAIL"
        size_status = "OK" if self.meets_size_requirement else "INSUFFICIENT"
        lines = [
            f"=== Qari ML Evaluation Report ===",
            f"Overall Precision: {self.overall_precision:.2%}",
            f"Precision Gate ({self.gate_threshold:.0%}): {status}",
            f"Evaluation Set Size: {self.total_recordings} (min {self.min_size}) — {size_status}",
            f"Total Words Evaluated: {self.total_words}",
            "",
        ]
        for c in self.cohorts:
            lines.append(f"  [{c.cohort_name}] {c.total_recordings} recordings, "
                        f"{c.total_words} words, precision={c.word_verdict_precision:.2%}")
        return "\n".join(lines)


# ── Precision Evaluator ──────────────────────────────────────────────────────

class PrecisionEvaluator:
    """
    Evaluate word-verdict precision of the ML pipeline against ground truth.

    Parameters
    ----------
    gate_threshold : float, default 0.90
        Minimum precision required to pass the gate.
    min_set_size : int, default 500
        Minimum number of recordings in the evaluation set.
    """

    def __init__(
        self,
        gate_threshold: float = PRECISION_GATE,
        min_set_size: int = MIN_EVALUATION_SET_SIZE,
    ) -> None:
        self.gate_threshold = gate_threshold
        self.min_set_size = min_set_size

    def evaluate_recording(
        self,
        alignment: AlignmentResult,
        ground_truth_verdicts: list[WordVerdict],
    ) -> list[WordEvaluation]:
        """
        Evaluate a single recording's word verdicts against ground truth.

        Parameters
        ----------
        alignment : AlignmentResult
            The pipeline's alignment result with system verdicts.
        ground_truth_verdicts : list[WordVerdict]
            Human-annotated ground truth verdicts, one per aligned word.

        Returns
        -------
        list[WordEvaluation]
            Per-word evaluation entries.
        """
        evaluations: list[WordEvaluation] = []

        for i, aligned_word in enumerate(alignment.aligned_words):
            if i >= len(ground_truth_verdicts):
                break

            gt = ground_truth_verdicts[i]
            sys_v = aligned_word.verdict
            is_correct = (sys_v == gt)

            evaluations.append(WordEvaluation(
                system_verdict=sys_v,
                ground_truth=gt,
                word=aligned_word.reference or aligned_word.hypothesis or "",
                is_correct=is_correct,
            ))

        return evaluations

    def evaluate_cohort(
        self,
        cohort_name: str,
        recordings: list[tuple[AlignmentResult, list[WordVerdict]]],
    ) -> CohortResult:
        """
        Evaluate a cohort of recordings.

        Parameters
        ----------
        cohort_name : str
            Name of the cohort (e.g., "beginner", "intermediate").
        recordings : list[tuple[AlignmentResult, list[WordVerdict]]]
            List of (alignment_result, ground_truth_verdicts) tuples.

        Returns
        -------
        CohortResult
            Evaluation results for this cohort.
        """
        all_evaluations: list[WordEvaluation] = []

        for alignment, gt_verdicts in recordings:
            evals = self.evaluate_recording(alignment, gt_verdicts)
            all_evaluations.extend(evals)

        result = CohortResult(
            cohort_name=cohort_name,
            total_recordings=len(recordings),
            total_words=len(all_evaluations),
            correct_verdicts=sum(1 for e in all_evaluations if e.is_correct),
        )
        result.compute_precision()
        result.compute_per_verdict_precision(all_evaluations)
        result.compute_confusion_matrix(all_evaluations)

        return result

    def evaluate(
        self,
        cohorts: dict[str, list[tuple[AlignmentResult, list[WordVerdict]]]],
    ) -> EvaluationReport:
        """
        Run full evaluation across all cohorts.

        Parameters
        ----------
        cohorts : dict[str, list[tuple[AlignmentResult, list[WordVerdict]]]]
            Mapping of cohort name → list of (alignment, ground_truth) tuples.

        Returns
        -------
        EvaluationReport
            Full evaluation report with per-cohort and overall results.
        """
        cohort_results: list[CohortResult] = []

        for name, recordings in cohorts.items():
            logger.info("Evaluating cohort '%s' with %d recordings", name, len(recordings))
            result = self.evaluate_cohort(name, recordings)
            cohort_results.append(result)

        report = EvaluationReport(
            cohorts=cohort_results,
            gate_threshold=self.gate_threshold,
            min_size=self.min_set_size,
        )
        report.compute_overall()

        logger.info("Evaluation complete: precision=%.2f%%, gate=%s",
                    report.overall_precision * 100,
                    "PASS" if report.passes_gate else "FAIL")

        return report

    def save_report(self, report: EvaluationReport, filepath: str | Path) -> None:
        """Save evaluation report to a JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info("Report saved to %s", filepath)

    @staticmethod
    def load_ground_truth(filepath: str | Path) -> list[WordVerdict]:
        """
        Load ground truth verdicts from a JSON file.

        Expected format: a list of verdict strings, e.g.:
        ["correct", "correct", "omitted", "mispronounced", ...]
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [WordVerdict(v) for v in data]
