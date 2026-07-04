"""Quranic Arabic Corpus parser — POS tags, morphology, roots.

The morphology dataset is a downloadable, versioned file from corpus.quran.com
(GNU-licensed, by Kais Dukes). Parse offline and load into the DB.
"""
import csv
import json
from typing import Any
import structlog

log = structlog.get_logger()


class CorpusParser:
    """Parse the Quranic Arabic Corpus morphology file."""

    # POS group mapping from corpus POS tags to our ism/fil/harf groups
    POS_GROUP_MAP = {
        "N": "ism",      # Noun
        "PN": "ism",     # Proper Noun
        "ADJ": "ism",    # Adjective
        "DET": "ism",    # Determiner
        "PRON": "ism",   # Pronoun
        "V": "fil",      # Verb
        "P": "harf",     # Particle
        "REL": "harf",   # Relative pronoun
        "ACC": "harf",   # Accusative particle
        "COND": "harf",  # Conditional particle
        "SUB": "harf",   # Subordinating conjunction
        "PREV": "harf",  # Preventive particle
        "INL": "harf",   # Interrogative particle
        "INTG": "harf",  # Interrogative particle
        "NEG": "harf",   # Negative particle
        "PRP": "harf",   # Preposition
        "PRO": "harf",   # Particle of response
        "EXL": "harf",   # Exlamatory particle
        "IMP": "harf",   # Imperative particle
        "REM": "harf",   # Resumption particle
        "AVR": "harf",   # Arabic verb root
        "CIRC": "harf",  # Circumstantial particle
        "RSLT": "harf",  # Result particle
        "EMPH": "harf",  # Emphatic particle
        "AMP": "harf",   # Amending particle
        "FUT": "harf",   # Future particle
        "INC": "harf",   # Inceptive particle
        "ANS": "harf",   # Answer particle
        "EQ": "harf",    # Equal particle
        "EXH": "harf",   # Exhortation particle
        "EXP": "harf",   # Explanation particle
        "RES": "harf",   # Restriction particle
        "PROG": "harf",  # Progressive particle
    }

    def parse_morphology_file(self, file_path: str) -> list[dict]:
        """Parse the corpus morphology CSV/TSV file.

        Expected columns: surah, ayah, word, segment, pos, features, root, lemma
        """
        words = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                pos_tag = row.get("pos", "").strip()
                pos_group = self.POS_GROUP_MAP.get(pos_tag, "harf")

                word_data = {
                    "surah_number": int(row["surah"]),
                    "ayah_number": int(row["ayah"]),
                    "word_position": int(row["word"]),
                    "pos_tag": pos_tag,
                    "pos_group": pos_group,
                    "lemma": row.get("lemma", "").strip() or None,
                    "root_arabic": row.get("root", "").strip() or None,
                    "morphology": self._parse_features(row.get("features", "")),
                }
                words.append(word_data)

        log.info("Parsed corpus morphology", word_count=len(words))
        return words

    def _parse_features(self, features_str: str) -> list[dict]:
        """Parse the features field into structured morphology segments."""
        if not features_str:
            return []
        # Features format: "seg:pos:feat1|feat2|feat3"
        segments = []
        for seg_entry in features_str.split(";"):
            parts = seg_entry.split(":")
            if len(parts) >= 2:
                segments.append({
                    "segment": parts[0],
                    "pos": parts[1],
                    "features": parts[2].split("|") if len(parts) > 2 else [],
                })
        return segments

    def extract_roots(self, words: list[dict]) -> list[dict]:
        """Extract unique roots from parsed words."""
        roots_map = {}
        for w in words:
            root_ar = w.get("root_arabic")
            if not root_ar:
                continue
            if root_ar not in roots_map:
                roots_map[root_ar] = {
                    "root_arabic": root_ar,
                    "occurrence_count": 0,
                }
            roots_map[root_ar]["occurrence_count"] += 1

        roots = []
        for idx, (root_ar, data) in enumerate(sorted(roots_map.items()), start=1):
            roots.append({
                "root_id": idx,
                "root_arabic": root_ar,
                "root_translit": self._transliterate_root(root_ar),
                "core_meaning": {"en": "", "hi_latn": ""},  # To be filled by content team
                "occurrence_count": data["occurrence_count"],
            })

        log.info("Extracted roots", count=len(roots))
        return roots

    def _transliterate_root(self, root_arabic: str) -> str:
        """Simple transliteration for root letters."""
        mapping = {
            "ا": "A", "ب": "B", "ت": "T", "ث": "TH", "ج": "J", "ح": "H",
            "خ": "KH", "د": "D", "ذ": "DH", "ر": "R", "ز": "Z", "س": "S",
            "ش": "SH", "ص": "S", "ض": "D", "ط": "T", "ظ": "Z", "ع": "A",
            "غ": "GH", "ف": "F", "ق": "Q", "ك": "K", "ل": "L", "م": "M",
            "ن": "N", "ه": "H", "و": "W", "ي": "Y", "ء": "",
        }
        return "-".join(mapping.get(c, c) for c in root_arabic if c.strip())
