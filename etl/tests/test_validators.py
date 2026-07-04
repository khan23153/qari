"""
Tests for ETL validators: row count validation, checksum validation,
and diff against previous loads.
"""

import unittest

from etl.validators import ETLValidator, ValidationResult, DiffResult


# ---------------------------------------------------------------------------
# Row count validation tests
# ---------------------------------------------------------------------------

class TestRowCountValidation(unittest.TestCase):
    """Test validate_row_counts against expected canonical counts."""

    def setUp(self):
        self.validator = ETLValidator(
            expected_surahs=114,
            expected_ayahs=6236,
            expected_words=77430,
        )

    def test_exact_match_passes(self):
        """Exact match of all counts should pass."""
        result = self.validator.validate_row_counts(114, 6236, 77430)
        self.assertTrue(result.passed)
        self.assertEqual(len(result.errors), 0)

    def test_surah_count_mismatch_fails(self):
        """Wrong surah count should fail."""
        result = self.validator.validate_row_counts(113, 6236, 77430)
        self.assertFalse(result.passed)
        self.assertTrue(any("Surah count" in e for e in result.errors))

    def test_ayah_count_mismatch_fails(self):
        """Wrong ayah count should fail."""
        result = self.validator.validate_row_counts(114, 6235, 77430)
        self.assertFalse(result.passed)
        self.assertTrue(any("Ayah count" in e for e in result.errors))

    def test_word_count_mismatch_fails(self):
        """Wrong word count should fail."""
        result = self.validator.validate_row_counts(114, 6236, 77429)
        self.assertFalse(result.passed)
        self.assertTrue(any("Word count" in e for e in result.errors))

    def test_all_counts_wrong(self):
        """All counts wrong should produce 3 errors."""
        result = self.validator.validate_row_counts(0, 0, 0)
        self.assertFalse(result.passed)
        self.assertEqual(len(result.errors), 3)

    def test_metadata_includes_expected_and_actual(self):
        """Metadata should include both expected and actual counts."""
        result = self.validator.validate_row_counts(114, 6236, 77430)
        self.assertIn("surahs", result.metadata)
        self.assertEqual(result.metadata["surahs"]["expected"], 114)
        self.assertEqual(result.metadata["surahs"]["actual"], 114)


# ---------------------------------------------------------------------------
# Checksum validation tests
# ---------------------------------------------------------------------------

class TestChecksumValidation(unittest.TestCase):
    """Test checksum computation and validation."""

    def setUp(self):
        self.validator = ETLValidator()

    def test_compute_checksum_deterministic(self):
        """Same text should produce the same checksum."""
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        c1 = self.validator.compute_checksum(text)
        c2 = self.validator.compute_checksum(text)
        self.assertEqual(c1, c2)

    def test_compute_checksum_different_texts(self):
        """Different texts should produce different checksums."""
        c1 = self.validator.compute_checksum("text_one")
        c2 = self.validator.compute_checksum("text_two")
        self.assertNotEqual(c1, c2)

    def test_compute_checksum_is_sha256(self):
        """Checksum should be a 64-char hex string (SHA-256)."""
        checksum = self.validator.compute_checksum("test")
        self.assertEqual(len(checksum), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in checksum))

    def test_validate_checksums_returns_dict(self):
        """validate_checksums should return verse_key → checksum dict."""
        text_blocks = {
            "1:1": "بِسْمِ ٱللَّهِ",
            "1:2": "ٱلْحَمْدُ لِلَّهِ",
        }
        checksums = self.validator.validate_checksums(text_blocks)
        self.assertEqual(len(checksums), 2)
        self.assertIn("1:1", checksums)
        self.assertIn("1:2", checksums)

    def test_validate_checksums_empty_text_raises(self):
        """Empty text should raise ValueError."""
        with self.assertRaises(ValueError):
            self.validator.validate_checksums({"1:1": ""})


# ---------------------------------------------------------------------------
# Diff validation tests
# ---------------------------------------------------------------------------

