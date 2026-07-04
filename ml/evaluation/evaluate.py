"""ML evaluation — word-verdict precision measurement.

Gate: ≥90% word-verdict precision on beginner eval set,
measured per accent cohort, before red highlighting is enabled.
"""
import json
from typing import list
import structlog

log = structlog.get_logger()


def evaluate_precision(
    predictions: list[dict],
    ground_truth: list[dict],
) -> dict:
    """Evaluate word-verdict precision against labeled ground truth.

    Args:
        predictions: list of {"session_id", "words": [{"key", "verdict"}]}
        ground_truth: list of {"session_id", "words": [{"key", "verdict"}]}

    Returns:
        {"overall_precision": float, "per_cohort": dict, "meets_gate": bool}
    """
    pred_by_session = {p["session_id"]: p for p in predictions}
    gt_by_session = {g["session_id"]: g for g in ground_truth}

    correct = 0
    total = 0
    per_cohort = {}

    for session_id, gt in gt_by_session.items():
        pred = pred_by_session.get(session_id)
        if not pred:
            continue

        cohort = gt.get("accent_cohort", "unknown")
        if cohort not in per_cohort:
            per_cohort[cohort] = {"correct": 0, "total": 0}

        gt_words = {w["key"]: w["verdict"] for w in gt["words"]}
        pred_words = {w["key"]: w["verdict"] for w in pred["words"]}

        for key, gt_verdict in gt_words.items():
            pred_verdict = pred_words.get(key)
            if pred_verdict:
                total += 1
                per_cohort[cohort]["total"] += 1
                if pred_verdict == gt_verdict:
                    correct += 1
                    per_cohort[cohort]["correct"] += 1

    overall_precision = correct / total if total > 0 else 0.0

    cohort_precision = {}
    for cohort, counts in per_cohort.items():
        p = counts["correct"] / counts["total"] if counts["total"] > 0 else 0.0
        cohort_precision[cohort] = {
            "precision": p,
            "samples": counts["total"],
            "meets_gate": p >= 0.90,
        }

    return {
        "overall_precision": overall_precision,
        "total_samples": total,
        "per_cohort": cohort_precision,
        "meets_gate": overall_precision >= 0.90,
    }


if __name__ == "__main__":
    # Example usage
    print("Run with labeled eval set:")
    print("  python -m ml.evaluation.evaluate --predictions pred.json --ground-truth gt.json")
