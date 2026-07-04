"""
Tests for ETL parsers: CorpusParser POS mapping, root extraction,
TajweedParser markup parsing, and AudioSegmentParser.
"""

import os
import tempfile
import unittest

from etl.parsers.corpus_parser import CorpusParser, POS_GROUP_MAP
from etl.parsers.tajweed_parser import TajweedParser, TAJWEED_RULES
from etl.parsers.audio_segment_parser import AudioSegmentParser


# ---------------------------------------------------------------------------
# CorpusParser tests
# ---------------------------------------------------------------------------

class TestCorpusParserPOSMapping(unittest.TestCase):
    """Test POS tag → group mapping (ism/fil/harf)."""

    def test_noun_maps_to_ism(self):
        """N, PN, ADJ, DET, PRON should map to 'ism'."""
        for tag in ["N", "PN", "ADJ", "DET", "PRON"]:
            self.assertEqual(
                POS_GROUP_MAP[tag], "ism",
                f"Tag {tag} should map to 'ism'"
            )

    def test_verb_maps_to_fil(self):
        """V, PV, IV, IMPV should map to 'fil'."""
        for tag in ["V", "PV", "IV", "IMPV"]:
            self.assertEqual(
                POS_GROUP_MAP[tag], "fil",
                f"Tag {tag} should map to 'fil'"
            )

    def test_particle_maps_to_harf(self):
        """P, PREP, CONJ, NEG, INTG should map to 'harf'."""
        for tag in ["P", "PREP", "CONJ", "NEG", "INTG", "ACC", "PRO"]:
            self.assertEqual(
                POS_GROUP_MAP[tag], "harf",
                f"Tag {tag} should map to 'harf'"
            )

    def test_unknown_tag_defaults_to_harf(self):
        """Unknown tags should default to 'harf'."""
        self.assertEqual(POS_GROUP_MAP.get("UNKNOWN_TAG", "harf"), "harf")


class TestCorpusParserMorphology(unittest.TestCase):
    """Test parsing of the corpus TSV morphology file."""

    SAMPLE_TSV = """# Quranic Arabic Corpus Morphology File
# Format: location	form	tag	features	lemma	root	gloss
2:1:1	الٓمٓ	DET	Al|ROOT:alm|LEM:الٓمٓ	الٓمٓ	alm	Alif Lam Mim
2:1:2	ٓ	P	N	;	;
2:255:1	ٱللَّهُ	PN	DEM|ROOT:Allh|LEM:ٱللَّهُ	ٱللَّهُ	Allh	Allah
2:255:2	لَا	NEG	NEG|ROOT:lA|LEM:لَا	لَا	lA	No
2:255:3	خَلْقٌ	N	ROOT:xlq|LEM:خَلْق	خَلْق	xlq	creation
3:45:1:1	إِذْ	P	COND|ROOT:|LEM:إِذْ	إِذْ	;	when
"""

    def setUp(self):
        self.parser = CorpusParser()
        # Write sample TSV to a temp file
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        self.tmp.write(self.SAMPLE_TSV)
        self.tmp.close()
        self.tmp_path = self.tmp.name

    def tearDown(self):
        os.unlink(self.tmp_path)

    def test_parse_morphology_file_returns_words(self):
        """Parsing should return a list of word dicts."""
        words = self.parser.parse_morphology_file(self.tmp_path)
        self.assertIsInstance(words, list)
        self.assertGreater(len(words), 0)

    def test_parsed_word_has_required_fields(self):
        """Each parsed word should have all required fields."""
        words = self.parser.parse_morphology_file(self.tmp_path)
        required = {"surah", "ayah", "word", "form", "pos_tag", "pos_group",
                     "lemma", "root", "features", "location"}
        for w in words:
            missing = required - set(w.keys())
            self.assertEqual(missing, set(), f"Missing fields: {missing}")

    def test_pos_group_assignment(self):
        """POS groups should be correctly assigned from tags."""
        words = self.parser.parse_morphology_file(self.tmp_path)
        # First word is DET → ism
        self.assertEqual(words[0]["pos_group"], "ism")
        # Find the NEG word
        neg_words = [w for w in words if w["pos_tag"] == "NEG"]
        self.assertTrue(len(neg_words) > 0)
        self.assertEqual(neg_words[0]["pos_group"], "harf")

    def test_features_parsed_as_dict(self):
        """Features should be parsed into a dict."""
        words = self.parser.parse_morphology_file(self.tmp_path)
        for w in words:
            self.assertIsInstance(w["features"], dict)

    def test_comments_skipped(self):
        """Lines starting with # should be skipped."""
        words = self.parser.parse_morphology_file(self.tmp_path)
        # Our sample has 6 data lines (2 comment lines)
        self.assertEqual(len(words), 6)

    def test_location_parsing(self):
        """Location strings should be parsed into surah, ayah, word."""
        words = self.parser.parse_morphology_file(self.tmp_path)
        first = words[0]
        self.assertEqual(first["surah"], 2)
        self.assertEqual(first["ayah"], 1)
        self.assertEqual(first["word"], 1)


