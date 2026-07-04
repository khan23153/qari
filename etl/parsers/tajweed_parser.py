"""Tajweed annotation parser — derives tajweed_annotations from text_uthmani_tajweed.

Parses Quran.com's tajweed-markup text variant into structured rows.
"""
import re
from typing import Any
import structlog

log = structlog.get_logger()


# Tajweed rule color codes from Quran.com tajweed markup
TAJWEED_RULES = {
    "1": "ghunnah",           # nasalization (2 harakah)
    "2": "qalqalah",          # echoing/bouncing letter
    "3": "ikhfa",             # hiding (noon sakinah + ta/tha/etc.)
    "4": "idgham",            # merging (noon sakinah + ya/waw/mim/nun/lam/ra)
    "5": "iqlab",             # conversion (noon sakinah + ba)
    "6": "madd_2",            # normal madd (2 harakah)
    "7": "madd_4_5",          # extended madd (4-5 harakah)
    "8": "madd_6",            # longest madd (6 harakah)
    "9": "madd_2_necessary",  # necessary madd
}


class TajweedParser:
    """Parse tajweed-markup text into structured annotations."""

    # Quran.com uses HTML-like tags: <tajweed class="N">...</tajweed>
    TAJWEED_PATTERN = re.compile(
        r'<tajweed\s+class="([\d]+)"\s*>([^<]+)</tajweed>',
        re.IGNORECASE,
    )

    def parse_ayah(self, surah_number: int, ayah_number: int,
                   tajweed_text: str, words: list[dict]) -> list[dict]:
        """Parse tajweed markup for a single ayah.

        Args:
            tajweed_text: The text_uthmani_tajweed variant with markup tags
            words: List of word dicts with word_position and text_uthmani

        Returns:
            List of tajweed annotation dicts
        """
        annotations = []
        char_offset = 0
        word_idx = 0
        word_start = 0

        # Strip tajweed tags to get plain text and track positions
        clean_text = ""
        tag_positions = []  # (start, end, rule, text)

        last_end = 0
        for match in self.TAJWEED_PATTERN.finditer(tajweed_text):
            # Text before the tag
            clean_text += tajweed_text[last_end:match.start()]
            tag_start = len(clean_text)
            clean_text += match.group(2)
            tag_end = len(clean_text)
            rule_code = match.group(1)
            rule = TAJWEED_RULES.get(rule_code, f"unknown_{rule_code}")
            tag_positions.append((tag_start, tag_end, rule, match.group(2)))
            last_end = match.end()

        # Remaining text after last tag
        clean_text += tajweed_text[last_end:]

        # Map tag positions to words
        for word in words:
            word_text = word["text_uthmani"]
            word_end = word_start + len(word_text)

            for tag_start, tag_end, rule, tag_text in tag_positions:
                # Check if tag overlaps with this word
                if tag_start < word_end and tag_end > word_start:
                    char_start = max(0, tag_start - word_start)
                    char_end = min(len(word_text), tag_end - word_start)
                    annotations.append({
                        "surah_number": surah_number,
                        "ayah_number": ayah_number,
                        "word_position": word["word_position"],
                        "char_start": char_start,
                        "char_end": char_end,
                        "rule": rule,
                    })

            word_start = word_end
            # Skip space between words
            if word_idx < len(words) - 1:
                word_start += 1
            word_idx += 1

        return annotations
