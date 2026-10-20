import copy
import math

import pytest

from ml.training.human_word_data import parse_label_row
from ml.training.local_vowel_data import (
    local_word_crops, unique_exact_matches, vowel_word_labels,
)


def source(**changes):
    row = dict(file_name='data/ID45V1T.wav', label='1', label_name='correct',
               verse_number='1', verse_text='قُلْ هُوَ اللَّهُ أَحَدٌ',
               error_location='', error_type='', error_explanation='')
    return parse_label_row({**row, **changes}, set())


def test_correct_utterance_labels_only_its_own_words_negative():
    rows = vowel_word_labels(source())
    assert [r['word_index'] for r in rows] == [0, 1, 2, 3]
    assert [r['target'] for r in rows] == [0, 0, 0, 0]


def test_parallel_mixed_types_keep_tajweed_and_unlisted_words_unknown():
    rows = vowel_word_labels(source(file_name='data/ID45V1F.wav', label='0', label_name='error',
                                   error_location='قُلْ, أَحَدٌ', error_type='حركات, تجويد'))
    assert [r['target'] for r in rows] == [1, None, None, None]


def test_ambiguous_category_location_cardinality_stays_unknown():
    rows = vowel_word_labels(source(file_name='data/ID45V1F.wav', label='0', label_name='error',
                                   error_location='قُلْ, أَحَدٌ', error_type='حركات'))
    assert [r['target'] for r in rows] == [None] * 4


def test_tajweed_only_error_does_not_become_a_vowel_negative():
    rows = vowel_word_labels(source(file_name='data/ID45V1F.wav', label='0', label_name='error',
                                   error_location='أَحَدٌ', error_type='تجويد'))
    assert [r['target'] for r in rows] == [None] * 4


def test_original_word_mapping_survives_qps_assimilation_in_yakun_lahu():
    rows = vowel_word_labels(source(file_name='data/ID45V4F.wav', label='0', label_name='error',
                                   verse_number='4', verse_text='وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ',
                                   error_location='كُفُوًا', error_type='حركات وتجويد'))
    assert [r['target'] for r in rows] == [None, None, None, 1, None]


def test_unknown_category_cannot_gain_vowel_supervision_from_a_substring():
    row = source(file_name='data/ID45V1F.wav', label='0', label_name='error',
                 error_location='قُلْ', error_type='حركات')
    row['source_error_type'] = 'لا توجد حركات'
    assert all(r['target'] is None for r in vowel_word_labels(row))


@pytest.mark.parametrize('expected,actual,want', [
    ([1, 2, 1], [1, 2, 1], {0: 0, 1: 1, 2: 2}),
    ([1, 1], [1], {}),
    ([1, 2], [1, 3], {0: 0}),
    ([1, 2], [1, 3, 2], {0: 0, 1: 2}),
    ([1, 2, 1], [1], {}),
])
def test_only_matches_shared_by_every_optimal_alignment_become_anchors(expected, actual, want):
    assert unique_exact_matches(expected, actual) == want


def phonemes():
    return [dict(id=token, start_frame=start, end_frame=end, confidence=.9)
            for token, start, end in [(21, 1, 3), (33, 3, 4), (23, 4, 6),
                                      (26, 10, 12), (33, 12, 13), (27, 13, 15)]]


def test_word_crops_follow_native_consonants_and_include_actual_word_ending():
    rows = local_word_crops([21, 33, 23, 26, 33, 27], [0, 0, 0, 1, 1, 1], phonemes(), 20)
    assert [(r['word_index'], r['frame_start'], r['frame_end']) for r in rows] == [(0, 1, 10), (1, 10, 20)]
    assert all(r['available'] for r in rows)
    assert rows[0]['reference_ids'] == [21, 33, 23]


def test_low_confidence_anchor_leaves_that_word_unassessed():
    emissions = phonemes(); emissions[0]['confidence'] = .54
    rows = local_word_crops([21, 33, 23, 26, 33, 27], [0, 0, 0, 1, 1, 1], emissions, 20)
    assert rows[0]['available'] is False and rows[0]['reason'] == 'low_native_confidence'
    assert rows[1]['available'] is True


def test_inserted_consonant_inside_word_does_not_become_a_correct_reference_crop():
    emissions = [dict(id=t, start_frame=i*3, end_frame=i*3+2, confidence=.99)
                 for i, t in enumerate([21, 8, 23])]
    rows = local_word_crops([21, 33, 23], [0, 0, 0], emissions, 12)
    assert rows[0]['available'] is False and rows[0]['reason'] == 'noncontiguous_native_consonants'


def test_ambiguous_repeated_anchor_does_not_select_an_arbitrary_word_occurrence():
    rows = local_word_crops([23, 23], [0, 1],
                           [dict(id=23, start_frame=1, end_frame=4, confidence=.99)], 10)
    assert len(rows) == 2 and all(r['available'] is False for r in rows)


@pytest.mark.parametrize('change', [{'confidence': math.nan}, {'id': 99}, {'end_frame': 1000}])
def test_malformed_native_records_stop_before_feature_cache(change):
    emissions = copy.deepcopy(phonemes()); emissions[0].update(change)
    with pytest.raises(ValueError):
        local_word_crops([21, 33, 23, 26, 33, 27], [0, 0, 0, 1, 1, 1], emissions, 20)
