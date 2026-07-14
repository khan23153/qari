"""Alignment sub-package: word-level alignment and forced alignment.

The heavy modules (``word_alignment``, ``forced_alignment``) import numpy/torch
at module load. To keep the *lightweight* real-time streaming matcher
importable in environments without the full ML stack (e.g. the recitation-api
container running the live WS stream), we expose a lazy-access helper and do
NOT eagerly import the torch-dependent modules here.
"""

from .streaming_matcher import StreamingMatcher, WordStatus, WordState

__all__ = [
    "StreamingMatcher",
    "WordStatus",
    "WordState",
    "WordAligner",
    "WordVerdict",
    "AlignmentResult",
    "ForcedAligner",
    "ForcedAlignmentResult",
    "WordTimestamp",
]


def __getattr__(name: str):  # noqa: D401 - module-level lazy import shim
    """Lazily import torch-dependent names on first access.

    This means ``from ml.alignment import StreamingMatcher`` never pulls in
    numpy/torch, while ``from ml.alignment import WordAligner`` (used by the
    batch inference worker, which has the full ML stack) still works.
    """
    if name in ("WordAligner", "WordVerdict", "AlignmentResult"):
        from .word_alignment import (  # type: ignore
            WordAligner,
            WordVerdict,
            AlignmentResult,
        )

        return {
            "WordAligner": WordAligner,
            "WordVerdict": WordVerdict,
            "AlignmentResult": AlignmentResult,
        }[name]
    if name in ("ForcedAligner", "ForcedAlignmentResult", "WordTimestamp"):
        from .forced_alignment import (  # type: ignore
            ForcedAligner,
            ForcedAlignmentResult,
            WordTimestamp,
        )

        return {
            "ForcedAligner": ForcedAligner,
            "ForcedAlignmentResult": ForcedAlignmentResult,
            "WordTimestamp": WordTimestamp,
        }[name]
    raise AttributeError(f"module 'ml.alignment' has no attribute {name!r}")
