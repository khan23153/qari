"""
Parser for the Quranic Arabic Corpus morphology TSV files.

The corpus (https://corpus.quran.com) by Kais Dukes is GNU-licensed and
distributes a TSV file ``quranic-corpus-morphology.txt`` with one token per
line and tab-separated columns:

    Column 1 – location (e.g. ``2:1:1`` = surah 2, ayah 1, word 1)
    Column 2 – form (the Arabic surface form)
    Column 3 – tag (POS tag, e.g. ``V``, ``N``, ``PREP``, ``REL``, …)
    Column 4 – features (morphology features as ``|``-separated key:value pairs)
    Column 5 – lemma (Arabic lemma)
    Column 6 – root (Arabic root, typically 3 letters)
    Column 7 – (optional) gloss

Lines starting with ``#`` are comments / headers.

The parser converts each row into a structured dict and maps the corpus POS
tags to the three classical Arabic part-of-speech groups:

    * **ism**  (noun) – N, PN, ADJ, DET, PRON, REL, DEM, NUM
    * **fil**  (verb) – V, PV, IV, CV, IMPV
    * **harf** (particle) – P, PREP, CONJ, PART, NEG, INTG, ACC, CND, RC, PRO, INL, INC, RES, AMD, EQ, FUT, PREV, REM, VOC, EXL, SUP, DET+PN, PRON+DEM, etc.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# POS tag → part-of-speech group mapping
# ---------------------------------------------------------------------------

POS_GROUP_MAP: Dict[str, str] = {
    # Nouns (ism)
    "N": "ism",
    "PN": "ism",       # Proper noun
    "ADJ": "ism",      # Adjective
    "DET": "ism",      # Determiner / definite article
    "PRON": "ism",     # Pronoun
    "REL": "ism",      # Relative pronoun
    "DEM": "ism",      # Demonstrative pronoun
    "NUM": "ism",      # Number / numeral
    "T": "ism",        # Title (rare)

    # Verbs (fil)
    "V": "fil",
    "PV": "fil",       # Perfect verb
    "IV": "fil",       # Imperfect verb
    "CV": "fil",       # Imperative verb / command
    "IMPV": "fil",     # Imperative

    # Particles (harf) — everything else
    "P": "harf",
    "PREP": "harf",    # Preposition
    "CONJ": "harf",    # Conjunction
    "PART": "harf",    # Particle (generic)
    "NEG": "harf",     # Negative particle
    "INTG": "harf",    # Interrogative particle
    "ACC": "harf",     # Accusative particle (e.g. إنّ)
    "CND": "harf",     # Conditional particle
    "RC": "harf",      # Resumption / count particle
    "PRO": "harf",     # Prohibition particle (لا)
    "INL": "harf",     # Particle of incitement
    "INC": "harf",     # Particle of incitement
    "RES": "harf",     # Restriction particle (إنما)
    "AMD": "harf",     # Amendment / exceptive particle
    "EQ": "harf",      # Equalising particle
    "FUT": "harf",     # Future particle (سوف)
    "PREV": "harf",    # Preventive particle
    "REM": "harf",     # Remnant particle
    "VOC": "harf",     # Vocative particle (يا)
    "EXL": "harf",     # Exclamation particle
    "SUP": "harf",     # Supplement / response particle
    "RP": "harf",      # Response particle
    "EMPH": "harf",    # Emphatic particle (لام التوكيد)
    "IMPV_PART": "harf",  # Imperative particle
    "PRP": "harf",     # Purpose particle (لام التعليل)
    "RSLT": "harf",    # Result particle
    "COM": "harf",     # Commentary / vocative complement
    "EXH": "harf",     # Exhortation particle
    "AVR": "harf",     # Aversion particle
    "EXP": "harf",     # Exceptive particle
    "PRT": "harf",     # Generic particle alias
}

# Default group for unknown tags
DEFAULT_POS_GROUP = "harf"


# ---------------------------------------------------------------------------
# Arabic → Latin transliteration (simplified Buckwalter-ish)
# ---------------------------------------------------------------------------

_ARABIC_TO_LATIN: Dict[str, str] = {
    "ا": "A", "أ": ">", "إ": "<", "آ": "|", "ء": "'",
    "ب": "b", "ت": "t", "ث": "v", "ج": "j", "ح": "H",
    "خ": "x", "د": "d", "ذ": "*", "ر": "r", "ز": "z",
    "س": "s", "ش": "$", "ص": "S", "ض": "D", "ط": "T",
    "ظ": "Z", "ع": "E", "غ": "g", "ف": "f", "ق": "q",
    "ك": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h",
    "و": "w", "ي": "y", "ى": "Y", "ة": "p", "ؤ": "&",
    "ئ": "}", "ء": "'",
    "َ": "a", "ُ": "u", "ِ": "i", "ْ": "~", "ّ": "#",
    "ً": "F", "ٌ": "N", "ٍ": "K", "ُ": "u", "ِ": "i",
}


class CorpusParser:
    """Parse Quranic Arabic Corpus morphology TSV files.

    Usage::

        parser = CorpusParser()
        words = parser.parse_morphology_file("quranic-corpus-morphology.txt")
        roots = parser.extract_roots(words)
    """

    # Regex to split a location string like "2:255:1:3" (surah:ayah:word:token)
    _LOC_RE = re.compile(r"^(\d+):(\d+):(\d+)(?::(\d+))?$")

    def __init__(self) -> None:
        self._stats: Counter = Counter()

    # ------------------------------------------------------------------
    # Main parse method
    # ------------------------------------------------------------------

    def parse_morphology_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a corpus morphology TSV file into a list of word dicts.

        Parameters
        ----------
        file_path:
            Path to the ``quranic-corpus-morphology.txt`` file.

        Returns
        -------
        list of dicts, each with keys::

            surah, ayah, word, token (optional),
            form (Arabic surface form),
            pos_tag (raw corpus tag, e.g. "V", "N", "PREP"),
            pos_group ("ism" | "fil" | "harf"),
            lemma (Arabic lemma or None),
            root (Arabic root or None),
            features (dict of feature key→value),
            features_raw (original feature string),
            gloss (optional English gloss),
            location (original "surah:ayah:word[:token]" string),
        """
        words: List[Dict[str, Any]] = []

        with open(file_path, encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    word = self._parse_line(line)
                except Exception as exc:
                    logger.warning(
                        "parse_error",
                        line_no=line_no,
                        line=line[:80],
                        error=str(exc),
                    )
                    self._stats["parse_errors"] += 1
                    continue

                if word is not None:
                    words.append(word)
                    self._stats["parsed"] += 1

        logger.info("corpus_parse_complete", total=len(words), stats=dict(self._stats))
        return words

    # ------------------------------------------------------------------
    # Single-line parser
    # ------------------------------------------------------------------

    def _parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single TSV line into a word dict."""
        parts = line.split("\t")
        if len(parts) < 3:
            raise ValueError(f"Expected ≥3 columns, got {len(parts)}")

        location = parts[0].strip()
        form = parts[1].strip()
        tag = parts[2].strip()
        features_raw = parts[3].strip() if len(parts) > 3 else ""
        lemma = parts[4].strip() if len(parts) > 4 else ""
        root = parts[5].strip() if len(parts) > 5 else ""
        gloss = parts[6].strip() if len(parts) > 6 else ""

        # Parse location "surah:ayah:word[:token]"
        match = self._LOC_RE.match(location)
        if not match:
            raise ValueError(f"Bad location format: {location!r}")

        surah = int(match.group(1))
        ayah = int(match.group(2))
        word_num = int(match.group(3))
        token_num = int(match.group(4)) if match.group(4) else None

        # Map POS tag to group
        pos_group = POS_GROUP_MAP.get(tag, DEFAULT_POS_GROUP)

        # Parse features "key:value|key:value"
        features = self._parse_features(features_raw)

        # Clean up empty strings → None
        lemma = lemma if lemma and lemma != ";" else None
        root = root if root and root != ";" else None
        gloss = gloss if gloss and gloss != ";" else None

        return {
            "location": location,
            "surah": surah,
            "ayah": ayah,
            "word": word_num,
            "token": token_num,
            "form": form,
            "pos_tag": tag,
            "pos_group": pos_group,
            "lemma": lemma,
            "root": root,
            "features": features,
            "features_raw": features_raw,
            "gloss": gloss,
        }

    # ------------------------------------------------------------------
    # Feature parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_features(raw: str) -> Dict[str, str]:
        """Parse the features column into a dict.

        The corpus encodes features as ``|``-separated ``key:value`` pairs,
        e.g. ``M|P-1|ROOT:ktb|LEM:كتاب``.
        Some entries use bare flags (no colon).
        """
        features: Dict[str, str] = {}
        if not raw or raw == ";":
            return features

        for segment in raw.split("|"):
            segment = segment.strip()
            if not segment:
                continue
            if ":" in segment:
                key, value = segment.split(":", 1)
                features[key.strip()] = value.strip()
            else:
                # Bare flag like "M" (masc), "P" (passive), "1" (1st person)
                features[segment] = "true"
        return features

    # ------------------------------------------------------------------
    # Root extraction
    # ------------------------------------------------------------------

    def extract_roots(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract unique roots with occurrence counts.

        Parameters
        ----------
        words:
            The list of word dicts returned by :meth:`parse_morphology_file`.

        Returns
        -------
        list of dicts with keys::

            root (Arabic),
            transliteration (Latin),
            occurrence_count (int),
            unique_lemmas (list of Arabic lemma strings),
        """
        root_data: Dict[str, Dict[str, Any]] = {}

        for word in words:
            root = word.get("root")
            if not root:
                continue

            if root not in root_data:
                root_data[root] = {
                    "root": root,
                    "transliteration": self._transliterate_root(root),
                    "occurrence_count": 0,
                    "unique_lemmas": set(),
                }

            root_data[root]["occurrence_count"] += 1
            lemma = word.get("lemma")
            if lemma:
                root_data[root]["unique_lemmas"].add(lemma)

        # Convert sets to sorted lists for JSON-friendliness
        roots = []
        for data in root_data.values():
            data["unique_lemmas"] = sorted(data["unique_lemmas"])
            roots.append(data)

        # Sort by occurrence count descending
        roots.sort(key=lambda r: r["occurrence_count"], reverse=True)

        logger.info("roots_extracted", unique_roots=len(roots))
        return roots

    # ------------------------------------------------------------------
    # Transliteration
    # ------------------------------------------------------------------

    @staticmethod
    def _transliterate_root(root_arabic: str) -> str:
        """Transliterate an Arabic root to a simplified Latin form.

        Uses a Buckwalter-style mapping.  Non-mapped characters are
        replaced with ``?``.
        """
        result: List[str] = []
        for char in root_arabic:
            result.append(_ARABIC_TO_LATIN.get(char, "?"))
        return "".join(result)
