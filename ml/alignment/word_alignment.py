"""Word-level alignment using Levenshtein/Needleman-Wunsch.

Compares ASR hypothesis tokens against expected ayah text
to detect omissions, insertions, and mispronunciations.
"""
from typing import Optional
import numpy as np
import structlog

log = structlog.get_logger()


def align_words(
    expected: list[str],
    hypothesis: list[str],
    asr_confidence: float = 0.85,
    char_distance_threshold: float = 0.3,
) -> list[dict]:
    """Align hypothesis words against expected words.

    Uses dynamic programming (Levenshtein at word level) to find
    the optimal alignment, then classifies each word.

    Returns list of verdicts:
      - "correct": matched with high confidence
      - "mispronounced": matched but low confidence or high char distance
      - "omitted": expected word with no match
      - "inserted_extra": hypothesis word with no expected match
      - "low_confidence": uncertain — NO visual mark shown
    """
    n, m = len(expected), len(hypothesis)

    # DP table for alignment
    # 0 = match, 1 = deletion (omitted), 2 = insertion (extra), 3 = substitution
    dp = np.zeros((n + 1, m + 1), dtype=int)
    dp[:, 0] = 1  # all deletions
    dp[0, :] = 2  # all insertions

    # Fill DP table
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if expected[i - 1] == hypothesis[j - 1]:
                dp[i][j] = 0  # match
            else:
                # Cost: substitution vs deletion vs insertion
                sub_cost = _char_levenshtein(expected[i - 1], hypothesis[j - 1])
                del_cost = 1
                ins_cost = 1

                if sub_cost <= del_cost and sub_cost <= ins_cost:
                    dp[i][j] = 3  # substitution
                elif del_cost <= ins_cost:
                    dp[i][j] = 1  # deletion
                else:
                    dp[i][j] = 2  # insertion

    # Backtrack to find alignment
    alignment = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] in (0, 3):
            alignment.append((i - 1, j - 1, dp[i][j]))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == 1:
            alignment.append((i - 1, None, 1))
            i -= 1
        elif j > 0 and dp[i][j] == 2:
            alignment.append((None, j - 1, 2))
            j -= 1
        else:
            i -= 1
            j -= 1

    alignment.reverse()

    # Classify each alignment entry
    results = []
    for exp_idx, hyp_idx, op in alignment:
        if op == 0:
            # Exact match
            results.append({
                "expected_idx": exp_idx,
                "verdict": "correct",
                "confidence": asr_confidence,
            })
        elif op == 3:
            # Substitution — check if it's mispronunciation or low confidence
            char_dist = _char_levenshtein(expected[exp_idx], hypothesis[hyp_idx])
            max_len = max(len(expected[exp_idx]), len(hyp_idx and hypothesis[hyp_idx] or ""))
            ratio = char_dist / max_len if max_len > 0 else 1.0

            if ratio <= char_distance_threshold and asr_confidence >= 0.85:
                results.append({
                    "expected_idx": exp_idx,
                    "hyp_idx": hyp_idx,
                    "verdict": "mispronounced",
                    "char_distance": char_dist,
                    "confidence": asr_confidence,
                })
            else:
                results.append({
                    "expected_idx": exp_idx,
                    "hyp_idx": hyp_idx,
                    "verdict": "low_confidence",
                    "char_distance": char_dist,
                    "confidence": asr_confidence,
                })
        elif op == 1:
            # Omitted word
            results.append({
                "expected_idx": exp_idx,
                "verdict": "omitted",
            })
        elif op == 2:
            # Inserted extra word
            results.append({
                "hyp_idx": hyp_idx,
                "verdict": "inserted_extra",
            })

    return results


def _char_levenshtein(s1: str, s2: str) -> int:
    """Character-level Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _char_levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]
