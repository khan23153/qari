"""Lend a second recognizer's vowel marks to words the live engine heard.

The live recognizer (FastConformer RNNT) emits undiacritized Arabic, so the
harakat check (:mod:`ml.alignment.harakat`) never has marks to compare and a
vowel mistake such as أَنْعَمْتُ for أَنْعَمْتَ is never seen. The independent,
unprompted Whisper decode does emit tashkeel, but it also hallucinates words.

This joins the two without trusting Whisper's words:

1. Pass 1 (base alignment): align the live engine's normalized words with
   Whisper's tokens normalized the same way (tashkeel stripped). Only exact
   base-word agreements count, so a hallucinated or misheard Whisper word
   lends nothing and a vowel error never shifts the rest of the alignment.
2. Only for those agreements is the Whisper token (with its marks) used as the
   word's raw observed text. The caller's existing harakat comparison then
   checks the marks letter by letter at that exact occurrence.

Ambiguous occurrences abstain: a single-word agreement on a word that appears
more than once on either side is skipped, as is any Whisper token below the
confidence floor or without short-vowel marks. Expected Quran text is never
an input, so nothing here can echo the reference.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Callable, Optional, Sequence

_SHORT_VOWEL_MARKS = frozenset("ًٌٍَُِ")


def has_short_vowel(text: str) -> bool:
    return any(ch in _SHORT_VOWEL_MARKS for ch in text or "")


def lend_vowels(
    native_words: Sequence[str],
    native_raw: Optional[Sequence[Optional[str]]],
    witness_raw: Sequence[str],
    witness_confidences: Sequence[float],
    normalize: Callable[[str], str],
    *,
    confidence_floor: float = 0.55,
) -> list[Optional[str]]:
    """Return ``native_raw`` with Whisper's marked spelling where both agree.

    ``native_words`` are the live engine's normalized words; ``native_raw``
    its raw tokens (same length, may be None). ``witness_raw`` and
    ``witness_confidences`` are Whisper's raw tokens and confidences.
    """
    out: list[Optional[str]] = (
        list(native_raw) if native_raw is not None and len(native_raw) == len(native_words)
        else [None] * len(native_words)
    )
    if not native_words or not witness_raw or len(witness_raw) != len(witness_confidences):
        return out
    witness_norm = [normalize(token) for token in witness_raw]
    native_list = list(native_words)
    matcher = SequenceMatcher(None, native_list, witness_norm, autojunk=False)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            i, j = block.a + k, block.b + k
            word = native_list[i]
            if not word:
                continue
            if block.size == 1 and (native_list.count(word) != 1 or witness_norm.count(word) != 1):
                continue  # which occurrence is unclear: abstain
            token = witness_raw[j]
            confidence = witness_confidences[j]
            if not (confidence_floor <= confidence <= 1.0) or not has_short_vowel(token):
                continue
            out[i] = token
    return out
