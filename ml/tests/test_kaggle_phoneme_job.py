"""The remote job must preserve audio identity, real frames and honest results."""
import hashlib
import json

import numpy as np
import pytest


def test_encoder_manifest_rejects_changed_weights_and_unexpected_files(tmp_path):
    from ml.training.kaggle_phoneme_job import verify_encoder
    names = ['model.bin', 'config.json', 'tokenizer.json', 'vocabulary.json', 'preprocessor_config.json']
    for name in names:
        (tmp_path/name).write_bytes(name.encode())
    hashes = {name: hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() for name in names}
    (tmp_path/'encoder-manifest.json').write_text(json.dumps({'files': hashes}))
    assert verify_encoder(tmp_path, expected_model_sha=hashes['model.bin']) == hashes
    (tmp_path/'.env').write_text('private-placeholder')
    with pytest.raises(ValueError):
        verify_encoder(tmp_path, expected_model_sha=hashes['model.bin'])
    (tmp_path/'.env').unlink();(tmp_path/'model.bin').write_bytes(b'changed')
    with pytest.raises(ValueError):
        verify_encoder(tmp_path, expected_model_sha=hashes['model.bin'])


def test_encoder_batch_uses_audio_only_and_keeps_real_short_clip_frames():
    from ml.training.kaggle_phoneme_job import extract_batch
    calls = []
    def frontend(audio):
        calls.append(len(audio));return np.ones((80, 3500), np.float32)
    def encoder(mel):
        assert mel.shape == (2, 80, 3000)
        return np.ones((2, 1500, 512), np.float32)
    outputs = extract_batch(frontend, encoder, [np.ones(4001, np.float32), np.ones(16000, np.float32)])
    assert calls == [4001, 16000]
    assert [x.shape for x in outputs] == [(13, 512), (50, 512)]
    assert all(x.dtype == np.float16 for x in outputs)


@pytest.mark.parametrize('audio', [np.ones(1), np.ones(12*16000+1),
                                 np.full(16000, np.nan), np.ones((2, 16000))])
def test_encoder_batch_rejects_invalid_audio_before_any_encode(audio):
    from ml.training.kaggle_phoneme_job import extract_batch
    def unexpected(*args):
        raise AssertionError('Invalid audio reached encoder')
    with pytest.raises(ValueError):
        extract_batch(unexpected, unexpected, [audio])


def test_float16_overflow_cannot_be_cached_as_acoustic_features():
    from ml.training.kaggle_phoneme_job import extract_batch
    with pytest.raises(ValueError):
        extract_batch(lambda audio: np.zeros((80, 3000), np.float32),
                      lambda mel: np.full((1, 1500, 512), 1e10, np.float32),
                      [np.ones(16000, np.float32)])


def feature_manifest(tmp_path, *, unknown=False):
    from ml.training.phoneme_gpu import source_role, reference_group
    rows = []
    for index, voice in enumerate(['Amer', 'Nabil', 'Jessica']):
        role = 'validation' if voice == 'Jessica' else 'train'
        for attempt in range(1000):
            row = {'speaker': voice, 'sentence_ref': f'reference {index} {attempt}',
                   'label': 'augmented', 'sentence_aug': 'altered', 'phoneme_mis': 'k u'}
            if source_role(row) == role: break
        if unknown and role == 'validation': row['phoneme_mis'] = 'z z'
        features = np.random.default_rng(index).standard_normal((24, 512)).astype(np.float16)
        path = tmp_path/f'{index}.npz';np.savez_compressed(path, features=features)
        rows.append(row | {'id': str(index), 'role': role, 'reference_group': reference_group(row['sentence_ref']),
                           'sample_count': 24*320, 'float_pcm_sha256': hashlib.sha256(str(index).encode()).hexdigest(),
                           'feature_path': str(path)})
    return {'label_type': 'synthetic_altered_phones', 'dataset': 'unit-public-source',
            'revision': 'unit-revision', 'feature_bundle_sha256': 'a'*64, 'cases': rows}


