"""Whisper lends vowel marks only to words the live engine also heard."""
import math
import re

from ml.alignment.harakat import compare_harakat
from ml.alignment.vowel_witness import lend_vowels

_MARKS = re.compile("[\u064b-\u065f\u0670]")


def _normalize(text: str) -> str:
    """Strip tashkeel and unify alif forms (as the live normalizer does)."""
    return _MARKS.sub("", text).translate(str.maketrans("أإآٱ", "اااا"))


RNNT = ["صراط", "الذين", "انعمت", "عليهم"]
RNNT_RAW = list(RNNT)  # RNNT emits no tashkeel


def lend(witness, confidences=None, native=RNNT, raw=RNNT_RAW):
    confidences = confidences or [0.9] * len(witness)
    return lend_vowels(native, raw, witness, confidences, _normalize)


def test_agreeing_words_get_whisper_marks_and_the_vowel_error_shows():
    out = lend(["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتُ", "عَلَيْهِمْ"])
    assert out == ["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتُ", "عَلَيْهِمْ"]
    assert compare_harakat("أَنْعَمْتَ", out[2], next_word_spoken=True).mismatch
    assert not compare_harakat("صِرَاطَ", out[0], next_word_spoken=True).mismatch


def test_a_vowel_error_does_not_shift_the_rest_of_the_alignment():
    out = lend(["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتِ", "عَلَيْهِمْ"])
    assert out[3] == "عَلَيْهِمْ"


def test_hallucinated_whisper_words_lend_nothing():
    out = lend(["صِرَاطَ", "الَّذِينَ", "مَا", "يَغْفَى", "مَا", "يَغْفَى"])
    assert out[:2] == ["صِرَاطَ", "الَّذِينَ"]
    assert out[2:] == ["انعمت", "عليهم"]


def test_a_misheard_base_word_keeps_the_live_engine_text():
    out = lend(["صِرَاطَ", "الَّذِينَ", "أَنْعَمْنَا", "عَلَيْهِمْ"])
    assert out[2] == "انعمت"


def test_low_confidence_or_unmarked_tokens_abstain():
    out = lend(["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتُ", "عليهم"], [0.9, 0.9, 0.3, 0.9])
    assert out[2] == "انعمت" and out[3] == "عليهم"
    out = lend(["صِرَاطَ", "الَّذِينَ", "أَنْعَمْتُ", "عَلَيْهِمْ"], [0.9, 0.9, math.nan, 0.9])
    assert out[2] == "انعمت"


def test_an_ambiguous_single_occurrence_abstains():
    native = ["الله", "احد", "الله"]
    out = lend(["اللَّهُ"], native=native, raw=list(native))
    assert out == native


def test_bad_inputs_leave_the_live_text_alone():
    assert lend([]) == RNNT_RAW
    assert lend_vowels(RNNT, None, ["صِرَاطَ"], [0.9], _normalize)[0] == "صِرَاطَ"
    assert lend_vowels(RNNT, RNNT_RAW, ["صِرَاطَ"], [], _normalize) == RNNT_RAW
