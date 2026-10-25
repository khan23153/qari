"""Letter-aligned *observed ASR text* diagnostics.

This module never certifies correct pronunciation and cannot recover vowels an
ASR language model canonicalized. Missing/ambiguous marks are inconclusive.
Callers must establish lexical identity, token confidence and occurrence first;
these rules must not advance the recitation cursor or replace acoustic evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

_VOCALIC = frozenset('\u064b\u064c\u064d\u064e\u064f\u0650\u0652')
_SHORT_VOWELS = frozenset('\u064b\u064c\u064d\u064e\u064f\u0650')
_ALIF_FORMS = str.maketrans({'ٱ': 'ا', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ی': 'ي'})
_DUPLICATE_MARKS = re.compile(r'([\u064b-\u0652])\1+')


@dataclass(frozen=True)
class HarakatComparison:
    mismatch: bool
    compared_positions: tuple[int, ...]
    conflicts: tuple[dict, ...]
    inconclusive: bool


def normalize_uthmani_harakat(text: str) -> str:
    """Normalize marks, not lexical correctness; deduplicate dagger-alif fatha."""
    normalized = unicodedata.normalize('NFC', text or '').replace('\u0670', '\u064e')
    return _DUPLICATE_MARKS.sub(r'\1', normalized)


def _clusters(text: str) -> list[tuple[str, frozenset[str]]] | None:
    letters: list[str] = []
    marks: list[set[str]] = []
    normalized = normalize_uthmani_harakat(text).translate(_ALIF_FORMS).strip()
    # Lexical normalization accepts word-edge punctuation. Remove only the
    # surrounding punctuation/space, never interior boundaries or bad letters.
    while normalized and (normalized[0].isspace() or unicodedata.category(normalized[0]).startswith('P')):
        normalized = normalized[1:]
    while normalized and (normalized[-1].isspace() or unicodedata.category(normalized[-1]).startswith('P')):
        normalized = normalized[:-1]
    for char in normalized:
        # These Quran recitation annotations are not lexical consonants. In
        # Unicode small waw/ya are Lm rather than combining marks.
        if char in {'\u0640', '\u06e5', '\u06e6'}:
            continue
        if char in _VOCALIC:
            if not marks:
                return None
            marks[-1].add(char)
        elif unicodedata.category(char).startswith('L') and '\u0600' <= char <= '\u06ff':
            letters.append(char)
            marks.append(set())
        elif unicodedata.category(char).startswith('M'):
            if not marks:
                return None
            # Shadda/hamza annotations are outside this vowel-quality diagnostic.
            continue
        else:
            # Word boundaries, digits or punctuation are not letter evidence.
            return None
    return list(zip(letters, (frozenset(m) for m in marks)))


def extract_vowel_signature(text: str) -> tuple[tuple[str, str | None], ...]:
    """Keep marks at their letter positions; never flatten to a vowel string."""
    clusters = _clusters(text)
    if clusters is None:
        return ()
    return tuple((letter, next(iter(marks)) if len(marks) == 1 else None)
                 for letter, marks in clusters)


def compare_harakat(
    expected: str,
    spoken: str,
    *,
    is_ayah_end: bool = False,
    is_stream_end: bool = False,
    next_word_spoken: bool = False,
) -> HarakatComparison:
    """Compare explicit vowel marks only at identical aligned letter positions.

    A missing final vowel is never invented, even at wasl. A final sukun is
    exempt at a possible stop (ayah end, current stream end, or no following
    spoken word). Explicit conflicting a/i/u/tanwin remains observable even
    at a stop: pausing cannot turn an actually emitted damma into a fatha.
    Lexical/spelling differences, including ambiguous Uthmani letter mapping,
    abstain rather than shifting all later vowel positions.
    """
    canonical, observed = _clusters(expected), _clusters(spoken)
    if (not canonical or not observed or
            [c[0] for c in canonical] != [c[0] for c in observed]):
        return HarakatComparison(False, (), (), True)
    positions: list[int] = []
    conflicts: list[dict] = []
    unknown = False
    for index, ((_, wanted), (_, heard)) in enumerate(zip(canonical, observed)):
        if len(wanted) != 1 or len(heard) != 1:
            unknown = True
            continue
        a, b = next(iter(wanted)), next(iter(heard))
        final = index == len(canonical) - 1
        may_stop = is_ayah_end or is_stream_end or not next_word_spoken
        if final and b == '\u0652' and a in _SHORT_VOWELS and may_stop:
            unknown = True
            continue
        # Fathatan on the consonant before a written, unvocalized final alif
        # may surface as long /a/ at waqf. Do not generalize this to other
        # vowels, other positions, or explicit continuing speech.
        if (may_stop and index == len(canonical) - 2
                and canonical[-1] == ('ا', frozenset())
                and observed[-1] == ('ا', frozenset())
                and a == '\u064b' and b == '\u064e'):
            unknown = True
            continue
        positions.append(index)
        if a != b:
            conflicts.append({'position': index, 'expected': a, 'observed': b})
    return HarakatComparison(bool(conflicts), tuple(positions), tuple(conflicts),
                             unknown or not positions)


def has_harakat_mistake(expected: str, spoken: str, **context: bool) -> bool:
    """Compatibility boolean; False includes inconclusive, not proven-correct."""
    return compare_harakat(expected, spoken, **context).mismatch
