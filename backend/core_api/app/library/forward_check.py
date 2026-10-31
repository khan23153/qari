"""Check a forwarded "hadith" against the hadith collections.

People forward hadith on WhatsApp in Arabic, Urdu and English, often without
a reference. This finds the closest hadith in the collections the Library
reads (fawazahmed0/hadith-api full editions), so the app can show the real
text, its reference and the grades named scholars gave it.

It never grades anything itself, and "no match" is reported as "not found
in these collections", never as "fabricated": absence from a search is not
a ruling.
"""

from __future__ import annotations

import math
import re
from array import array
from dataclasses import dataclass
from typing import Iterable, Optional

from app.library.arabic import normalize_arabic

# Score bands: the weighted share of the query's words and word pairs found
# in one hadith. Measured on Bukhari in Arabic, Urdu and English: forwards of
# real hadith scored 0.45-1.0, made-up messages at most about 0.33.
STRONG = 0.75
POSSIBLE = 0.4

_LATIN_WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")
_ARABIC_SCRIPT = re.compile("[؀-ۿ]")
_URDU_LETTERS = re.compile("[ٹڈڑںےۓہھکگپچژی]")

# Urdu letters folded to their Arabic counterparts so Urdu and Arabic
# spellings of shared words (اللہ / الله, کتاب / كتاب) meet.
_URDU_FOLD = str.maketrans({
    "ی": "ي", "ے": "ي", "ۓ": "ي", "ک": "ك", "ہ": "ه", "ھ": "ه", "ۃ": "ة",
    "ۂ": "ه", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي",
})

_EN_STOP = frozenset("""
a an and are as at be been but by did do does for from had has have he her
him his i if in is it its me my no not of on or our she so that the their
them then there they this to us was we were what when which who will with
you your said say says narrated allah's messenger prophet upon him peace be
""".split())

_AR_STOP = frozenset("""
في من على الى عن ان او ما لا قال قالت هو هي ثم كان قد لم لن كل هذا ذلك التي
الذي حدثنا اخبرنا عن رسول الله صلى عليه وسلم رضي عنه سے کے کی کا میں نے کو اور
ہے ہیں تھا تھے پر بھی یہ وہ جو کہ تو آپ اللہ علیہ وسلم فرمایا رسول
""".split())


def detect_language(text: str) -> str:
    """'ur', 'ar' or 'en' for the query script."""
    if _ARABIC_SCRIPT.search(text):
        return "ur" if _URDU_LETTERS.search(text) else "ar"
    return "en"


def tokenize(text: str, lang: str) -> list[str]:
    """Words worth matching, normalised for [lang] ('ar', 'ur' or 'en')."""
    if lang == "en":
        words = _LATIN_WORD.findall(text.lower().replace("’", "'"))
        return [_stem_en(w) for w in words if len(w) > 2 and w not in _EN_STOP]
    folded = normalize_arabic(text.translate(_URDU_FOLD))
    out = []
    for w in folded.split():
        if not _ARABIC_SCRIPT.search(w) or len(w) < 2:
            continue
        if w in _AR_STOP or normalize_arabic(w.translate(_URDU_FOLD)) in _AR_STOP_FOLDED:
            continue
        out.append(w)
    return out


