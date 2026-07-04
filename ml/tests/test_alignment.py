"""
Tests for word-level Levenshtein alignment.

Covers: all correct, omitted words, inserted words, mispronounced words,
low confidence, and edge cases (empty inputs, single word).
"""

import pytest
from ml.alignment.word_alignment import (
    WordAligner,
    WordVerdict,
    AlignmentResult,
    AlignedWord,
)


class TestAllCorrect:
    """Tests where hypothesis perfectly matches reference."""

    def test_all_correct_simple(self):
        """All words match → all CORRECT."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن", "الرحيم"]
        hyp = ["بسم", "الله", "الرحمن", "الرحيم"]
        result = aligner.align(ref, hyp)

        assert result.match_count == 4
        assert result.mismatch_count == 0
        assert result.omission_count == 0
        assert result.insertion_count == 0
        assert result.correct_ratio == 1.0
        for w in result.aligned_words:
            assert w.verdict == WordVerdict.CORRECT

    def test_all_correct_single_word(self):
        """Single word match."""
        aligner = WordAligner()
        result = aligner.align(["الحمد"], ["الحمد"])
        assert result.match_count == 1
        assert result.aligned_words[0].verdict == WordVerdict.CORRECT

    def test_all_correct_empty(self):
        """Both empty → no words."""
        aligner = WordAligner()
        result = aligner.align([], [])
        assert result.total_verdicts == 0
        assert result.match_count == 0


class TestOmitted:
    """Tests where reference words are missing from hypothesis."""

    def test_all_omitted(self):
        """Hypothesis is empty → all reference words omitted."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن"]
        result = aligner.align(ref, [])

        assert result.omission_count == 3
        assert result.match_count == 0
        for w in result.aligned_words:
            assert w.verdict == WordVerdict.OMITTED
            assert w.hypothesis is None
            assert w.reference is not None

    def test_partial_omission(self):
        """One word omitted from the middle."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن", "الرحيم"]
        hyp = ["بسم", "الرحمن", "الرحيم"]  # "الله" omitted
        result = aligner.align(ref, hyp)

        assert result.omission_count == 1
        assert result.match_count == 3
        omitted = [w for w in result.aligned_words if w.verdict == WordVerdict.OMITTED]
        assert len(omitted) == 1
        assert omitted[0].reference == "الله"

    def test_omission_at_end(self):
        """Last word omitted."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن"]
        hyp = ["بسم", "الله"]
        result = aligner.align(ref, hyp)

        assert result.omission_count == 1
        assert result.match_count == 2

    def test_omission_at_start(self):
        """First word omitted."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن"]
        hyp = ["الله", "الرحمن"]
        result = aligner.align(ref, hyp)

        assert result.omission_count == 1
        assert result.match_count == 2


class TestInserted:
    """Tests where hypothesis has extra words not in reference."""

    def test_all_inserted(self):
        """Reference is empty → all hypothesis words are insertions."""
        aligner = WordAligner()
        hyp = ["كلمة", "زائدة"]
        result = aligner.align([], hyp)

        assert result.insertion_count == 2
        for w in result.aligned_words:
            assert w.verdict == WordVerdict.INSERTED_EXTRA
            assert w.reference is None

    def test_partial_insertion(self):
        """Extra word inserted in the middle."""
        aligner = WordAligner()
        ref = ["بسم", "الله"]
        hyp = ["بسم", "كلمة", "الله"]  # "كلمة" is extra
        result = aligner.align(ref, hyp)

        assert result.insertion_count == 1
        assert result.match_count == 2
        inserted = [w for w in result.aligned_words if w.verdict == WordVerdict.INSERTED_EXTRA]
        assert len(inserted) == 1
        assert inserted[0].hypothesis == "كلمة"


class TestMispronounced:
    """Tests where words are present but differ from reference."""

    def test_mispronounced_word(self):
        """A word is substituted with a different word."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن"]
        hyp = ["بسم", "الله", "الرحمن"]  # "الله" → "الله" (same, but test with different)
        # Use clearly different words
        ref = ["بسم", "الله", "الرحمن"]
        hyp = ["بسم", "ربي", "الرحمن"]  # "الله" → "ربي"
        result = aligner.align(ref, hyp)

        assert result.mismatch_count == 1
        assert result.match_count == 2
        misp = [w for w in result.aligned_words if w.verdict == WordVerdict.MISPRONOUNCED]
        assert len(misp) == 1
        assert misp[0].reference == "الله"
        assert misp[0].hypothesis == "ربي"

    def test_mispronounced_with_confidence(self):
        """Mispronounced word with high confidence → MISPRONOUNCED."""
        aligner = WordAligner(low_confidence_threshold=0.5)
        ref = ["الحمد", "لله"]
        hyp = ["الحمد", "للي"]  # Similar but different
        result = aligner.align(ref, hyp, confidences=[0.9, 0.9])

        # At least one mismatch
        assert result.mismatch_count + result.low_confidence_count >= 1

    def test_multiple_mispronounced(self):
        """Multiple words substituted."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن", "الرحيم"]
        hyp = ["سم", "الله", "الرحيم", "الرحمن"]  # Multiple substitutions/reorderings
        result = aligner.align(ref, hyp)

        # Should have some mismatches (not all correct)
        assert result.match_count < 4


class TestLowConfidence:
    """Tests for low-confidence classification."""

    def test_low_confidence_from_asr(self):
        """Word with very low ASR confidence → LOW_CONFIDENCE."""
        aligner = WordAligner(low_confidence_threshold=0.50)
        ref = ["الله", "الرحمن"]
        hyp = ["الله", "الرحمن"]
        # Give second word very low confidence
        result = aligner.align(ref, hyp, confidences=[0.95, 0.30])

        # The low-confidence word should be classified as low_confidence
        # (but since the words match, it should still be CORRECT —
        # low_confidence only applies to substitutions)
        # Let's test with a substitution instead
        ref = ["الله", "الرحمن"]
        hyp = ["الله", "الرحيم"]  # Different word
        result = aligner.align(ref, hyp, confidences=[0.95, 0.30])

        low_conf = [w for w in result.aligned_words if w.verdict == WordVerdict.LOW_CONFIDENCE]
        assert len(low_conf) >= 1

    def test_high_confidence_mispronounced(self):
        """Word with high confidence but different → MISPRONOUNCED (not low_confidence)."""
        aligner = WordAligner(low_confidence_threshold=0.50)
        ref = ["الله", "الرحمن"]
        hyp = ["الله", "الرحيم"]
        result = aligner.align(ref, hyp, confidences=[0.95, 0.90])

        misp = [w for w in result.aligned_words if w.verdict == WordVerdict.MISPRONOUNCED]
        assert len(misp) >= 1


class TestEdgeCases:
    """Edge case tests."""

    def test_single_word_correct(self):
        aligner = WordAligner()
        result = aligner.align(["كلمة"], ["كلمة"])
        assert result.match_count == 1

    def test_single_word_omitted(self):
        aligner = WordAligner()
        result = aligner.align(["كلمة"], [])
        assert result.omission_count == 1

    def test_single_word_inserted(self):
        aligner = WordAligner()
        result = aligner.align([], ["كلمة"])
        assert result.insertion_count == 1

    def test_align_from_strings(self):
        """Test the convenience method."""
        aligner = WordAligner()
        result = aligner.align_from_strings("بسم الله", "بسم الله")
        assert result.match_count == 2

    def test_alignment_score_positive_for_matches(self):
        """Alignment score should be positive when all words match."""
        aligner = WordAligner()
        result = aligner.align(["a", "b", "c"], ["a", "b", "c"])
        assert result.score > 0

    def test_ref_and_hyp_indices(self):
        """Check that ref_index and hyp_index are correctly assigned."""
        aligner = WordAligner()
        ref = ["بسم", "الله", "الرحمن"]
        hyp = ["بسم", "الله", "الرحمن"]
        result = aligner.align(ref, hyp)

        for i, w in enumerate(result.aligned_words):
            assert w.ref_index == i
            assert w.hyp_index == i
