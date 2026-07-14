"""
Streaming word matcher for real-time recitation tracking (Tarteel-style).

Unlike :class:`ml.alignment.word_alignment.WordAligner` (which performs a full
global Needleman-Wunsch alignment once the recording is finished), this module
supports **live, word-by-word tracking** while the user is still reciting.

The frontend streams audio continuously; the backend re-transcribes the growing
audio buffer and calls :meth:`StreamingMatcher.evaluate` with the cumulative
hypothesis word list. The matcher greedily aligns the hypothesis against the
expected (reference) word sequence and returns a *stable* status for every
reference word that has been resolved so far:

  - ``matched``  : the user has correctly recited this word
  - ``error``    : the user recited a clearly different word here (mispronounced)
  - ``skipped``  : the user jumped past this word (a following word matched)
  - ``pending``  : not yet resolved (still masked / hidden in Hifz mode)

The evaluation is deterministic and stateless per call (it always re-derives the
full status map from the cumulative hypothesis), which makes it robust to the
ASR revising earlier words as more audio arrives. A thin session layer diffs
successive status maps to emit incremental events to the client.

This module has **no heavy dependencies** (pure Python) so it can be unit-tested
without model weights / GPU.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class WordStatus(str, Enum):
    """Live status of a single reference word during streaming."""

    PENDING = "pending"    # not resolved yet (masked in memorization mode)
    MATCHED = "matched"    # correctly recited
    ERROR = "error"        # mispronounced (a different word was said here)
    SKIPPED = "skipped"    # jumped over (a later word matched instead)


@dataclass
class WordState:
    """Resolved state for one reference word."""

    index: int
    expected: str
    status: WordStatus
    spoken: Optional[str] = None
    confidence: float = 1.0


# ── Similarity helpers (kept local so the module is dependency-free) ──────────

def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        cur = [i + 1]
        for j, cb in enumerate(b):
            cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (ca != cb)))
        prev = cur
    return prev[-1]


def char_similarity(a: str, b: str) -> float:
    """Normalized character similarity in ``[0, 1]`` (1.0 == identical)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return 1.0 - _levenshtein(a, b) / max(len(a), len(b))


# Words whose normalized character similarity is >= this are treated as the
# "same" word (absorbs minor ASR / tokenization noise so we don't flag a
# correctly-recited word red).
MATCH_SIMILARITY_THRESHOLD = 0.80

# How far ahead we look for a skip (user jumped over a word) or an inserted
# extra word (ASR hallucination / repeated word) before giving up.
LOOKAHEAD = 3


class StreamingMatcher:
    """Incrementally match a growing ASR hypothesis to a reference word list.

    Parameters
    ----------
    reference_words:
        The expected, **normalized** word sequence for the target ayah(s).
    match_threshold:
        Character similarity at/above which two words are considered equal.
    lookahead:
        Window size for skip / insertion detection.
    """

    def __init__(
        self,
        reference_words: list[str],
        *,
        match_threshold: float = MATCH_SIMILARITY_THRESHOLD,
        lookahead: int = LOOKAHEAD,
    ) -> None:
        self.reference = [w for w in reference_words]
        self.match_threshold = match_threshold
        self.lookahead = lookahead

    # ------------------------------------------------------------------
    def _is_match(self, hyp: str, ref: str) -> bool:
        if not hyp or not ref:
            return False
        if hyp == ref:
            return True
        return char_similarity(hyp, ref) >= self.match_threshold

    # ------------------------------------------------------------------
    def evaluate(
        self,
        hypothesis_words: list[str],
        confidences: Optional[list[float]] = None,
    ) -> list[WordState]:
        """Return the resolved state of every reference word so far.

        The returned list only contains reference words the matcher is
        confident about (matched / error / skipped). Words still ahead of the
        recitation are *not* included (they remain PENDING and stay masked).
        """
        states: list[WordState] = []
        i = 0  # reference cursor
        j = 0  # hypothesis cursor
        n_ref = len(self.reference)
        n_hyp = len(hypothesis_words)

        def conf(k: int) -> float:
            if confidences and 0 <= k < len(confidences):
                return confidences[k]
            return 1.0

        while i < n_ref and j < n_hyp:
            hw = hypothesis_words[j]
            rw = self.reference[i]

            if self._is_match(hw, rw):
                states.append(WordState(i, rw, WordStatus.MATCHED, hw, conf(j)))
                i += 1
                j += 1
                continue

            # Skip detection: did the user jump past one or more reference
            # words? Look for the current hypothesis word further ahead.
            skip_to = self._find_ref(hw, i + 1, self.lookahead)
            if skip_to is not None:
                for k in range(i, skip_to):
                    states.append(WordState(k, self.reference[k], WordStatus.SKIPPED))
                states.append(
                    WordState(skip_to, self.reference[skip_to], WordStatus.MATCHED, hw, conf(j))
                )
                i = skip_to + 1
                j += 1
                continue

            # Insertion detection: did the ASR emit an extra word (repeat /
            # hallucination)? Look for the current reference word further ahead
            # in the hypothesis and drop the intervening hypothesis words.
            ins_to = self._find_hyp(rw, hypothesis_words, j + 1, self.lookahead)
            if ins_to is not None:
                j = ins_to
                continue

            # Genuine substitution → mispronounced (real red mark).
            states.append(WordState(i, rw, WordStatus.ERROR, hw, conf(j)))
            i += 1
            j += 1

        return states

    # ------------------------------------------------------------------
    def _find_ref(self, hyp_word: str, start: int, window: int) -> Optional[int]:
        end = min(len(self.reference), start + window)
        for k in range(start, end):
            if self._is_match(hyp_word, self.reference[k]):
                return k
        return None

    def _find_hyp(
        self, ref_word: str, hypothesis: list[str], start: int, window: int
    ) -> Optional[int]:
        end = min(len(hypothesis), start + window)
        for k in range(start, end):
            if self._is_match(hypothesis[k], ref_word):
                return k
        return None

    # ------------------------------------------------------------------
    def finalize(self, hypothesis_words: list[str]) -> list[WordState]:
        """Return the state of *all* reference words at end-of-session.

        Any reference word that was never resolved is marked ``skipped`` (the
        user finished without reciting it).
        """
        resolved = {s.index: s for s in self.evaluate(hypothesis_words)}
        out: list[WordState] = []
        for idx, ref in enumerate(self.reference):
            if idx in resolved:
                out.append(resolved[idx])
            else:
                out.append(WordState(idx, ref, WordStatus.SKIPPED))
        return out
