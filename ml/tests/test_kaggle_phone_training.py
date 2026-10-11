import json
import shutil
import wave
from pathlib import Path

import pytest


def _audio(root, name, value=1000):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(value.to_bytes(2, 'little', signed=True) * 16000)
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


def test_filename_inferred_tlog_labels_and_their_augmentations_are_quarantined(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    clean = _row(_audio(tmp_path, 'verified.wav'), 'train')
    tlog = _row(_audio(tmp_path, '14_22.wav', 1200), 'tlog:unknown',
                source='tlog_clean_bucket', text='وقال الشيطان', is_clean=True,
                label_verified=True, clip_id='wrong_verse')
    aug = _row(_audio(tmp_path, 'aug.wav', 1300), 'tlog:unknown',
               source='tlog_phase3_aug', text='وقال الشيطان', clip_id='wrong_verse')
    _write(tmp_path, [clean, tlog, aug], [_row(_audio(tmp_path, 'eval.wav', 2000), 'eval')])
    original = (tmp_path / 'train_manifest.jsonl').read_bytes()
    out = tmp_path / 'prepared'
    report = prepare_pilot_data(tmp_path, out)
    kept = [json.loads(l)for l in (out/'train_manifest.jsonl').read_text().splitlines()]
    assert [Path(r['audio_path']).name for r in kept] == ['verified.wav']
    assert report['quarantined_training_rows'] == 2
    assert report['input_train_rows'] == 3
    quarantined = [json.loads(l)for l in (out/'quarantined_train_manifest.jsonl').read_text().splitlines()]
    assert [r['source']for r in quarantined] == ['tlog_clean_bucket','tlog_phase3_aug']
    assert all(r['quarantine_reason']for r in quarantined)
    assert (tmp_path/'train_manifest.jsonl').read_bytes() == original


def test_augmentation_cannot_wash_a_filename_label_by_changing_its_source(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    original = _row(_audio(tmp_path,'tlog.wav',1100),'train',source='tlog_clean_bucket',
                    parent_audio_path='suspect_original')
    disguised = _row(_audio(tmp_path,'aug.wav',1200),'train',source='retasy_phase3_aug',
                     parent_audio_path='suspect_original')
    _write(tmp_path,[original,disguised,_row(_audio(tmp_path,'good.wav'),'train')],
           [_row(_audio(tmp_path,'eval.wav',2000),'eval')])
    report = prepare_pilot_data(tmp_path,tmp_path/'prepared')
    assert report['train_rows'] == 1
    assert report['quarantined_training_rows'] == 2


def test_filename_labels_in_evaluation_are_rejected_without_silent_exclusion(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path,[_row(_audio(tmp_path,'train.wav'),'train')],
           [_row(_audio(tmp_path,'eval.wav',2000),'eval',source='tlog_clean_bucket')])
    with pytest.raises(ValueError,match='(?i)(label|tlog)'):
        prepare_pilot_data(tmp_path,tmp_path/'prepared')


def test_quarantine_of_all_training_labels_prevents_training(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    _write(tmp_path,[_row(_audio(tmp_path,'train.wav'),'train',source='tlog_clean_bucket')],
           [_row(_audio(tmp_path,'eval.wav',2000),'eval')])
    with pytest.raises(ValueError,match='(?i)(verified|label|training)'):
        prepare_pilot_data(tmp_path,tmp_path/'prepared')
    assert not (tmp_path/'prepared/train_manifest.jsonl').exists()


def test_retagged_evaluation_descendant_of_quarantined_label_is_rejected(tmp_path):
    from ml.training.kaggle_phone_training import prepare_pilot_data
    bad = _row(_audio(tmp_path,'bad.wav',1100),'train',source='tlog_clean_bucket',
               parent_audio_path='bad_original')
    good = _row(_audio(tmp_path,'good.wav'),'train')
    evaluation = _row(_audio(tmp_path,'eval.wav',2000),'eval',
                      parent_audio_path='bad_original')
    _write(tmp_path,[bad,good],[evaluation])
    with pytest.raises(ValueError,match='(?i)(label|lineage)'):
        prepare_pilot_data(tmp_path,tmp_path/'prepared')
