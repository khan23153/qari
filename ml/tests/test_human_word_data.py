import pytest

from ml.training.human_word_data import parse_label_row, select_threshold


def row(**changes):
    value = dict(file_name='data/ID45V1T.wav', label='1', label_name='correct',
                 verse_number='1', verse_text='قُلْ هُوَ اللَّهُ أَحَدٌ',
                 error_location='', error_type='', error_explanation='')
    return {**value, **changes}


def test_correct_utterance_only_labels_its_own_words():
    parsed = parse_label_row(row(), set())
    assert parsed['targets'] == [0] * 15
    assert parsed['mask'] == [1, 1, 1, 1] + [0] * 11


def test_error_does_not_turn_unlisted_words_into_negatives():
    parsed = parse_label_row(row(file_name='data/ID45V1F.wav', label='0', label_name='error',
                                 error_location='قُلْ', error_type='حركات'), set())
    assert parsed['targets'] == [1] + [0] * 14
    assert parsed['mask'] == [1] + [0] * 14


@pytest.mark.parametrize('changes', [
    {'file_name': 'data/ID45V1F.wav'}, {'label': '0'},
    {'verse_text': 'اللَّهُ الصَّمَدُ'}, {'file_name': '../../private.wav'},
    {'error_type': 'حركات'},
])
def test_quarantines_conflicting_labels_and_provenance(changes):
    with pytest.raises(ValueError):
        parse_label_row(row(**changes), set())


def test_error_location_must_map_without_ambiguous_repetition():
    with pytest.raises(ValueError, match='ambiguous'):
        parse_label_row(row(file_name='data/ID45V3F.wav', label='0', label_name='error',
                            verse_number='3', verse_text='لَمْ يَلِدْ وَلَمْ يُولَدْ',
                            error_location='لَمْ', error_type='تجويد'), set())


def test_uthmani_location_and_multiple_explicit_targets():
    parsed = parse_label_row(row(file_name='data/ID45V2F.wav', label='0', label_name='error',
                                 verse_number='2', verse_text='اللَّهُ الصَّمَدُ',
                                 error_location='ٱللَّهُ، ٱلصَّمَدُ', error_type='حركات, تجويد'), set())
    assert parsed['targets'] == [0] * 4 + [1, 1] + [0] * 9
    assert parsed['mask'] == [0] * 4 + [1, 1] + [0] * 9


def test_all_clips_from_a_participant_keep_one_role_and_probes_stay_reserved():
    original = parse_label_row(row(), set())
    other = parse_label_row(row(file_name='data/ID45V2T.wav', verse_number='2',
                               verse_text='اللَّهُ الصَّمَدُ'), set())
    assert original['role'] == other['role']
    assert parse_label_row(row(), {'45'})['role'] == 'reserved'


def test_conservative_threshold_uses_validation_labels():
    records = [{'role': 'validation', 'score': p, 'target': t}
               for p, t in [(.1, 0), (.6, 0), (.7, 1), (.9, 1)]]
    assert select_threshold(records) == .7
    tied = [{'role': 'validation', 'score': .9, 'target': t} for t in [0, 1]]
    assert select_threshold(tied) > 1.


def test_threshold_cannot_consume_test_scores_or_unknown_labels():
    base = [{'role': 'validation', 'score': .2, 'target': 0},
            {'role': 'validation', 'score': .8, 'target': 1}]
    for extra in [{'role': 'test', 'score': .1, 'target': 1},
                  {'role': 'reserved', 'score': .1, 'target': 1},
                  {'role': 'validation', 'score': float('nan'), 'target': 1},
                  {'role': 'validation', 'score': .5, 'target': -1}]:
        with pytest.raises(ValueError):
            select_threshold(base + [extra])
