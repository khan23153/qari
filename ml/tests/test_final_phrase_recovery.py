"""Final recovery corroborates one bounded position without consuming a mistake."""
import pytest
from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus

PHRASE = ['alpha', 'beta', 'gamma', 'epsilon']


def matched(matcher, words, scores):
    return [s.index for s in matcher.finalize(words, scores)
            if s.status == WordStatus.MATCHED]


def make(reference, **kwargs):
    return StreamingMatcher(reference, known_error_words=set(reference + PHRASE), **kwargs)


def test_unique_native_phrase_recovers_only_after_ordinary_alignment_stalls():
    reference = ['root'] + [f'miss{i}' for i in range(7)] + PHRASE + ['tail']
    assert matched(make(reference), ['root'] + PHRASE, [.9] * 5) == [0, 8, 9, 10, 11]


def test_current_substitution_and_its_adjacent_continuation_take_precedence():
    reference = ['root', 'delta', 'beta', 'gamma', 'epsilon'] + PHRASE + ['tail']
    m = make(reference)
    states = m.finalize(['root'] + PHRASE, [.9] * 5)
    assert [s.index for s in states if s.status == WordStatus.MATCHED] == [0, 2, 3, 4]
    assert states[1].status == WordStatus.ERROR
    assert states[1].spoken == 'alpha'


def test_first_target_outside_existing_eight_word_ceiling_cannot_recover():
    reference = ['root'] + [f'miss{i}' for i in range(8)] + PHRASE
    assert matched(make(reference), ['root'] + PHRASE, [.9] * 5) == [0]


@pytest.mark.parametrize('score', [.2, float('nan'), float('inf'), 1.01])
def test_four_word_corroboration_cannot_borrow_one_weak_or_invalid_token(score):
    reference = ['root'] + [f'miss{i}' for i in range(7)] + PHRASE
    assert matched(make(reference), ['root'] + PHRASE, [.9, .9, .9, score, .9]) == [0]


def test_phrase_repeated_before_the_opening_slice_is_still_ambiguous():
    reference = PHRASE + ['root'] + [f'miss{i}' for i in range(7)] + PHRASE
    m = make(reference)
    m.reference = reference[4:]
    m._final_reference_offset = 4
    assert matched(m, ['root'] + PHRASE, [.9] * 5) == [0]


def test_corpus_alias_in_earlier_phrase_also_counts_as_ambiguity():
    reference = ['alternate', 'beta', 'gamma', 'epsilon', 'root'] + [f'miss{i}' for i in range(7)] + PHRASE
    m = make(reference, word_aliases={'alternate': 'alpha'})
    m.reference = reference[4:]
    m._final_reference_offset = 4
    assert matched(m, ['root'] + PHRASE, [.9] * 5) == [0]


def test_ayah_ceiling_uses_original_coordinates_after_opening_slice():
    reference = [f'intro{i}' for i in range(5)] + ['root'] + [f'miss{i}' for i in range(5)] + PHRASE + [f'tail{i}' for i in range(6)]
    boundaries = [{'word_index_end': 5, 'word_count': 6},
                  {'word_index_end': 9, 'word_count': 4},
                  {'word_index_end': 10, 'word_count': 1},
                  {'word_index_end': 20, 'word_count': 10}]
    m = make(reference, ayah_boundaries=boundaries)
    m.reference = reference[5:]
    m._final_reference_offset = 5
    assert matched(m, ['root'] + PHRASE, [.9] * 5) == [0]


def test_budget_truncation_cannot_borrow_a_phrase_from_unreachable_reference():
    reference = ['root'] + [f'miss{i}' for i in range(7)] + PHRASE
    m = make(reference)
    m.reference = reference[:10]
    assert matched(m, ['root'] + PHRASE, [.9] * 5) == [0]
