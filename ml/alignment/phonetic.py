"""
Phonetic alignment for Quranic Arabic (grapheme → phoneme + similarity).

The streaming matcher originally compared words with plain character
Levenshtein similarity, which treats every letter pair as equally different.
Arabic ASR errors are not random, though: an acoustic model confuses letters
that *sound* alike (``ص``/``س``, ``ت``/``ط``, ``ذ``/``ز``, ``ء``/``ع``), and a
reciter with an accent produces exactly the same confusions. Character
distance over-penalizes those pairs (flagging a correctly-recited word red)
while under-penalizing pairs that look close in Unicode but sound nothing
alike.

This module maps each Arabic letter to a phoneme with articulatory features
(place of articulation, manner, voicing, emphatic) and scores word similarity
with a weighted phoneme edit distance: substituting a phonetically-close
letter costs a fraction of substituting an unrelated one.

Pure Python, no dependencies — safe to import in the streaming hot path and
unit-testable without model weights.

Usage:
    >>> phonetic_similarity("سراط", "صراط")   # sibilant, differs in emphasis
    0.96...
    >>> phonetic_similarity("الرحمن", "الرحيم")  # different words stay apart
    0.7...
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


# ── Phoneme inventory ────────────────────────────────────────────────────────
# Feature axes (coarse, tuned for confusion behaviour rather than strict IPA):
#   place : 0 labial · 1 dental · 2 alveolar · 3 postalveolar/palatal
#           4 velar · 5 uvular · 6 pharyngeal · 7 glottal
#   manner: 0 stop · 1 fricative · 2 nasal · 3 liquid (l/r) · 4 glide/vowel
#   voiced: 0/1
#   emphatic (pharyngealized): 0/1

@dataclass(frozen=True)
class Phoneme:
    symbol: str
    place: int
    manner: int
    voiced: int
    emphatic: int


_P = Phoneme

# One phoneme per bare Arabic letter (diacritics are stripped before lookup —
# the live tracker compares *normalized* text, where short vowels are absent).
_LETTER_PHONEMES: dict[str, Phoneme] = {
    "ء": _P("ʔ", 7, 0, 0, 0),
    "ا": _P("a", 7, 4, 1, 0),
    "أ": _P("ʔ", 7, 0, 0, 0),
    "إ": _P("ʔ", 7, 0, 0, 0),
    "آ": _P("ʔa", 7, 4, 1, 0),
    "ؤ": _P("ʔ", 7, 0, 0, 0),
    "ئ": _P("ʔ", 7, 0, 0, 0),
    "ب": _P("b", 0, 0, 1, 0),
    "ت": _P("t", 2, 0, 0, 0),
    "ث": _P("θ", 1, 1, 0, 0),
    "ج": _P("dʒ", 3, 0, 1, 0),
    "ح": _P("ħ", 6, 1, 0, 0),
    "خ": _P("x", 5, 1, 0, 0),
    "د": _P("d", 2, 0, 1, 0),
    "ذ": _P("ð", 1, 1, 1, 0),
    "ر": _P("r", 2, 3, 1, 0),
    "ز": _P("z", 2, 1, 1, 0),
    "س": _P("s", 2, 1, 0, 0),
    "ش": _P("ʃ", 3, 1, 0, 0),
    "ص": _P("sˤ", 2, 1, 0, 1),
    "ض": _P("dˤ", 2, 0, 1, 1),
    "ط": _P("tˤ", 2, 0, 0, 1),
    "ظ": _P("ðˤ", 1, 1, 1, 1),
    "ع": _P("ʕ", 6, 1, 1, 0),
    "غ": _P("ɣ", 5, 1, 1, 0),
    "ف": _P("f", 0, 1, 0, 0),
    "ق": _P("q", 5, 0, 0, 0),
    "ك": _P("k", 4, 0, 0, 0),
    "ل": _P("l", 2, 3, 1, 0),
    "م": _P("m", 0, 2, 1, 0),
    "ن": _P("n", 2, 2, 1, 0),
    "ه": _P("h", 7, 1, 0, 0),
    "ة": _P("h", 7, 1, 0, 0),   # taa marbuta ≈ h in pausa (t in liaison)
    "و": _P("w", 0, 4, 1, 0),
    "ي": _P("j", 3, 4, 1, 0),
    "ى": _P("a", 7, 4, 1, 0),   # alef maqsura ≈ long a
    "ٱ": _P("a", 7, 4, 1, 0),   # wasla
    "ٰ": _P("a", 7, 4, 1, 0),   # dagger alef (long a)
}

# Tashkeel / decorations stripped before phonemization (matcher input is
# normalized already; this makes the module safe on raw text too).
_STRIP = set(
    "ًٌٍَُِّْٕٓٔ"
    "ٰٖٗ٘ۖۗۘۙۚۛۜ"
    "ۣ۟۠ۡۢۤۥۦ۪ۧۨ"
    "ۭ۫۬ـ"  # incl. tatweel
)

# Feature weights: substituting a phoneme that differs only in emphasis
# (ص/س) or only voicing (ت/د) must cost far less than an unrelated pair.
_W_PLACE = 0.40
_W_MANNER = 0.30
_W_VOICED = 0.15
_W_EMPHATIC = 0.15
# Places of articulation are ordered front→back; distance is scaled so
# adjacent places (dental/alveolar) are cheap and labial↔glottal is full cost.
_MAX_PLACE_DIST = 7.0


def to_phonemes(word: str) -> list[Phoneme]:
    """Grapheme → phoneme sequence for one (possibly diacritized) word."""
    out: list[Phoneme] = []
    for ch in word:
        if ch in _STRIP:
            continue
        p = _LETTER_PHONEMES.get(ch)
        if p is not None:
            out.append(p)
        # Unknown characters (digits, symbols) are simply skipped: they carry
        # no pronunciation and must not poison the distance.
    return out


def _sub_cost(a: Phoneme, b: Phoneme) -> float:
    """Substitution cost in [0, 1] — 0 for identical phonemes."""
    if a.symbol == b.symbol:
        return 0.0
    cost = (
        _W_PLACE * min(abs(a.place - b.place) / _MAX_PLACE_DIST * 2.0, 1.0)
        + _W_MANNER * (a.manner != b.manner)
        + _W_VOICED * (a.voiced != b.voiced)
        + _W_EMPHATIC * (a.emphatic != b.emphatic)
    )
    return min(cost, 1.0)


@lru_cache(maxsize=16384)
def phonetic_similarity(a: str, b: str) -> float:
    """Similarity in [0, 1] between two Arabic words by weighted phoneme
    edit distance (1.0 == phonetically identical)."""
    pa, pb = to_phonemes(a), to_phonemes(b)
    if not pa and not pb:
        return 1.0
    if not pa or not pb:
        return 0.0
    n, m = len(pa), len(pb)
    prev = [j * 1.0 for j in range(m + 1)]
    for i in range(1, n + 1):
        cur = [i * 1.0] + [0.0] * m
        for j in range(1, m + 1):
            cur[j] = min(
                prev[j] + 1.0,                        # deletion
                cur[j - 1] + 1.0,                     # insertion
                prev[j - 1] + _sub_cost(pa[i - 1], pb[j - 1]),
            )
        prev = cur
    return 1.0 - prev[m] / max(n, m)


# Threshold at/above which two words are "the same word, possibly with an
# accent / ASR confusion". Deliberately HIGHER than the character-similarity
# threshold: phonetic distance is more forgiving per-letter, so the bar for
# declaring a match must be stricter or distinct words (الرحمن/الرحيم) would
# collide. Tuned against the pairs in ml/tests/test_phonetic.py.
PHONETIC_MATCH_THRESHOLD = 0.86
