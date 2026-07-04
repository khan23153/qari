"""
Tajweed annotation parser.

Quran.com provides a ``text_uthmani_tajweed`` field that embeds HTML-like
markup tags into the Uthmani Arabic text.  Each tag encodes a tajweed rule
and wraps the letters it applies to:

    <tajweed-rule-id>...letters...</tajweed-rule-id>

Rule IDs (from Quran.com / Tanzil.net):

    1  – ghunnah (nasalisation, 2-harakat)
    2  – qalqalah (echoing / bouncing sound)
    3  – ikhfa   (concealment)
    4  – idgham  (merging)
    5  – iqlab   (conversion)
    6  – madd_2  (elongation, 2 harakat — normal)
    7  – madd_4_5 (elongation, 4-5 harakat — due to hamza)
    8  – madd_6  (elongation, 6 harakat — due to sukoon)
    9  – madd_2_necessary (necessary elongation, 2 harakat)

The parser strips the markup, extracts each annotation with its rule,
the Arabic text fragment it covers, and maps the annotation to the
corresponding word index within the ayah.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Tajweed rule mapping
# ---------------------------------------------------------------------------

TAJWEED_RULES: Dict[int, str] = {
    1: "ghunnah",
    2: "qalqalah",
    3: "ikhfa",
    4: "idgham",
    5: "iqlab",
    6: "madd_2",
    7: "madd_4_5",
    8: "madd_6",
    9: "madd_2_necessary",
}

# Reverse lookup: rule name → id
TAJWEED_RULE_IDS: Dict[str, int] = {v: k for k, v in TAJWEED_RULES.items()}

# Human-readable descriptions for each rule
TAJWEED_DESCRIPTIONS: Dict[int, str] = {
    1: "Ghunnah: nasalisation lasting two harakat on mim/nun with shadda",
    2: "Qalqalah: bouncing/echoing sound on letters qutb jad, qalqala sugra",
    3: "Ikhfa: concealment of noon/tanween before certain letters",
    4: "Idgham: merging of noon/tanween into ya, waw, mim, nun, lam, ra",
    5: "Iqlab: conversion of noon/tanween to mim before ba",
    6: "Madd Tabii: natural elongation of two harakat",
    7: "Madd Muttasil: elongation of 4-5 harakat due to hamza",
    8: "Madd Lazim: obligatory elongation of 6 harakat due to sukoon",
    9: "Madd Lazim Kalimi: necessary elongation of 2 harakat",
}

# Regex to match <n>...</n> tags where n is a digit 1-9
_TAG_RE = re.compile(r"<(\d)>(.*?)</\1>", re.DOTALL)

# Regex to find all tags (including self-closing or malformed) for stripping
_ALL_TAG_RE = re.compile(r"</?\d+>")


class TajweedParser:
    """Parse tajweed markup from Quran.com's ``text_uthmani_tajweed`` field.

    Usage::

        parser = TajweedParser()
        annotations = parser.parse_ayah(2, 255, tajweed_text, words)
    """

    def __init__(self) -> None:
        self._stats: Dict[str, int] = {"annotations": 0, "ayahs": 0}

    # ------------------------------------------------------------------
    # Main parse method
    # ------------------------------------------------------------------

    def parse_ayah(
        self,
        surah_number: int,
        ayah_number: int,
        tajweed_text: str,
        words: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Parse tajweed markup for a single ayah.

        Parameters
        ----------
        surah_number:
            Surah number (1-114).
        ayah_number:
            Ayah number within the surah.
        tajweed_text:
            The raw ``text_uthmani_tajweed`` string containing markup tags.
        words:
            Optional list of word dicts (from corpus or API) for mapping
            annotations to word indices.  Each dict should have a ``form``
            key with the Arabic surface form.

        Returns
        -------
        dict with keys::

            surah, ayah,
            plain_text (markup stripped),
            annotations (list of dicts with rule_id, rule_name, description,
                         text_fragment, char_start, char_end, word_indices),
        """
        self._stats["ayahs"] += 1

        plain_text = self._strip_markup(tajweed_text)
        annotations = self._extract_annotations(tajweed_text, plain_text)

        # Map annotations to word indices
        if words:
            annotations = self._map_to_words(annotations, words)

        self._stats["annotations"] += len(annotations)

        logger.debug(
            "parsed_ayah_tajweed",
            surah=surah_number,
            ayah=ayah_number,
            annotations=len(annotations),
        )

        return {
            "surah": surah_number,
            "ayah": ayah_number,
            "plain_text": plain_text,
            "annotations": annotations,
        }

    # ------------------------------------------------------------------
    # Markup stripping
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_markup(text: str) -> str:
        """Remove all tajweed markup tags, returning plain Uthmani text."""
        return _ALL_TAG_RE.sub("", text)

    # ------------------------------------------------------------------
    # Annotation extraction
    # ------------------------------------------------------------------

    def _extract_annotations(
        self,
        tajweed_text: str,
        plain_text: str,
    ) -> List[Dict[str, Any]]:
        """Extract structured annotations from the tajweed markup.

        We walk through the tagged text, tracking character offsets in the
        *plain* (stripped) text so that each annotation's ``char_start`` and
        ``char_end`` refer to positions in the clean Uthmani string.
        """
        annotations: List[Dict[str, Any]] = []

        # Build a mapping from positions in the tagged text to positions
        # in the plain text, then extract each tag's content.
        for match in _TAG_RE.finditer(tajweed_text):
            rule_id = int(match.group(1))
            fragment = match.group(2)

            rule_name = TAJWEED_RULES.get(rule_id, f"unknown_{rule_id}")
            description = TAJWEED_DESCRIPTIONS.get(rule_id, "")

            # Compute the character offset of this fragment in the plain text.
            # Everything before this match in the tagged text, minus tags,
            # gives us the plain-text offset.
            tagged_before = tajweed_text[: match.start()]
            plain_before = self._strip_markup(tagged_before)
            char_start = len(plain_before)
            char_end = char_start + len(fragment)

            annotations.append({
                "rule_id": rule_id,
                "rule_name": rule_name,
                "description": description,
                "text_fragment": fragment,
                "char_start": char_start,
                "char_end": char_end,
                "word_indices": [],
            })

        return annotations

    # ------------------------------------------------------------------
    # Word mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _map_to_words(
        annotations: List[Dict[str, Any]],
        words: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Map each annotation's character range to word indices.

        We reconstruct the ayah by joining word forms with spaces and then
        find which word(s) overlap with each annotation's character range.
        """
        if not words:
            return annotations

        # Build word boundaries in the plain text
        word_forms = [w.get("form", "") for w in words]
        word_boundaries: List[Tuple[int, int]] = []
        pos = 0
        for form in word_forms:
            start = pos
            end = pos + len(form)
            word_boundaries.append((start, end))
            pos = end + 1  # +1 for the space separator

        for ann in annotations:
            ann_start = ann["char_start"]
            ann_end = ann["char_end"]
            indices: List[int] = []

            for idx, (w_start, w_end) in enumerate(word_boundaries):
                # Check overlap between [ann_start, ann_end) and [w_start, w_end)
                if ann_start < w_end and ann_end > w_start:
                    indices.append(idx)

            ann["word_indices"] = indices

        return annotations

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def parse_surah(
        self,
        surah_number: int,
        tajweed_verses: List[Dict[str, Any]],
        words_by_ayah: Optional[Dict[int, List[Dict[str, Any]]]] = None,
    ) -> List[Dict[str, Any]]:
        """Parse tajweed for all ayahs in a surah.

        Parameters
        ----------
        surah_number:
            Surah number.
        tajweed_verses:
            List of verse dicts from ``get_tajweed_text()``, each with
            ``verse_number`` and ``text_uthmani_tajweed``.
        words_by_ayah:
            Optional mapping of ayah_number → list of word dicts.
        """
        results: List[Dict[str, Any]] = []

        for verse in tajweed_verses:
            ayah_num = verse.get("verse_number", 0)
            tajweed_text = verse.get("text_uthmani_tajweed", "")
            words = words_by_ayah.get(ayah_num) if words_by_ayah else None

            parsed = self.parse_ayah(surah_number, ayah_num, tajweed_text, words)
            results.append(parsed)

        logger.info(
            "parsed_surah_tajweed",
            surah=surah_number,
            ayahs=len(results),
            total_annotations=self._stats["annotations"],
        )
        return results

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, int]:
        """Return cumulative parse statistics."""
        return dict(self._stats)
