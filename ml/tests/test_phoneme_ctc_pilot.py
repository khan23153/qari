"""Training targets must reflect altered audio; canonical words are not truth."""
import pytest
import numpy as np
from types import SimpleNamespace


def frontend(**changes):
    values = dict(sampling_rate=16000, hop_length=160, n_fft=400, chunk_length=30,
                  n_samples=480000, nb_max_frames=3000, mel_filters=np.zeros((80, 201)))
    values.update(changes)
    return SimpleNamespace(**values)


def test_feature_identity_includes_frontend_config_bytes_and_presence(tmp_path):
    from ml.training.phoneme_ctc_pilot import feature_identity
    (tmp_path/'model.bin').write_bytes(b'encoder')
    (tmp_path/'config.json').write_text('{}')
    original = feature_identity(tmp_path, frontend(), frontend_source=__file__)
    path = tmp_path/'preprocessor_config.json'
    path.write_text('{"hop_length":160}')
    present = feature_identity(tmp_path, frontend(), frontend_source=__file__)
    path.write_text('{"hop_length":160,"n_fft":400}')
    changed = feature_identity(tmp_path, frontend(), frontend_source=__file__)
    assert len({r['feature_bundle_sha256'] for r in (original, present, changed)}) == 3
    assert original['preprocessor_config_sha256'] is None
    assert present['preprocessor_config_sha256'] != changed['preprocessor_config_sha256']


@pytest.mark.parametrize('change', [{'sampling_rate': 8000}, {'hop_length': 320},
                                    {'mel_filters': np.zeros((128, 201))}, {'n_fft': 512}])
def test_feature_identity_rejects_incompatible_frontend(tmp_path, change):
    from ml.training.phoneme_ctc_pilot import feature_identity
    with pytest.raises(ValueError, match='frontend'):
        feature_identity(tmp_path, frontend(**change))


def test_pcm_frame_limit_checked_before_audio_allocation(monkeypatch):
    import wave
    from ml.training.phoneme_ctc_pilot import read_pcm16_bounded
    class Oversized:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def getframerate(self): return 16000
        def getnchannels(self): return 1
        def getsampwidth(self): return 2
        def getnframes(self): return 16000 * 60 * 60
        def readframes(self, count): raise AssertionError('Oversized audio was allocated')
    monkeypatch.setattr(wave, 'open', lambda *args: Oversized())
    with pytest.raises(ValueError, match='bounded'):
        read_pcm16_bounded('oversized.wav')


def row(speaker='voice-a', sentence='reference', phones='k u f w a n'):
    return {'speaker': speaker, 'sentence_ref': sentence, 'sentence_aug': 'altered',
            'label': 'augmented', 'phoneme_ref': 'k u f u w a n', 'phoneme_mis': phones}


def test_actual_altered_phones_are_used_without_canonical_fallback():
    from ml.training.phoneme_ctc_pilot import altered_targets
    assert altered_targets(row()) == ('k', 'u', 'f', 'w', 'a', 'n')
    assert altered_targets(row(phones='<sil> D AA r <sil>')) == ('D', 'AA', 'r')


@pytest.mark.parametrize('change', [{'phoneme_mis': ''}, {'phoneme_mis': None},
                                    {'label': 'original'}, {'sentence_aug': ''}])
def test_ambiguous_or_missing_actual_phone_targets_are_rejected(change):
    from ml.training.phoneme_ctc_pilot import altered_targets
    case = row();case.update(change)
    with pytest.raises(ValueError):
        altered_targets(case)


def test_held_voice_and_its_reference_sentences_are_excluded_from_training():
    from ml.training.phoneme_ctc_pilot import split_voices
    cases = [row('a', 'first'), row('b', 'overlap'), row('held', 'overlap'), row('held', 'last')]
    train, validation = split_voices(cases, 'held')
    assert [r['sentence_ref'] for r in train] == ['first']
    assert {r['speaker'] for r in validation} == {'held'}
    assert not {r['sentence_ref'] for r in train} & {r['sentence_ref'] for r in validation}


@pytest.mark.parametrize('cases', [[row('a')], [row('held')], [row('a'), row('held')]])
def test_empty_or_fully_leaked_splits_are_rejected(cases):
    from ml.training.phoneme_ctc_pilot import split_voices
    with pytest.raises(ValueError):
        split_voices(cases, 'held')


