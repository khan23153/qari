"""Loss labels must preserve the independently verified spoken transcript."""
import importlib
import importlib.util

import pytest


def subject():
    name = "ml.training.conformer_transcripts"
    assert importlib.util.find_spec(name) is not None, "PCD transcript boundary is missing"
    return importlib.import_module(name)


def test_pcd_text_preserves_vowels_hamza_and_alif_maqsura():
    text = "أَلَمْ يَجِدْكَ يَتِيمًا فَآوَى"
    assert subject().prepare_pcd_transcript(text) == text


def test_pcd_text_removes_display_annotations_without_removing_short_vowels():
    assert subject().prepare_pcd_transcript("\ufeff  فَآوَىٰۚ  \n") == "فَآوَى"


@pytest.mark.parametrize("text", ["لَهُۥ", "بِهِۦ"])
def test_pcd_cleanup_cannot_silently_delete_arabic_small_letters(text):
    assert subject().prepare_pcd_transcript(text) == text


def test_meaningful_small_high_yeh_and_long_vowel_annotation_are_preserved():
    text = subject().prepare_pcd_transcript("إِبْرَٰهِـۧمَ")
    assert "ۧ" in text
    assert "ٰ" in text


def test_dagger_alif_in_ar_rahman_is_not_silently_deleted():
    assert subject().prepare_pcd_transcript("الرَّحْمَٰنِ").count("ٰ") == 1


def test_nonspoken_rub_marker_is_removed_from_published_ayah():
    assert subject().prepare_pcd_transcript("۞ أَوَلَمْ يَرَوْا") == "أَوَلَمْ يَرَوْا"


@pytest.mark.parametrize("text,plain", [("فَآوَى", "فآوى"), ("فَأَبَى", "فأبى")])
def test_published_label_variants_change_only_optional_short_vowels(text, plain):
    module = subject()
    assert hasattr(module, "pcd_transcript_variants"), "Published label variants are missing"
    assert module.pcd_transcript_variants(text) == (text, plain)


def test_unvocalized_published_label_does_not_duplicate_variants():
    module = subject()
    assert hasattr(module, "pcd_transcript_variants"), "Published label variants are missing"
    assert module.pcd_transcript_variants("فآوى") == ("فآوى",)


def test_training_tokenizer_receives_training_text_instead_of_matcher_key():
    class Tokenizer:
        unk_id = 0

        def text_to_ids(self, text):
            self.received = text
            return [13, 41, 7]

    tokenizer = Tokenizer()
    row = {"training_text": "فَآوَى", "normalized_text": "فاوي"}
    assert subject().tokenize_pcd_transcript(row, tokenizer) == [13, 41, 7]
    assert tokenizer.received == "فَآوَى"


def test_unknown_token_cannot_enter_training_loss():
    class Tokenizer:
        unk_id = 0

        def text_to_ids(self, text):
            return [13, 0, 7]

    with pytest.raises(ValueError, match="unknown"):
        subject().tokenize_pcd_transcript({"training_text": "فَآوَى"}, Tokenizer())


def test_tokenizer_must_declare_its_unknown_token_boundary():
    class Tokenizer:
        def text_to_ids(self, text):
            return [13, 7]

    with pytest.raises(ValueError, match="unknown"):
        subject().tokenize_pcd_transcript({"training_text": "فَآوَى"}, Tokenizer())


@pytest.mark.parametrize("row", [{"normalized_text": "فاوي"}, {"expected_text": "فَآوَى"}])
def test_matching_or_expected_reference_text_cannot_supply_training_label(row):
    with pytest.raises(ValueError, match="training_text"):
        subject().tokenize_pcd_transcript(row, object())


@pytest.mark.parametrize("text", [None, "", " \n ", 123, "۞"])
def test_pcd_transcript_requires_nonempty_actual_text(text):
    with pytest.raises(ValueError, match="transcript"):
        subject().prepare_pcd_transcript(text)
