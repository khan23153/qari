"""Speech evidence with optional window-relative token emission bounds."""

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class TimedTranscript:
    words: list[str]
    confidences: list[float]
    # These are RNNT emission bounds, not acoustic/phoneme alignments. A word
    # made of one token may have equal start and end times.
    timings: list[tuple[float, float]]

    def __iter__(self) -> Iterator[list[str] | list[float]]:
        """Preserve the legacy ``words, confidences = transcribe(...)`` API."""
        yield self.words
        yield self.confidences