def test_repeated_ctc_targets_need_a_blank_separation_frame():
    from ml.training.phoneme_ctc_pilot import validate_ctc_frames
    validate_ctc_frames(('a', 'a'), 3)
    with pytest.raises(ValueError):
        validate_ctc_frames(('a', 'a'), 2)
    with pytest.raises(ValueError):
        validate_ctc_frames((), 3)


def test_encoder_padding_is_excluded_from_short_audio_features():
    from ml.training.phoneme_ctc_pilot import crop_encoder_frames
    encoded = np.ones((1, 1500, 512), dtype=np.float32)
    assert crop_encoder_frames(encoded, 64640).shape == (202, 512)
    assert crop_encoder_frames(encoded, 64641).shape == (203, 512)


@pytest.mark.parametrize('shape,samples', [((1, 1500, 384), 16000), ((2, 1500, 512), 16000),
                                          ((1, 2, 512), 16000), ((1, 1500, 512), 0)])
def test_invalid_or_truncated_encoder_features_are_rejected(shape, samples):
    from ml.training.phoneme_ctc_pilot import crop_encoder_frames
    with pytest.raises(ValueError):
        crop_encoder_frames(np.zeros(shape, np.float32), samples)


def test_nonfinite_features_are_rejected():
    from ml.training.phoneme_ctc_pilot import crop_encoder_frames
    features = np.zeros((1, 1500, 512), np.float32);features[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        crop_encoder_frames(features, 16000)


def test_greedy_ctc_keeps_a_repeated_phone_only_after_a_blank():
    from ml.training.phoneme_ctc_pilot import greedy_phones, phoneme_distance
    assert greedy_phones([1, 1, 0, 1, 2, 2, 0], ['<blank>', 'a', 'aa']) == ('a', 'a', 'aa')
    assert phoneme_distance(('k', 'u', 'f', 'u'), ('k', 'u', 'f')) == 1


def test_cpu_pilot_uses_only_encoder_and_never_qualifies_synthetic_training(tmp_path, monkeypatch):
    import hashlib
    import json
    import os
    import struct
    import wave
    import torch
    import sys
    from ml.training.phoneme_ctc_pilot import run_pilot

    encoder = tmp_path / 'encoder';encoder.mkdir()
    (encoder / 'model.bin').write_bytes(b'isolated-test-encoder')
    (encoder / 'config.json').write_text('{}')
    cases = []
    for index, voice in enumerate(('training', 'Jessica')):
        audio = tmp_path / f'{index}.wav'
        pcm = struct.pack('<h', 10000 + index) * 8000
        with wave.open(str(audio), 'wb') as wav:
            wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'));wav.writeframes(pcm)
        cases.append(row(voice, f'distinct reference {index}', 'k u') | {
            'id': str(index), 'audio': str(audio), 'pcm_sha256': hashlib.sha256(pcm).hexdigest(),
        })
    manifest = tmp_path / 'cases.json'
    manifest.write_text(json.dumps({
        'dataset': 'synthetic-unit-fixture', 'revision': 'test', 'label_type': 'synthetic_altered_phones',
        'encoder_sha256': hashlib.sha256((encoder / 'model.bin').read_bytes()).hexdigest(),
        'cases': cases,
    }))
    calls = []

    class EncoderOnly:
        def __init__(self, *args, **kwargs):
            class Extractor:
                def __call__(self, audio): return np.zeros((80, 3050), np.float32)
            self.feature_extractor = Extractor()
            self.feature_extractor.__dict__.update(frontend().__dict__)

        def encode(self, features):
            assert features.shape == (80, 3000)
            calls.append('encode')
            return np.zeros((1, 1500, 512), np.float32)

        def transcribe(self, *args, **kwargs):
            raise AssertionError('A text decoder cannot supply pronunciation evidence')

    monkeypatch.setitem(sys.modules, 'faster_whisper', SimpleNamespace(WhisperModel=EncoderOnly))
    monkeypatch.setattr(os, 'nice', lambda value: None)
    monkeypatch.setattr(torch, 'set_num_interop_threads', lambda value: None)
    report = run_pilot(manifest, encoder, tmp_path / 'output', epochs=1)
    assert calls == ['encode', 'encode']
    assert report['qualified'] is False
    assert report['human_evaluation_pending'] is True
    assert report['text_decoder_used'] is False
    assert report['training_clips'] == report['synthetic_validation_clips'] == 1
    assert np.isfinite(report['history'][0]['training_loss'])
    assert np.isfinite(report['history'][0]['synthetic_validation_loss'])
    assert (tmp_path / 'output' / 'experimental-head.pt').exists()