def test_temporal_training_saves_best_checkpoint_and_remains_unqualified(tmp_path):
    import torch
    from ml.training.kaggle_phoneme_job import train_features
    manifest = feature_manifest(tmp_path, unknown=True)
    report = train_features(manifest, tmp_path/'out', epochs=3, device='cpu')
    assert report['qualified'] is False and report['production_changed'] is False
    assert report['training_clips'] == 2 and report['validation_clips'] == 1
    assert report['unknown_validation_phones'] == ['z']
    assert report['best_validation_per'] >= 1
    assert report['history'][-1]['validation_loss'] is None
    checkpoint = torch.load(tmp_path/'out/candidate-head.pt', map_location='cpu', weights_only=True)
    assert checkpoint['epoch'] == report['best_epoch']
    assert checkpoint['validation_per'] == report['best_validation_per']
    assert hashlib.sha256((tmp_path/'out/candidate-head.pt').read_bytes()).hexdigest() == report['head_sha256']
    assert all(np.isfinite(row['training_loss']) for row in report['history'])


def test_training_validation_pcm_overlap_is_rejected_before_training(tmp_path):
    from ml.training.kaggle_phoneme_job import train_features
    manifest = feature_manifest(tmp_path)
    manifest['cases'][-1]['float_pcm_sha256'] = manifest['cases'][0]['float_pcm_sha256']
    with pytest.raises(ValueError, match='overlap'):
        train_features(manifest, tmp_path/'out', epochs=1, device='cpu')


def test_cached_feature_frame_count_must_match_original_audio(tmp_path):
    from ml.training.kaggle_phoneme_job import train_features
    manifest = feature_manifest(tmp_path);manifest['cases'][0]['sample_count'] = 16000
    with pytest.raises(ValueError, match='frame'):
        train_features(manifest, tmp_path/'out', epochs=1, device='cpu')


def test_public_audio_preparation_preserves_voice_caps_actual_targets_and_hashes(tmp_path):
    import io
    import wave
    from ml.training.phoneme_gpu import source_role
    from ml.training.kaggle_phoneme_job import prepare_features
    rows = []
    for index, voice in enumerate(['Amer']*3 + ['Nabil']*3 + ['Jessica']*3):
        role = 'validation' if voice == 'Jessica' else 'train'
        for attempt in range(1000):
            row = {'speaker': voice, 'sentence_ref': f'content {index} {attempt}',
                   'label': 'augmented', 'sentence_aug': 'changed', 'phoneme_mis': 'k a'}
            if source_role(row) == role: break
        stream = io.BytesIO()
        pcm = (np.sin(np.arange(8000)*(.02+index*.001))*12000).astype('<i2').tobytes()
        with wave.open(stream, 'wb') as wav:
            wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'));wav.writeframes(pcm)
        rows.append(row | {'audio': {'bytes': stream.getvalue()}})
    def encoder(mel): return np.zeros((len(mel), 1500, 512), np.float32)
    manifest = prepare_features(rows, lambda audio: np.zeros((80, 3000), np.float32), encoder,
                                tmp_path/'cache', tmp_path/'out', {'feature_bundle_sha256': 'a'*64},
                                max_train=4, min_train=4, max_validation=2, per_voice=2, device='cpu')
    assert len(manifest['cases']) == 6
    train = [r for r in manifest['cases'] if r['role'] == 'train']
    held = [r for r in manifest['cases'] if r['role'] == 'validation']
    assert sorted(r['speaker'] for r in train) == ['Amer', 'Amer', 'Nabil', 'Nabil']
    assert {r['speaker'] for r in held} == {'Jessica'}
    assert all(r['phoneme_mis'] == 'k a' and r['sample_count'] == 8000 for r in manifest['cases'])
    assert len({r['float_pcm_sha256'] for r in manifest['cases']}) == 6
    assert (tmp_path/'out/source-manifest.json').exists()


def test_training_precision_is_independent_of_ambient_autocast(tmp_path):
    """The small CTC head must not inherit reduced precision from its caller."""
    import torch
    from ml.training.kaggle_phoneme_job import train_features
    manifest=feature_manifest(tmp_path)
    with torch.autocast('cpu',dtype=torch.bfloat16):
        ambient=train_features(manifest,tmp_path/'ambient',epochs=1,device='cpu')
    plain=train_features(manifest,tmp_path/'plain',epochs=1,device='cpu')
    assert ambient['history']==plain['history']
    left=torch.load(tmp_path/'ambient/candidate-head.pt',map_location='cpu',weights_only=True)
    right=torch.load(tmp_path/'plain/candidate-head.pt',map_location='cpu',weights_only=True)
    assert all(torch.equal(left['state_dict'][key],value)for key,value in right['state_dict'].items())
