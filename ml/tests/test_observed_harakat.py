"""Observed ASR-diacritic diagnostics, not acoustic pronunciation truth."""
import pytest

from ml.alignment.harakat import (
    compare_harakat,
    has_harakat_mistake,
    normalize_uthmani_harakat,
)


def test_dagger_alif_does_not_duplicate_fatha():
    text = normalize_uthmani_harakat('الرَّحْمَٰنِ')
    assert '\u0670' not in text
    assert '\u064e\u064e' not in text
    assert compare_harakat('الرَّحْمَٰنِ', text).mismatch is False


@pytest.mark.parametrize('spoken', ['الْعَالَمِين', 'الْعَالَمِينْ'])
def test_waqf_missing_or_sukun_final_vowel_is_valid(spoken):
    result = compare_harakat('الْعَالَمِينَ', spoken, is_ayah_end=True, is_stream_end=True)
    assert result.mismatch is False


@pytest.mark.parametrize('spoken', ['انعمت', 'أَنْعَمْت', 'أنعمتَ'])
def test_missing_and_partial_tashkeel_cannot_create_false_alarm(spoken):
    result = compare_harakat('أَنْعَمْتَ', spoken, next_word_spoken=True)
    assert result.mismatch is False
    assert not has_harakat_mistake('أَنْعَمْتَ', spoken, next_word_spoken=True)


def test_partial_marks_stay_attached_to_their_letters():
    # A flat vowel list misaligns these observed marks; letter positions do not.
    assert compare_harakat('أَنْعَمْتَ', 'أَنعمْتَ', next_word_spoken=True).mismatch is False


@pytest.mark.parametrize('context', [
    {'next_word_spoken': True},
    {'is_stream_end': True},
    {'is_ayah_end': True},
])
def test_explicit_conflicting_final_vowel_is_not_hidden_by_pause(context):
    result = compare_harakat('أَنْعَمْتَ', 'أَنْعَمْتُ', **context)
    assert result.mismatch is True
    assert result.conflicts[-1]['position'] == 4
    assert result.conflicts[-1]['expected'] == '\u064e'
    assert result.conflicts[-1]['observed'] == '\u064f'
    assert 4 in result.compared_positions


def test_stream_end_sukun_exempt_but_explicit_wasl_sukun_conflicts():
    assert not compare_harakat('أَنْعَمْتَ', 'أَنْعَمْتْ', is_stream_end=True).mismatch
    assert compare_harakat('أَنْعَمْتَ', 'أَنْعَمْتْ', next_word_spoken=True).mismatch


def test_no_final_vowel_does_not_become_invented_wasl_vowel():
    result = compare_harakat('أَنْعَمْتَ', 'أَنْعَمْت', next_word_spoken=True)
    assert not result.mismatch
    assert result.inconclusive


def test_unknown_canonical_vowel_and_lexical_mismatch_abstain():
    assert not compare_harakat('انعمت', 'أَنْعَمْتُ').mismatch
    result = compare_harakat('أَنْعَمْتَ', 'أَنْعَمْنَ')
    assert result.inconclusive and not result.mismatch
    assert result.compared_positions == ()


def test_conflicting_multiple_marks_are_inconclusive_not_accusation():
    result = compare_harakat('قُلْ', 'قَُلْ')
    assert not result.mismatch
    assert result.inconclusive


def test_interior_explicit_conflict_is_not_exempted_by_word_end():
    result = compare_harakat('قُلْ', 'قَلْ', is_stream_end=True, is_ayah_end=True)
    assert result.mismatch
    assert result.conflicts[0]['position'] == 0


@pytest.mark.parametrize('context', [
    {'is_ayah_end': True, 'is_stream_end': True},
    {'is_stream_end': True},
    {},
])
def test_fathatan_waqf_before_written_alif_abstains(context):
    result = compare_harakat('عَلِيمًا', 'عَلِيمَا', **context)
    assert not result.mismatch
    assert result.inconclusive
    assert 3 not in result.compared_positions


def test_fathatan_exception_does_not_hide_wasl_or_other_explicit_vowels():
    assert compare_harakat('عَلِيمًا', 'عَلِيمَا', next_word_spoken=True).mismatch
    assert compare_harakat('عَلِيمًا', 'عَلِيمُا', is_stream_end=True).mismatch
    assert compare_harakat('أَنْعَمْتَ', 'أَنْعَمْتُ', is_stream_end=True).mismatch


@pytest.mark.parametrize('spoken', ['أَنْعَمْتُ،', ' «أَنْعَمْتُ» ', '(أَنْعَمْتُ).'])
def test_surrounding_punctuation_preserves_explicit_vowel_evidence(spoken):
    result = compare_harakat('أَنْعَمْتَ', spoken, is_stream_end=True)
    assert result.mismatch
    assert result.conflicts == ({'position': 4, 'expected': '\u064e', 'observed': '\u064f'},)


@pytest.mark.parametrize('spoken', [
    'أَنْعَمْتُ عَلَيْهِمْ', 'أَنْعَمْتُ،عَلَيْهِمْ',
    'أَنْعَمْ،تُ', 'أَنْعَمْتُ1', 'xأَنْعَمْتُ', '\u0651أَنْعَمْتُ',
])
def test_multiword_and_malformed_raw_evidence_abstains(spoken):
    result = compare_harakat('أَنْعَمْتَ', spoken, is_stream_end=True)
    assert not result.mismatch
    assert result.inconclusive
    assert result.compared_positions == ()


def test_nonword_input_and_empty_marks_abstain():
    for expected, spoken in [('', ''), ('قُلْ', ''), ('قُلْ', 'قل'), ('١', '١')]:
        result = compare_harakat(expected, spoken)
        assert not result.mismatch
        assert result.inconclusive
