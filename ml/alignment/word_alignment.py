"""
Word-level alignment using dynamic programming (Needleman-Wunsch / Levenshtein).

Aligns ASR hypothesis words against reference (expected) words from the Quran
text and classifies each word with a verdict:

  - correct          : word matches the reference
  - mispronounced    : word is present but differs from reference (substitution)
  - omitted          : reference word is missing from the hypothesis
  - inserted_extra   : hypothesis word has no corresponding reference word
  - low_confidence   : ASR confidence too low to make a determination

The alignment uses a standard Needleman-Wunsch global alignment algorithm
with custom scoring for match, mismatch (substitution), and gap (insertion/deletion).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ── Verdict classification ───────────────────────────────────────────────────

class WordVerdict(str, Enum):
    """Classification of each word in the alignment."""
    CORRECT = "correct"
    MISPRONOUNCED = "mispronounced"
    OMITTED = "omitted"
    INSERTED_EXTRA = "inserted_extra"
    LOW_CONFIDENCE = "low_confidence"


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class AlignedWord:
    """A single aligned word with its verdict and metadata."""
    reference: Optional[str]      # Expected word (None for insertions)
    hypothesis: Optional[str]     # Recognized word (None for omissions)
    verdict: WordVerdict
    ref_index: Optional[int]      # Index in reference sequence (None for insertions)
    hyp_index: Optional[int]      # Index in hypothesis sequence (None for omissions)
    confidence: float = 1.0       # ASR confidence if available
    similarity: float = 1.0       # Character-level similarity for substitutions


@dataclass
class AlignmentResult:
    """Full alignment result."""
    aligned_words: list[AlignedWord] = field(default_factory=list)
    reference_words: list[str] = field(default_factory=list)
    hypothesis_words: list[str] = field(default_factory=list)
    score: float = 0.0             # Alignment score
    match_count: int = 0
    mismatch_count: int = 0
    omission_count: int = 0
    insertion_count: int = 0
    low_confidence_count: int = 0

    @property
    def total_verdicts(self) -> int:
        return len(self.aligned_words)

    @property
    def correct_ratio(self) -> float:
        """Ratio of correct words to total reference words."""
        if not self.reference_words:
            return 0.0
        return self.match_count / len(self.reference_words)

    def get_verdicts_for_reference(self) -> list[AlignedWord]:
        """Return only words that correspond to a reference position (excludes insertions)."""
        return [w for w in self.aligned_words if w.ref_index is not None]


# ── Alignment scoring ────────────────────────────────────────────────────────

# Default scoring for Needleman-Wunsch
MATCH_SCORE = 2
MISMATCH_SCORE = -1
GAP_SCORE = -2

# Confidence threshold below which a word is marked low_confidence
LOW_CONFIDENCE_THRESHOLD = 0.50

# Character similarity threshold for distinguishing mispronounced vs low_confidence
MISPRONUNCIATION_SIMILARITY_THRESHOLD = 0.3

# Character similarity at/above which a differing word is treated as a correct
# near-match (ASR/tokenization noise) instead of a mispronunciation.
NEAR_MATCH_CORRECT_THRESHOLD = 0.85


def _char_similarity(s1: str, s2: str) -> float:
    """
    Compute character-level similarity between two strings.

    Uses a normalized Levenshtein distance: similarity = 1 - dist / max_len.

    Parameters
    ----------
    s1, s2 : str
        Strings to compare.

    Returns
    -------
    float
        Similarity in [0, 1]. 1.0 = identical, 0.0 = completely different.
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    dist = _levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 - (dist / max_len)