class TestDiffValidation(unittest.TestCase):
    """Test diff_against_previous for Quranic text integrity."""

    def setUp(self):
        self.validator = ETLValidator()

    def test_identical_checksums_pass(self):
        """Identical checksums should produce identical=True."""
        checksums = {"1:1": "abc123", "1:2": "def456"}
        result = self.validator.diff_against_previous(checksums, dict(checksums))
        self.assertTrue(result.identical)
        self.assertEqual(len(result.changed), 0)

    def test_changed_checksum_fails(self):
        """A changed checksum should produce identical=False."""
        old = {"1:1": "abc123", "1:2": "def456"}
        new = {"1:1": "abc123", "1:2": "changed789"}
        result = self.validator.diff_against_previous(new, old)
        self.assertFalse(result.identical)
        self.assertEqual(len(result.changed), 1)
        self.assertEqual(result.changed[0][0], "1:2")

    def test_added_verses_reported(self):
        """New verses should be reported in 'added'."""
        old = {"1:1": "abc"}
        new = {"1:1": "abc", "1:2": "def"}
        result = self.validator.diff_against_previous(new, old)
        self.assertTrue(result.identical)  # No changes, just additions
        self.assertIn("1:2", result.added)

    def test_removed_verses_reported(self):
        """Removed verses should be reported in 'removed'."""
        old = {"1:1": "abc", "1:2": "def"}
        new = {"1:1": "abc"}
        result = self.validator.diff_against_previous(new, old)
        self.assertTrue(result.identical)  # No text changed
        self.assertIn("1:2", result.removed)

    def test_empty_previous_passes(self):
        """Empty previous checksums (first load) should pass."""
        new = {"1:1": "abc"}
        result = self.validator.diff_against_previous(new, {})
        self.assertTrue(result.identical)
        self.assertIn("1:1", result.added)

    def test_multiple_changes_all_reported(self):
        """Multiple changed verses should all be reported."""
        old = {"1:1": "a", "1:2": "b", "1:3": "c"}
        new = {"1:1": "x", "1:2": "y", "1:3": "c"}
        result = self.validator.diff_against_previous(new, old)
        self.assertFalse(result.identical)
        self.assertEqual(len(result.changed), 2)

    def test_diff_metadata(self):
        """Diff result should include summary metadata."""
        old = {"1:1": "a", "1:2": "b"}
        new = {"1:1": "a", "1:2": "c", "1:3": "d"}
        result = self.validator.diff_against_previous(new, old)
        self.assertEqual(result.metadata["new_count"], 3)
        self.assertEqual(result.metadata["old_count"], 2)
        self.assertEqual(result.metadata["changed_count"], 1)
        self.assertEqual(result.metadata["added_count"], 1)


# ---------------------------------------------------------------------------
# ValidationResult tests
# ---------------------------------------------------------------------------

class TestValidationResult(unittest.TestCase):
    """Test ValidationResult merge behaviour."""

    def test_merge_two_passing(self):
        """Merging two passing results should pass."""
        r1 = ValidationResult(passed=True)
        r2 = ValidationResult(passed=True)
        merged = r1.merge(r2)
        self.assertTrue(merged.passed)

    def test_merge_one_failing(self):
        """Merging with a failing result should fail."""
        r1 = ValidationResult(passed=True)
        r2 = ValidationResult(passed=False, errors=["error"])
        merged = r1.merge(r2)
        self.assertFalse(merged.passed)
        self.assertEqual(len(merged.errors), 1)

    def test_merge_accumulates_errors(self):
        """Merging should accumulate errors from both results."""
        r1 = ValidationResult(passed=False, errors=["e1"])
        r2 = ValidationResult(passed=False, errors=["e2"])
        merged = r1.merge(r2)
        self.assertEqual(len(merged.errors), 2)

    def test_bool_conversion(self):
        """ValidationResult should be truthy when passed."""
        self.assertTrue(ValidationResult(passed=True))
        self.assertFalse(ValidationResult(passed=False))


if __name__ == "__main__":
    unittest.main()
