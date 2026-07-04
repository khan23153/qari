"""Tests for word-level alignment."""
import pytest
from ml.alignment.word_alignment import align_words, _char_levenshtein


class TestCharLevenshtein:
    def test_identical(self):
        assert _char_levenshtein("abc", "abc") == 0

    def test_one_substitution(self):
        assert _char_levenshtein("abc", "abd") == 1

    def test_one_insertion(self):
        assert _char_levenshtein("abc", "abcd") == 1

    def test_empty(self):
        assert _char_levenshtein("", "abc") == 3


class TestAlignWords:
    def test_all_correct(self):
        expected = ["bismi", "llahi", "rahmani", "raheemi"]
        hypothesis = ["bismi", "llahi", "rahmani", "raheemi"]
        results = align_words(expected, hypothesis)
        assert all(r["verdict"] == "correct" for r in results)

    def test_omitted_word(self):
        expected = ["bismi", "llahi", "rahmani", "raheemi"]
        hypothesis = ["bismi", "rahmani", "raheemi"]
        results = align_words(expected, hypothesis)
        verdicts = [r["verdict"] for r in results]
        assert "omitted" in verdicts

    def test_inserted_extra(self):
        expected = ["bismi", "llahi"]
        hypothesis = ["bismi", "llahi", "extra"]
        results = align_words(expected, hypothesis)
        verdicts = [r["verdict"] for r in results]
        assert "inserted_extra" in verdicts
