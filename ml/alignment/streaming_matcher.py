"""Incremental word alignment for live Quran recitation tracking."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .phonetic import PHONETIC_MATCH_THRESHOLD, phonetic_similarity


class WordStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class WordState:
    index: int
    expected: str
    status: WordStatus
    spoken: Optional[str] = None
    confidence: float = 1.0


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a):
        current = [i + 1]
        for j, char_b in enumerate(b):
            current.append(
                min(
                    previous[j + 1] + 1,
                    current[j] + 1,
                    previous[j] + (char_a != char_b),
                )
            )
        previous = current
    return previous[-1]


def char_similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return 1.0 - _levenshtein(a, b) / max(len(a), len(b))


MATCH_SIMILARITY_THRESHOLD = 0.80
LIVE_MATCH_CONFIDENCE_THRESHOLD = 0.55
LOOKAHEAD = 3
WINDOW_SIZE = 15


class StreamingMatcher:
    """Incrementally align a cumulative ASR hypothesis to a Quran reference.

    Live mode is deliberately conservative: it only advances on a confident
    sequential match. Unmatched ASR tokens are treated as possible insertions or
    hallucinations and are ignored until final review. This prevents one noisy
    Whisper window from painting the rest of a page red or skipping ahead while
    the user is silent.

    Full/final mode retains richer error and skip classification for the review
    result after recording has stopped.
    """

    def __init__(
        self,
        reference_words: list[str],
        *,
        match_threshold: float = MATCH_SIMILARITY_THRESHOLD,
        live_confidence_threshold: float = LIVE_MATCH_CONFIDENCE_THRESHOLD,
        lookahead: int = LOOKAHEAD,
        window_size: int = WINDOW_SIZE,
        phonetic_threshold: float = PHONETIC_MATCH_THRESHOLD,
        use_phonetic: bool = True,
    ) -> None:
        self.reference = list(reference_words)
        self.match_threshold = match_threshold
        self.live_confidence_threshold = max(0.0, min(1.0, live_confidence_threshold))
        self.lookahead = max(0, lookahead)
        self.window_size = max(1, window_size)
        self.phonetic_threshold = phonetic_threshold
        self.use_phonetic = use_phonetic
        self._cursor = 0
        self._hyp_cursor = 0
        self._resolved: dict[int, WordStatus] = {}
        self._resolved_states: list[WordState] = []

    def _is_match(self, hypothesis: str, reference: str) -> bool:
        if not hypothesis or not reference:
            return False
        if hypothesis == reference:
            return True
        if char_similarity(hypothesis, reference) >= self.match_threshold:
            return True
        return self.use_phonetic and (
            phonetic_similarity(hypothesis, reference) >= self.phonetic_threshold
        )

    def evaluate(
        self,
        hypothesis_words: list[str],
        confidences: Optional[list[float]] = None,
        *,
        full: bool = False,
    ) -> list[WordState]:
        i = self._cursor
        j = min(self._hyp_cursor, len(hypothesis_words))
        reference_count = len(self.reference)
        hypothesis_count = len(hypothesis_words)
        window_end = (
            reference_count
            if full
            else min(reference_count, self._cursor + self.window_size)
        )

        def confidence(index: int) -> float:
            if confidences is not None and 0 <= index < len(confidences):
                return float(confidences[index])
            return 1.0

        if not full:
            # Trust-first live tracking: never mark a word wrong or skipped while
            # audio is still streaming. A noisy/hallucinated token is discarded,
            # and the reference cursor only moves after a confident match to the
            # current expected word.
            while i < window_end and j < hypothesis_count:
                expected = self.reference[i]
                spoken = hypothesis_words[j]
                spoken_confidence = confidence(j)

                if (
                    spoken_confidence >= self.live_confidence_threshold
                    and self._is_match(spoken, expected)
                ):
                    self._resolved_states.append(
                        WordState(
                            i,
                            expected,
                            WordStatus.MATCHED,
                            spoken,
                            spoken_confidence,
                        )
                    )
                    i += 1
                    j += 1
                    continue

                # Search only a very small hypothesis lookahead for the current
                # expected word. This skips an inserted hallucination without
                # skipping any Quran reference words.
                insertion_end = min(hypothesis_count, j + 1 + self.lookahead)
                insertion_to: Optional[int] = None
                for candidate in range(j + 1, insertion_end):
                    if (
                        confidence(candidate) >= self.live_confidence_threshold
                        and self._is_match(hypothesis_words[candidate], expected)
                    ):
                        insertion_to = candidate
                        break
                if insertion_to is not None:
                    j = insertion_to
                    continue

                # Consume only the ASR token. The reference word remains active.
                j += 1

            self._cursor = i
            self._hyp_cursor = min(j, hypothesis_count)
            for state in self._resolved_states:
                self._resolved[state.index] = state.status
            return list(self._resolved_states)

        # Final review mode: classify substitutions and short skips after the
        # session has ended. This path is intentionally richer than live mode.
        while i < window_end and j < hypothesis_count:
            spoken = hypothesis_words[j]
            expected = self.reference[i]

            if self._is_match(spoken, expected):
                self._resolved_states.append(
                    WordState(i, expected, WordStatus.MATCHED, spoken, confidence(j))
                )
                i += 1
                j += 1
                continue

            skip_search_end = min(window_end, i + 1 + self.lookahead)
            skip_to = self._find_ref(spoken, i + 1, skip_search_end)
            if skip_to is not None:
                for index in range(i, skip_to):
                    self._resolved_states.append(
                        WordState(index, self.reference[index], WordStatus.SKIPPED)
                    )
                self._resolved_states.append(
                    WordState(
                        skip_to,
                        self.reference[skip_to],
                        WordStatus.MATCHED,
                        spoken,
                        confidence(j),
                    )
                )
                i = skip_to + 1
                j += 1
                continue

            insertion_search_end = j + 1 + self.lookahead
            insertion_to = self._find_hyp(
                expected,
                hypothesis_words,
                j + 1,
                insertion_search_end,
            )
            if insertion_to is not None:
                j = insertion_to
                continue

            self._resolved_states.append(
                WordState(i, expected, WordStatus.ERROR, spoken, confidence(j))
            )
            i += 1
            j += 1

        self._cursor = i
        self._hyp_cursor = min(j, hypothesis_count)
        for state in self._resolved_states:
            self._resolved[state.index] = state.status
        return list(self._resolved_states)

    def _find_ref(self, word: str, start: int, end: int) -> Optional[int]:
        for index in range(start, min(len(self.reference), end)):
            if self._is_match(word, self.reference[index]):
                return index
        return None

    def _find_hyp(
        self,
        word: str,
        hypothesis: list[str],
        start: int,
        end: int,
    ) -> Optional[int]:
        for index in range(start, min(len(hypothesis), end)):
            if self._is_match(hypothesis[index], word):
                return index
        return None

    def finalize(
        self,
        hypothesis_words: list[str],
        confidences: Optional[list[float]] = None,
    ) -> list[WordState]:
        self.evaluate(hypothesis_words, confidences, full=True)
        state_by_index = {state.index: state for state in self._resolved_states}
        final_states: list[WordState] = []
        for index, expected in enumerate(self.reference):
            state = state_by_index.get(index)
            final_states.append(
                WordState(
                    index=index,
                    expected=expected,
                    status=self._resolved.get(index, WordStatus.SKIPPED),
                    spoken=state.spoken if state is not None else None,
                    confidence=state.confidence if state is not None else 1.0,
                )
            )
        return final_states