class TestCorpusParserRoots(unittest.TestCase):
    """Test root extraction from parsed words."""

    def test_extract_roots_counts_occurrences(self):
        """Roots should be extracted with correct occurrence counts."""
        parser = CorpusParser()
        words = [
            {"root": "ktb", "lemma": "كتاب", "form": "كِتَاب"},
            {"root": "ktb", "lemma": "كتب", "form": "كَتَبَ"},
            {"root": "slm", "lemma": "سلام", "form": "سَلَام"},
            {"root": None, "lemma": None, "form": "و"},
        ]
        roots = parser.extract_roots(words)

        self.assertEqual(len(roots), 2)  # ktb and slm

        # ktb has 2 occurrences, slm has 1
        ktb = next(r for r in roots if r["root"] == "ktb")
        self.assertEqual(ktb["occurrence_count"], 2)
        self.assertIn("كتاب", ktb["unique_lemmas"])
        self.assertIn("كتب", ktb["unique_lemmas"])

        slm = next(r for r in roots if r["root"] == "slm")
        self.assertEqual(slm["occurrence_count"], 1)

    def test_extract_roots_sorted_by_count(self):
        """Roots should be sorted by occurrence count descending."""
        parser = CorpusParser()
        words = [
            {"root": "a", "lemma": "l1", "form": "f1"},
            {"root": "a", "lemma": "l2", "form": "f2"},
            {"root": "a", "lemma": "l3", "form": "f3"},
            {"root": "b", "lemma": "l4", "form": "f4"},
        ]
        roots = parser.extract_roots(words)
        self.assertEqual(roots[0]["root"], "a")
        self.assertEqual(roots[0]["occurrence_count"], 3)
        self.assertEqual(roots[1]["root"], "b")
        self.assertEqual(roots[1]["occurrence_count"], 1)

    def test_transliteration(self):
        """Root transliteration should produce Latin characters."""
        parser = CorpusParser()
        translit = parser._transliterate_root("كتب")
        self.assertIsInstance(translit, str)
        self.assertTrue(all(c.isascii() or c == "?" for c in translit))


# ---------------------------------------------------------------------------
# TajweedParser tests
# ---------------------------------------------------------------------------

