"""Tajweed-aware Quran pronunciation references via ``quranic-phonemizer``.

This module generates the *expected* Hafs phoneme sequence for a Quran ayah.
It does not inspect user audio and therefore must never be used by itself to
claim that a user pronounced a phoneme or tajweed rule correctly. Actual
pronunciation assessment still requires an acoustic phoneme recognizer or
forced aligner whose output can be compared with this reference.
"""
from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class QuranicPhonemizerUnavailable(RuntimeError):
    """Raised when the optional Quranic phonemizer dependency cannot load."""


@lru_cache(maxsize=1)
def _get_phonemizer():
    try:
        from quranic_phonemizer import Phonemizer
    except ImportError as exc:  # pragma: no cover - deployment/config failure
        raise QuranicPhonemizerUnavailable(
            "Install quranic-phonemizer to generate Quran pronunciation references"
        ) from exc
    return Phonemizer()


@lru_cache(maxsize=6236)
def get_ayah_word_phonemes(
    surah: int,
    ayah: int,
    expected_word_count: int = 0,
) -> tuple[tuple[str, ...], ...]:
    """Return one Tajweed-aware phoneme string per Quran word.

    ``quranic-phonemizer`` preserves word boundaries in ``phonemes_str()``.
    Each returned inner tuple currently contains one complete IPA/custom
    phoneme string for that word. Keeping the word as an atomic string avoids
    incorrectly splitting IPA combining marks and custom tajweed symbols.

    An empty tuple is returned when the library output does not align with the
    repository's expected Quran word count. A mismatch is safer than assigning
    phonemes to the wrong displayed word.
    """
    if not 1 <= int(surah) <= 114 or int(ayah) < 1:
        raise ValueError(f"Invalid Quran reference: {surah}:{ayah}")

    result = _get_phonemizer().phonemize(f"{int(surah)}:{int(ayah)}")
    phoneme_text = str(result.phonemes_str() or "").strip()
    if not phoneme_text:
        logger.warning("Quranic phonemizer returned no output for %s:%s", surah, ayah)
        return ()

    words = tuple(part for part in phoneme_text.split() if part)
    if expected_word_count and len(words) != expected_word_count:
        logger.warning(
            "Quranic phoneme word-count mismatch for %s:%s: expected=%s got=%s",
            surah,
            ayah,
            expected_word_count,
            len(words),
        )
        return ()
    return tuple((word,) for word in words)


def clear_phonemizer_cache() -> None:
    """Clear caches for tests or controlled runtime reloads."""
    get_ayah_word_phonemes.cache_clear()
    _get_phonemizer.cache_clear()
