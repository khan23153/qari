"""
Tajweed annotation parser.

Quran.com provides a ``text_uthmani_tajweed`` field that embeds HTML-like
markup into the Uthmani Arabic text.  Each tajweed rule is wrapped in a
``<tajweed>`` tag carrying a ``class`` attribute naming the rule, and the
tag wraps the letters the rule applies to::

    <tajweed class=ham_wasl>ٱ</tajweed>
    <tajweed class=madda_normal>ـٰ</tajweed>
    <tajweed class=ikhafa>...</tajweed>

(The legacy Tanzil markup used numeric tags ``<1>..</1>``; Quran.com v4
uses the descriptive ``class`` names listed in :data:`TAJWEED_CLASSES`.)

Verse-end markers appear as ``<span class=end>١</span>`` (the ayah number)
and are stripped entirely so the plain text aligns with the word forms.

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
# Tajweed rule mapping (Quran.com v4 / Tanzil class names)
# ---------------------------------------------------------------------------
#
# Each entry maps a markup ``class`` to its category, English/Arabic names,
# and descriptions in English, Urdu, and Romanised Hindi.

TAJWEED_CLASSES: Dict[str, Dict[str, str]] = {
    "ham_wasl": {
        "category": "hamza",
        "name_en": "Hamzat al-Wasl",
        "name_ar": "همزة الوصل",
        "desc_en": "Connecting hamza that is silent when the word is preceded by another.",
        "desc_ur": "وہ ہمزہ جو ادائیگی میں خاموش رہتا ہے اور صرف وصل کے لیے ہوتا ہے۔",
        "desc_hi": "Woh hamza jo adaigi mein khamosh rehta hai aur wasl ke liye hota hai.",
    },
    "laam_shamsiyah": {
        "category": "laam",
        "name_en": "Lam Shamsiyyah",
        "name_ar": "اللام الشمسية",
        "desc_en": "Sun-letter lam that is merged into the following sun letter.",
        "desc_ur": "شمسی حرف کے ساتھ لام جو شمسی حرف میں مدغم ہو جاتی ہے۔",
        "desc_hi": "Shamsi harf ke sath lam jo shamsi harf mein idgham ho jati hai.",
    },
    "madda_normal": {
        "category": "madd",
        "name_en": "Madd Tabii (Natural)",
        "name_ar": "المد الطبيعي",
        "desc_en": "Natural elongation of two harakat.",
        "desc_ur": "قدرتی مد جو دو حرکات تک ہوتی ہے۔",
        "desc_hi": "Qudrati madd jo do harakat tak hoti hai.",
    },
    "madda_permissible": {
        "category": "madd",
        "name_en": "Madd Ja'iz (Permissible)",
        "name_ar": "المد الجائز",
        "desc_en": "Permissible elongation of two to four harakat due to a hamza.",
        "desc_ur": "جوازی مد جو دو سے چار حرکات تک ہو سکتی ہے۔",
        "desc_hi": "Jaiz madd jo do se char harakat tak ho sakti hai.",
    },
    "madda_obligatory": {
        "category": "madd",
        "name_en": "Madd Wajib (Obligatory)",
        "name_ar": "المد الواجب",
        "desc_en": "Obligatory elongation of four to five harakat due to a hamza.",
        "desc_ur": "واجب مد جو چار سے پانچ حرکات تک ہوتی ہے۔",
        "desc_hi": "Wajib madd jo char se panch harakat tak hoti hai.",
    },
    "madda_necessary": {
        "category": "madd",
        "name_en": "Madd Lazim (Necessary)",
        "name_ar": "المد اللازم",
        "desc_en": "Necessary elongation of six harakat due to a sukoon.",
        "desc_ur": "لازمی مد جو چھ حرکات تک ہوتی ہے۔",
        "desc_hi": "Lazmi madd jo chhah harakat tak hoti hai.",
    },
    "slnt": {
        "category": "madd",
        "name_en": "Madd 'Arid (Silent/Weak)",
        "name_ar": "المد العارض",
        "desc_en": "Incidental elongation that appears only at a stopping pause.",
        "desc_ur": "عارضی مد جو صرف وقف کے وقت طویل ہو جاتی ہے۔",
        "desc_hi": "Aarzi madd jo sirf waqf ke waqt taweel ho jati hai.",
    },
    "ghunnah": {
        "category": "ghunnah",
        "name_en": "Ghunnah (Nasalisation)",
        "name_ar": "الغنة",
        "desc_en": "Nasal resonance of two harakat on mim/nun with shadda.",
        "desc_ur": "نون یا میم کی تشدید کے ساتھ ناک سے آواز کا نکلنا۔",
        "desc_hi": "Noon ya meem ki tashdeed ke sath naak se awaz ka nikalna.",
    },
    "ikhafa": {
        "category": "noon",
        "name_en": "Ikhfa (Concealment)",
        "name_ar": "الإخفاء",
        "desc_en": "Concealment of noon/tanween before certain letters.",
        "desc_ur": "نون یا تنوین کو کچھ حروف کے سامنے چھپا کر ادا کرنا۔",
        "desc_hi": "Noon ya tanween ko kuch huroof ke samne chhupa kar ada karna.",
    },
    "ikhafa_shafawi": {
        "category": "mim",
        "name_en": "Ikhfa Shafawi (Labial Concealment)",
        "name_ar": "الإخفاء الشفوي",
        "desc_en": "Concealment of mim before ba.",
        "desc_ur": "میم کے بعد آنے والے باء کو چھپا کر ادا کرنا۔",
        "desc_hi": "Meem ke baad aane wale baa ko chhupa kar ada karna.",
    },
    "qalaqah": {
        "category": "qalqalah",
        "name_en": "Qalqalah (Echoing)",
        "name_ar": "القلقلة",
        "desc_en": "Bouncing/echoing sound on qaf, ta, ba, jim, dal.",
        "desc_ur": "قاف، طاء، باء، جیم، دال پر وقف کے ساتھ آواز کا واپس آنے کا اثر۔",
        "desc_hi": "Qaf, taa, baa, jeem, dal par waqf ke sath awaz ka wapas aane ka asar.",
    },
    "idgham_ghunnah": {
        "category": "noon",
        "name_en": "Idgham bi Ghunnah (Merging with Nasalisation)",
        "name_ar": "الإدغام بغنة",
        "desc_en": "Merging of noon/tanween into ya, waw, mim, nun, lam, ra with ghunnah.",
        "desc_ur": "نون یا تنوین کو یاء، واو، میم، نون، لم، راء میں بغنّہ ملا کر ادا کرنا۔",
        "desc_hi": "Noon ya tanween ko ya, waw, meem, noon, lam, ra mein bi-ghunnah mila kar ada karna.",
    },
    "idgham_wo_ghunnah": {
        "category": "noon",
        "name_en": "Idgham bila Ghunnah (Merging without Nasalisation)",
        "name_ar": "الإدغام بغير غنة",
        "desc_en": "Merging of noon/tanween into similar/near letters without ghunnah.",
        "desc_ur": "نون یا تنوین کو بغیر غنّہ کے ملا کر ادا کرنا۔",
        "desc_hi": "Noon ya tanween ko baghair ghunnah ke mila kar ada karna.",
    },
    "idgham_shafawi": {
        "category": "mim",
        "name_en": "Idgham Shafawi (Labial Merging)",
        "name_ar": "الإدغام الشفوي",
        "desc_en": "Merging of mim into a following mim.",
        "desc_ur": "میم کے بعد آنے والی میم کو ملا کر ادا کرنا۔",
        "desc_hi": "Meem ke baad aane wali meem ko mila kar ada karna.",
    },
    "iqlab": {
        "category": "noon",
        "name_en": "Iqlab (Conversion)",
        "name_ar": "الإقلاب",
        "desc_en": "Conversion of noon/tanween into mim before ba.",
        "desc_ur": "نون یا تنوین کو باء کے سامنے میم میں بدلنا۔",
        "desc_hi": "Noon ya tanween ko baa ke samne meem mein badalna.",
    },
    "idgham_mutajanisayn": {
        "category": "noon",
        "name_en": "Idgham Mutajanisayn (Similar Letters)",
        "name_ar": "الإدغام المتجانسين",
        "desc_en": "Merging of noon/tanween into letters of the same articulation point.",
        "desc_ur": "نون یا تنوین کا ہم مخرج حروف میں ملنا۔",
        "desc_hi": "Noon ya tanween ka ham-makhraj huroof mein milna.",
    },
}

# Reverse lookup: class name → info (avoids repeated dict lookups)
_DEFAULT_RULE = {
    "category": "other",
    "name_en": "Unknown",
    "name_ar": "",
    "desc_en": "",
    "desc_ur": "",
    "desc_hi": "",
}


# Regex to match <tajweed class=X>...</tajweed> tags
_TAG_RE = re.compile(r"<tajweed class=([^>\s]+)>(.*?)</tajweed>", re.DOTALL)

# Regex to match verse-end spans (e.g. <span class=end>١</span>) — stripped whole
_SPAN_RE = re.compile(r"<span[^>]*>.*?</span>", re.DOTALL)

# Regex to remove tajweed tag markers while keeping their content
_TAJWEED_MARKUP_RE = re.compile(r"</?tajweed[^>]*>")


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
            annotations (list of dicts with rule_category, rule_name,
                         rule_name_arabic, description_en/ur/hi_latn,
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
        """Remove all tajweed markup, returning plain Uthmani text.

        Verse-end ``<span class=end>..</span>`` markers are removed entirely
        (including their digit) so the result aligns with the word forms.
        """
        text = _SPAN_RE.sub("", text)
        text = _TAJWEED_MARKUP_RE.sub("", text)
        return text

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

        for match in _TAG_RE.finditer(tajweed_text):
            class_name = match.group(1)
            fragment = match.group(2)

            info = TAJWEED_CLASSES.get(class_name, _DEFAULT_RULE)
            rule_name = info["name_en"] or class_name
            description_en = info["desc_en"]

            # Compute the character offset of this fragment in the plain text.
            # Everything before this match in the tagged text, minus tags,
            # gives us the plain-text offset.
            tagged_before = tajweed_text[: match.start()]
            plain_before = self._strip_markup(tagged_before)
            char_start = len(plain_before)
            char_end = char_start + len(fragment)

            annotations.append({
                "rule_category": info["category"],
                "rule_name": rule_name,
                "rule_name_arabic": info["name_ar"],
                "description_en": description_en,
                "description_ur": info["desc_ur"],
                "description_hi_latn": info["desc_hi"],
                # Backwards-compatible aliases consumed by loaders
                "rule_id": class_name,
                "description": description_en,
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
        word_forms = [
            w.get("form") or w.get("text_uthmani") or w.get("text_arabic")
            or w.get("text") or ""
            for w in words
        ]
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
