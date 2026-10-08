import json
import shutil
import wave
from pathlib import Path

import pytest


def _audio(root, name, value=1000, *, seconds=1):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(value.to_bytes(2, 'little', signed=True) * int(16000 * seconds))
    return name


def _write(root, train, evaluation):
    for name, rows in [('train_manifest.jsonl', train), ('eval_manifest.jsonl', evaluation)]:
        (root / name).write_text(''.join(json.dumps(r) + '\n' for r in rows))


def _row(path, speaker, **extra):
    return {'audio_path': path, 'text': 'بِسْمِ اللَّهِ', 'speaker_id': speaker,
            'source': 'retasy_correct', 'augmentation': 'clean', **extra}


def test_pilot_caps_augmentations_by_clean_audio_lineage(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    train = [_row(_audio(tmp_path, 'clean.wav'), 'train', parent_audio_path='original')]
    for i in range(8):
        train.append(_row(_audio(tmp_path, f'aug{i}.wav', 1100 + i), 'train',
                          source='retasy_phase3_aug', augmentation=['noise'],
                          parent_audio_path='original'))
    _write(tmp_path, train, [_row(_audio(tmp_path, 'eval.wav', 2000), 'eval')])
    report = prepare_pilot_data(tmp_path, tmp_path / 'prepared')
    assert report['train_rows'] == 2
    assert report['excluded_augmentations'] == 7
    assert report['eval_rows'] == 1


def test_pilot_rejects_speaker_leakage(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path, [_row(_audio(tmp_path, 'train.wav'), 'same')],
           [_row(_audio(tmp_path, 'eval.wav', 2000), 'same')])
    with pytest.raises(ValueError, match='speaker'):
        prepare_pilot_data(tmp_path, tmp_path / 'prepared')


def test_expected_verse_cannot_substitute_for_spoken_training_transcript(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    row = _row(_audio(tmp_path, 'train.wav'), 'train', text='', expected_text='بسم الله')
    _write(tmp_path, [row], [_row(_audio(tmp_path, 'eval.wav', 2000), 'eval')])
    with pytest.raises(ValueError, match='transcript'):
        prepare_pilot_data(tmp_path, tmp_path / 'prepared')


def test_pilot_rejects_audio_outside_dataset(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    root = tmp_path / 'dataset'
    root.mkdir()
    _audio(tmp_path, 'outside.wav')
    _write(root, [_row('../outside.wav', 'train')],
           [_row(_audio(root, 'eval.wav', 2000), 'eval')])
    with pytest.raises(ValueError, match='outside'):
        prepare_pilot_data(root, root / 'prepared')


def test_pilot_rejects_same_audio_in_train_and_eval(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _audio(tmp_path, 'train.wav')
    shutil.copyfile(tmp_path / 'train.wav', tmp_path / 'eval.wav')
    _write(tmp_path, [_row('train.wav', 'train')], [_row('eval.wav', 'eval')])
    with pytest.raises(ValueError, match='duplicate'):
        prepare_pilot_data(tmp_path, tmp_path / 'prepared')


def test_namespaced_unknown_evaluation_speaker_is_rejected(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path, [_row(_audio(tmp_path, 'train.wav'), 'train')],
           [_row(_audio(tmp_path, 'eval.wav', 2000), 'tlog:unknown')])
    with pytest.raises(ValueError, match='known speaker'):
        prepare_pilot_data(tmp_path, tmp_path / 'prepared')


def test_unknown_training_speakers_are_reported_without_disjoint_claim(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path, [_row(_audio(tmp_path, 'train.wav'), 'tlog:unknown')],
           [_row(_audio(tmp_path, 'eval.wav', 2000), 'eval')])
    report = prepare_pilot_data(tmp_path, tmp_path / 'prepared')
    assert report['unknown_train_speaker_rows'] == 1
    assert report['full_speaker_disjoint_verified'] is False


def test_overlong_training_audio_is_excluded_and_audited_without_truncation(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    valid = _audio(tmp_path, 'valid.wav')
    overlong = _audio(tmp_path, 'overlong.wav', 1100, seconds=30.16)
    original = (tmp_path / overlong).read_bytes()
    _write(tmp_path, [_row(valid, 'train'), _row(overlong, 'train')],
           [_row(_audio(tmp_path, 'eval.wav', 2000), 'eval')])
    report = prepare_pilot_data(tmp_path, tmp_path / 'prepared')
    rows = [json.loads(line) for line in
            (tmp_path / 'prepared/train_manifest.jsonl').read_text().splitlines()]
    assert [Path(row['audio_path']).name for row in rows] == ['valid.wav']
    assert report['excluded_training_duration_rows'] == 1
    assert report['training_duration_exclusions'][0]['audio_path'] == 'overlong.wav'
    assert report['training_duration_exclusions'][0]['duration_seconds'] == 30.16
    assert (tmp_path / overlong).read_bytes() == original


def test_overlong_evaluation_audio_is_rejected_without_changing_holdout(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path, [_row(_audio(tmp_path, 'train.wav'), 'train')],
           [_row(_audio(tmp_path, 'eval.wav', 2000, seconds=30.16), 'eval')])
    with pytest.raises(ValueError, match='Unsupported audio duration'):
        prepare_pilot_data(tmp_path, tmp_path / 'prepared')


def test_filtering_every_training_clip_still_rejects_empty_training(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path, [_row(_audio(tmp_path, 'train.wav', seconds=30.16), 'train')],
           [_row(_audio(tmp_path, 'eval.wav', 2000), 'eval')])
    with pytest.raises(ValueError, match='Empty manifest'):
        prepare_pilot_data(tmp_path, tmp_path / 'prepared')


def test_silent_training_audio_is_excluded_and_audited(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path, [_row(_audio(tmp_path, 'valid.wav'), 'train'),
                      _row(_audio(tmp_path, 'silent.wav', 0), 'train')],
           [_row(_audio(tmp_path, 'eval.wav', 2000), 'eval')])
    report = prepare_pilot_data(tmp_path, tmp_path / 'prepared')
    assert report['train_rows'] == 1
    assert report['excluded_training_quality_rows'] == 1
    assert report['training_quality_exclusions'][0]['audio_path'] == 'silent.wav'
    assert report['training_quality_exclusions'][0]['reason'] == 'silent_audio'


def test_silent_evaluation_audio_still_fails_closed(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path, [_row(_audio(tmp_path, 'train.wav'), 'train')],
           [_row(_audio(tmp_path, 'eval.wav', 0), 'eval')])
    with pytest.raises(ValueError, match='Silent/non-finite'):
        prepare_pilot_data(tmp_path, tmp_path / 'prepared')


def test_noisy_augmentation_of_silent_origin_cannot_become_speech_training(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path, [
        _row(_audio(tmp_path, 'valid.wav'), 'train'),
        _row(_audio(tmp_path, 'silent.wav', 0), 'train',
             source='tlog_clean_bucket', clip_id='bad-origin'),
        _row(_audio(tmp_path, 'noise.wav', 1500), 'train',
             source='tlog_phase3_aug', clip_id='bad-origin', augmentation=['noise']),
    ], [_row(_audio(tmp_path, 'eval.wav', 2000), 'eval')])
    report = prepare_pilot_data(tmp_path, tmp_path / 'prepared')
    assert report['train_rows'] == 1
    assert report['excluded_invalid_origin_augmentations'] == 1
    assert report['training_quality_exclusions'][-1]['reason'] == 'augmentation_of_unusable_origin'


def test_overlong_augmentation_does_not_discard_its_valid_clean_origin(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path, [
        _row(_audio(tmp_path, 'valid.wav'), 'train',
             source='tlog_clean_bucket', clip_id='good-origin'),
        _row(_audio(tmp_path, 'long-aug.wav', 1500, seconds=30.16), 'train',
             source='tlog_phase3_aug', clip_id='good-origin', augmentation=['noise']),
    ], [_row(_audio(tmp_path, 'eval.wav', 2000), 'eval')])
    report = prepare_pilot_data(tmp_path, tmp_path / 'prepared')
    assert report['train_rows'] == 1
    assert report['excluded_invalid_origin_augmentations'] == 0