def _stem_en(word: str) -> str:
    """A light English stem so 'intentions'/'intended' and 'learns'/'learn'
    meet; translations of the same hadith vary in such endings."""
    word = word.split("'")[0]
    for suffix in ("ations", "ation", "ings", "ing", "ness", "ed", "es", "ly", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


_AR_STOP_FOLDED = frozenset(normalize_arabic(w.translate(_URDU_FOLD)) for w in _AR_STOP)


@dataclass(frozen=True)
class ForwardMatch:
    hadith_id: str
    score: float
    language: str

    @property
    def band(self) -> str:
        return "strong" if self.score >= STRONG else "possible"


def features(words: list[str]) -> tuple[set[str], set[str]]:
    """(single words, adjacent word pairs). Pairs carry the wording: a
    forward that merely shares common words with a hadith shares few pairs."""
    pairs = {f"{a} {b}" for a, b in zip(words, words[1:])}
    return set(words), pairs


# How much the word pairs count against the single words in a score.
PAIR_WEIGHT = 0.6


class _LanguageIndex:
    """Inverted index of one language over hadith ids."""

    def __init__(self) -> None:
        self.postings: dict[str, array] = {}
        self.docs = 0

    def add(self, doc: int, words: list[str]) -> None:
        self.docs += 1
        singles, pairs = features(words)
        for w in singles | pairs:
            posting = self.postings.get(w)
            if posting is None:
                posting = self.postings[w] = array("I")
            posting.append(doc)

    def idf(self, word: str) -> float:
        df = len(self.postings.get(word, ()))
        # Unknown words still weigh in the query, so a text full of words
        # no hadith uses scores low instead of matching on two common ones.
        return math.log((self.docs + 1) / (df + 0.5))

    def _coverage(self, query: set[str]) -> dict[int, float]:
        total = sum(self.idf(w) for w in query)
        if total <= 0:
            return {}
        acc: dict[int, float] = {}
        for w in query:
            posting = self.postings.get(w)
            if not posting:
                continue
            weight = self.idf(w)
            for doc in posting:
                acc[doc] = acc.get(doc, 0.0) + weight
        return {doc: s / total for doc, s in acc.items()}

    def score(self, words: list[str]) -> dict[int, float]:
        singles, pairs = features(words)
        single = self._coverage(singles)
        paired = self._coverage(pairs) if pairs else {}
        return {
            doc: (1 - PAIR_WEIGHT) * s + PAIR_WEIGHT * paired.get(doc, 0.0)
            for doc, s in single.items()
        }


class ForwardIndex:
    """Hadith texts in Arabic, Urdu and English, searchable by wording."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._doc_of: dict[str, int] = {}
        self._langs: dict[str, _LanguageIndex] = {}
        self.collections: list[str] = []

    def _doc(self, hadith_id: str) -> int:
        doc = self._doc_of.get(hadith_id)
        if doc is None:
            doc = self._doc_of[hadith_id] = len(self._ids)
            self._ids.append(hadith_id)
        return doc

    def add_edition(self, slug: str, lang: str, edition: dict) -> None:
        """Adds a fawazahmed0 full edition ({"hadiths": [...]})."""
        index = self._langs.setdefault(lang, _LanguageIndex())
        for h in edition.get("hadiths", []):
            text = h.get("text") or ""
            words = tokenize(text, lang)
            if len(words) < 3:
                continue
            number = h.get("hadithnumber")
            if number is None:
                continue
            index.add(self._doc(f"{slug}:{_num(number)}"), words)
        if slug not in self.collections:
            self.collections.append(slug)

    @property
    def languages(self) -> list[str]:
        return sorted(self._langs)

    def search(self, text: str, limit: int = 5) -> list[ForwardMatch]:
        lang = detect_language(text)
        # Arabic script may be Arabic or Urdu: try both and keep the best.
        langs = ["ar", "ur"] if lang in ("ar", "ur") else ["en"]
        best: dict[int, tuple[float, str]] = {}
        for l in langs:
            index = self._langs.get(l)
            if index is None:
                continue
            words = tokenize(text, l)
            if len(words) < 3:
                continue
            for doc, s in index.score(words).items():
                if s > best.get(doc, (0.0, ""))[0]:
                    best[doc] = (s, l)
        ranked = sorted(best.items(), key=lambda kv: kv[1][0], reverse=True)
        return [
            ForwardMatch(self._ids[doc], round(s, 3), l)
            for doc, (s, l) in ranked[:limit]
            if s >= POSSIBLE
        ]


def _num(n) -> str:
    """5 or 5.0 -> '5'; keeps sub-numbers like '5.2' as they are."""
    try:
        f = float(n)
    except (TypeError, ValueError):
        return str(n)
    return str(int(f)) if f.is_integer() else str(n)


# Editions per language for a collection, from its remote config.
def editions_for(remote_cfg: dict) -> dict[str, str]:
    ara = remote_cfg["arabic_edition"]
    out = {"ar": ara, "en": remote_cfg["translation_edition"]}
    if ara.startswith("ara-"):
        out["ur"] = "urd-" + ara[4:]
    return out


def build_index(editions: Iterable[tuple[str, str, Optional[dict]]]) -> ForwardIndex:
    """[(slug, lang, edition or None)] -> index (missing editions skipped)."""
    index = ForwardIndex()
    for slug, lang, edition in editions:
        if edition:
            index.add_edition(slug, lang, edition)
    return index