def _levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein edit distance between two strings.

    Uses O(min(m,n)) space optimization.

    Parameters
    ----------
    s1, s2 : str
        Strings to compare.

    Returns
    -------
    int
        Edit distance (number of insertions, deletions, substitutions).
    """
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    if len(s2) == 0:
        return len(s1)

    previous = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous[j + 1] + 1
            deletions = current[j] + 1
            substitutions = previous[j] + (c1 != c2)
            current.append(min(insertions, deletions, substitutions))
        previous = current

    return previous[-1]


# ── Word Aligner ─────────────────────────────────────────────────────────────

class WordAligner:
    """
    Word-level aligner using Needleman-Wunsch dynamic programming.

    Aligns the ASR hypothesis word sequence against the reference (expected)
    word sequence from the Quran text. Each aligned position is classified
    with a WordVerdict.

    Parameters
    ----------
    match_score : int, default 2
        Score for matching words.
    mismatch_score : int, default -1
        Score for substituting one word for another.
    gap_score : int, default -2
        Score for insertions/deletions (gaps).
    low_confidence_threshold : float, default 0.50
        ASR confidence below which a word is marked low_confidence instead of
        mispronounced.
    """

    def __init__(
        self,
        match_score: int = MATCH_SCORE,
        mismatch_score: int = MISMATCH_SCORE,
        gap_score: int = GAP_SCORE,
        low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
        near_match_correct_threshold: float = NEAR_MATCH_CORRECT_THRESHOLD,
    ) -> None:
        self.match_score = match_score
        self.mismatch_score = mismatch_score
        self.gap_score = gap_score
        self.low_confidence_threshold = low_confidence_threshold
        self.near_match_correct_threshold = near_match_correct_threshold

    def align(
        self,
        reference: list[str],
        hypothesis: list[str],
        *,
        confidences: Optional[list[float]] = None,
    ) -> AlignmentResult:
        """
        Align hypothesis words to reference words using Needleman-Wunsch DP.

        Parameters
        ----------
        reference : list[str]
            Expected word sequence (from Quran text).
        hypothesis : list[str]
            ASR-recognized word sequence (normalized).
        confidences : list[float], optional
            Per-hypothesis-word confidence scores in [0, 1]. If provided,
            low-confidence words are classified accordingly.

        Returns
        -------
        AlignmentResult
            Full alignment with per-word verdicts and summary statistics.
        """
        m = len(reference)
        n = len(hypothesis)

        # Handle edge cases
        if m == 0 and n == 0:
            return AlignmentResult()
        if m == 0:
            # All hypothesis words are insertions
            aligned = [
                AlignedWord(
                    reference=None,
                    hypothesis=h,
                    verdict=WordVerdict.INSERTED_EXTRA,
                    ref_index=None,
                    hyp_index=i,
                    confidence=confidences[i] if confidences else 1.0,
                )
                for i, h in enumerate(hypothesis)
            ]
            return AlignmentResult(
                aligned_words=aligned,
                reference_words=reference,
                hypothesis_words=hypothesis,
                insertion_count=n,
            )
        if n == 0:
            # All reference words are omitted
            aligned = [
                AlignedWord(
                    reference=r,
                    hypothesis=None,
                    verdict=WordVerdict.OMITTED,
                    ref_index=i,
                    hyp_index=None,
                )
                for i, r in enumerate(reference)
            ]
            return AlignmentResult(
                aligned_words=aligned,
                reference_words=reference,
                hypothesis_words=hypothesis,
                omission_count=m,
            )

        # Build DP scoring matrix
        # dp[i][j] = best alignment score for reference[:i] and hypothesis[:j]
        dp = np.zeros((m + 1, n + 1), dtype=np.float64)

        # Initialize: gap penalties for first row and column
        for i in range(1, m + 1):
            dp[i][0] = i * self.gap_score
        for j in range(1, n + 1):
            dp[0][j] = j * self.gap_score

        # Fill DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                ref_word = reference[i - 1]
                hyp_word = hypothesis[j - 1]

                if ref_word == hyp_word:
                    sub_score = self.match_score
                else:
                    # Use character similarity to decide mismatch vs near-match
                    sim = _char_similarity(ref_word, hyp_word)
                    if sim > 0.5:
                        # Partial credit for near-matches
                        sub_score = self.mismatch_score + sim
                    else:
                        sub_score = self.mismatch_score

                match_or_sub = dp[i - 1][j - 1] + sub_score
                delete = dp[i - 1][j] + self.gap_score      # ref word omitted
                insert = dp[i][j - 1] + self.gap_score       # hyp word inserted

                dp[i][j] = max(match_or_sub, delete, insert)

        # Traceback to find alignment
        aligned_words = self._traceback(
            dp, reference, hypothesis, confidences
        )

        # Compute summary statistics
        match_count = sum(1 for w in aligned_words if w.verdict == WordVerdict.CORRECT)
        mismatch_count = sum(1 for w in aligned_words if w.verdict == WordVerdict.MISPRONOUNCED)
        omission_count = sum(1 for w in aligned_words if w.verdict == WordVerdict.OMITTED)
        insertion_count = sum(1 for w in aligned_words if w.verdict == WordVerdict.INSERTED_EXTRA)
        low_conf_count = sum(1 for w in aligned_words if w.verdict == WordVerdict.LOW_CONFIDENCE)

        return AlignmentResult(
            aligned_words=aligned_words,
            reference_words=reference,
            hypothesis_words=hypothesis,
            score=float(dp[m][n]),
            match_count=match_count,
            mismatch_count=mismatch_count,
            omission_count=omission_count,
            insertion_count=insertion_count,
            low_confidence_count=low_conf_count,
        )

    def _traceback(
        self,
        dp: np.ndarray,
        reference: list[str],
        hypothesis: list[str],
        confidences: Optional[list[float]],
    ) -> list[AlignedWord]:
        """
        Traceback through the DP matrix to reconstruct the alignment.

        Walks from dp[m][n] back to dp[0][0], collecting aligned word pairs.
        """
        m = len(reference)
        n = len(hypothesis)

        i, j = m, n
        aligned: list[AlignedWord] = []

        while i > 0 or j > 0:
            if i > 0 and j > 0:
                ref_word = reference[i - 1]
                hyp_word = hypothesis[j - 1]

                if ref_word == hyp_word:
                    sub_score = self.match_score
                else:
                    sim = _char_similarity(ref_word, hyp_word)
                    sub_score = self.mismatch_score + sim if sim > 0.5 else self.mismatch_score

                if dp[i][j] == dp[i - 1][j - 1] + sub_score:
                    # Match or substitution
                    conf = confidences[j - 1] if confidences and j - 1 < len(confidences) else 1.0
                    if ref_word == hyp_word:
                        verdict = WordVerdict.CORRECT
                        sim_val = 1.0
                    else:
                        verdict = self._classify_substitution(ref_word, hyp_word, conf, sim)
                        sim_val = sim
                    aligned.append(AlignedWord(
                        reference=ref_word,
                        hypothesis=hyp_word,
                        verdict=verdict,
                        ref_index=i - 1,
                        hyp_index=j - 1,
                        confidence=conf,
                        similarity=sim_val,
                    ))
                    i -= 1
                    j -= 1
                    continue

            if i > 0 and dp[i][j] == dp[i - 1][j] + self.gap_score:
                # Deletion: reference word omitted
                aligned.append(AlignedWord(
                    reference=reference[i - 1],
                    hypothesis=None,
                    verdict=WordVerdict.OMITTED,
                    ref_index=i - 1,
                    hyp_index=None,
                ))
                i -= 1
            elif j > 0 and dp[i][j] == dp[i][j - 1] + self.gap_score:
                # Insertion: extra hypothesis word
                conf = confidences[j - 1] if confidences and j - 1 < len(confidences) else 1.0
                aligned.append(AlignedWord(
                    reference=None,
                    hypothesis=hypothesis[j - 1],
                    verdict=WordVerdict.INSERTED_EXTRA,
                    ref_index=None,
                    hyp_index=j - 1,
                    confidence=conf,
                ))
                j -= 1
            else:
                # Fallback (shouldn't happen with valid DP)
                break

        aligned.reverse()
        return aligned

    def _classify_substitution(
        self,
        ref_word: str,
        hyp_word: str,
        confidence: float,
        similarity: float,
    ) -> WordVerdict:
        """
        Classify a substitution as mispronounced or low_confidence.

        Priority:
        1. If ASR confidence is below threshold → low_confidence (ASR unsure)
        2. If the recognised word is near-identical to the reference
           (character similarity >= ``near_match_correct_threshold``) → correct.
           High similarity almost always means an ASR/tokenization mismatch
           rather than a real mispronunciation, so we avoid a false red mark.
        3. Otherwise → mispronounced (ASR is confident the user said something different)

        The character similarity is informational and stored on the AlignedWord
        but does not override the confidence-based classification. A high-confidence
        recognition of a different word is a mispronunciation, not an ASR error.

        Parameters
        ----------
        ref_word : str
            Expected word.
        hyp_word : str
            Recognized word.
        confidence : float
            ASR confidence for the hypothesis word.
        similarity : float
            Character-level similarity between ref and hyp.

        Returns
        -------
        WordVerdict
            MISPRONOUNCED or LOW_CONFIDENCE.
        """
        if confidence < self.low_confidence_threshold:
            return WordVerdict.LOW_CONFIDENCE
        # Near-identical words (high character similarity) are almost always an
        # ASR / tokenization mismatch rather than a real mispronunciation — e.g.
        # a correctly recited word recognised with a slightly different token.
        # Marking these as wrong produces false reds ("I said it correctly!"),
        # so treat them as correct instead of mispronounced.
        if similarity >= self.near_match_correct_threshold:
            return WordVerdict.CORRECT
        return WordVerdict.MISPRONOUNCED

    def align_from_strings(
        self,
        reference_text: str,
        hypothesis_text: str,
        *,
        confidences: Optional[list[float]] = None,
    ) -> AlignmentResult:
        """
        Convenience: align from raw text strings (split by whitespace).

        Parameters
        ----------
        reference_text : str
            Reference text (normalized).
        hypothesis_text : str
            Hypothesis text (normalized).
        confidences : list[float], optional
            Per-word confidences for hypothesis.

        Returns
        -------
        AlignmentResult
        """
        ref_words = reference_text.split() if reference_text else []
        hyp_words = hypothesis_text.split() if hypothesis_text else []
        return self.align(ref_words, hyp_words, confidences=confidences)