class TestTajweedParser(unittest.TestCase):
    """Test tajweed markup parsing."""

    def test_tajweed_rules_mapping(self):
        """All 9 rule IDs should be mapped."""
        self.assertEqual(len(TAJWEED_RULES), 9)
        self.assertEqual(TAJWEED_RULES[1], "ghunnah")
        self.assertEqual(TAJWEED_RULES[2], "qalqalah")
        self.assertEqual(TAJWEED_RULES[3], "ikhfa")
        self.assertEqual(TAJWEED_RULES[4], "idgham")
        self.assertEqual(TAJWEED_RULES[5], "iqlab")
        self.assertEqual(TAJWEED_RULES[6], "madd_2")
        self.assertEqual(TAJWEED_RULES[7], "madd_4_5")
        self.assertEqual(TAJWEED_RULES[8], "madd_6")
        self.assertEqual(TAJWEED_RULES[9], "madd_2_necessary")

    def test_strip_markup(self):
        """Markup tags should be stripped from text."""
        parser = TajweedParser()
        text = "بِسْمِ<1> ٱللَّهِ</1> ٱلرَّحْمَٰنِ"
        plain = parser._strip_markup(text)
        self.assertNotIn("<1>", plain)
        self.assertNotIn("</1>", plain)
        self.assertIn("ٱللَّهِ", plain)

    def test_parse_ayah_extracts_annotations(self):
        """parse_ayah should extract structured annotations."""
        parser = TajweedParser()
        # Simple example: ghunnah tag wrapping "ٱللَّهِ"
        tajweed_text = "بِسْمِ<1>ٱللَّهِ</1>ٱلرَّحْمَٰنِ"
        result = parser.parse_ayah(1, 1, tajweed_text)

        self.assertEqual(result["surah"], 1)
        self.assertEqual(result["ayah"], 1)
        self.assertIsInstance(result["annotations"], list)
        self.assertGreater(len(result["annotations"]), 0)

        ann = result["annotations"][0]
        self.assertEqual(ann["rule_id"], 1)
        self.assertEqual(ann["rule_name"], "ghunnah")
        self.assertEqual(ann["text_fragment"], "ٱللَّهِ")

    def test_parse_ayah_multiple_rules(self):
        """Multiple tajweed rules in one ayah should all be extracted."""
        parser = TajweedParser()
        tajweed_text = "<2>قُلْ</2> هُوَ <6>ٱللَّهُ</6> أَحَدٌ"
        result = parser.parse_ayah(112, 1, tajweed_text)

        self.assertEqual(len(result["annotations"]), 2)
        rules = [a["rule_id"] for a in result["annotations"]]
        self.assertIn(2, rules)  # qalqalah
        self.assertIn(6, rules)  # madd_2

    def test_parse_ayah_char_offsets(self):
        """Character offsets should be relative to the plain text."""
        parser = TajweedParser()
        tajweed_text = "بِسْمِ<1>ٱللَّهِ</1>ٱلرَّحْمَٰنِ"
        result = parser.parse_ayah(1, 1, tajweed_text)

        plain = result["plain_text"]
        ann = result["annotations"][0]
        # The fragment should be at the correct position in plain text
        fragment_in_plain = plain[ann["char_start"]:ann["char_end"]]
        self.assertEqual(fragment_in_plain, ann["text_fragment"])

    def test_parse_ayah_no_markup(self):
        """Ayah with no markup should return empty annotations."""
        parser = TajweedParser()
        result = parser.parse_ayah(1, 1, "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ")
        self.assertEqual(len(result["annotations"]), 0)

    def test_word_mapping(self):
        """Annotations should be mapped to word indices when words provided."""
        parser = TajweedParser()
        tajweed_text = "<1>كَلِمَة</1> أُخْرَىٰ"
        words = [
            {"form": "كَلِمَة"},
            {"form": "أُخْرَىٰ"},
        ]
        result = parser.parse_ayah(1, 1, tajweed_text, words)
        ann = result["annotations"][0]
        self.assertIn(0, ann["word_indices"])  # First word


# ---------------------------------------------------------------------------
# AudioSegmentParser tests
# ---------------------------------------------------------------------------

class TestAudioSegmentParser(unittest.TestCase):
    """Test audio segment parsing."""

    def test_parse_basic_segments(self):
        """Basic 3-element segments should be parsed correctly."""
        parser = AudioSegmentParser()
        segments = [
            [0, 4200, 0],
            [4200, 5100, 1],
            [5100, 6800, 2],
        ]
        timings = parser.parse_segments(segments)
        self.assertEqual(len(timings), 3)
        self.assertEqual(timings[1]["word_position"], 1)
        self.assertEqual(timings[1]["start_ms"], 4200)
        self.assertEqual(timings[1]["end_ms"], 5100)
        self.assertEqual(timings[1]["duration_ms"], 900)

    def test_silence_detection(self):
        """Word position <= 0 should be flagged as silence."""
        parser = AudioSegmentParser()
        segments = [[0, 500, 0], [500, 1200, 1]]
        timings = parser.parse_segments(segments)
        self.assertTrue(timings[0]["is_silence"])
        self.assertFalse(timings[1]["is_silence"])

    def test_empty_segments(self):
        """Empty or None segments should return empty list."""
        parser = AudioSegmentParser()
        self.assertEqual(parser.parse_segments(None), [])
        self.assertEqual(parser.parse_segments([]), [])

    def test_malformed_segments_skipped(self):
        """Malformed segments should be skipped, not crash."""
        parser = AudioSegmentParser()
        segments = [
            [0, 1000, 1],
            [1000],  # Too short
            None,
            [2000, 3000, 2],
        ]
        timings = parser.parse_segments(segments)
        self.assertEqual(len(timings), 2)  # Only 2 valid

    def test_four_element_segments(self):
        """4-element segments should include verse_segment."""
        parser = AudioSegmentParser()
        segments = [[0, 1000, 1, 5]]
        timings = parser.parse_segments(segments)
        self.assertEqual(timings[0]["verse_segment"], 5)


if __name__ == "__main__":
    unittest.main()
