import hashlib
import io
import json

import numpy as np
import pytest
import soundfile as sf

from ml.training.human_word_data import parse_label_row
from ml.training.kaggle_human_word_job import decode_source_audio, prepare_human_features


def wave_bytes(rate=16000, seconds=.32, amplitude=.1, frequency=200):
    x = amplitude * np.sin(2 * np.pi * frequency * np.arange(round(rate * seconds)) / rate)
    out = io.BytesIO(); sf.write(out, x.astype(np.float32), rate, format='WAV', subtype='PCM_16')
    return out.getvalue()


def label(speaker):
    return parse_label_row(dict(file_name=f'data/ID{speaker}V1T.wav', label='1', label_name='correct',
                               verse_number='1', verse_text='قُلْ هُوَ اللَّهُ أَحَدٌ',
                               error_location='', error_type='', error_explanation=''), set())


def test_resamples_real_source_pcm_to_sixteen_khz():
    x = decode_source_audio(wave_bytes(rate=8000))
    assert x.dtype == np.float32 and x.shape == (5120,)
    assert .06 < np.sqrt(np.mean(x ** 2)) < .08


@pytest.mark.parametrize('data', [b'x' * 3000001, wave_bytes(seconds=.1),
                                 wave_bytes(seconds=12.1), wave_bytes(amplitude=0)],
                         ids=['byte_budget', 'too_short', 'too_long', 'silence'])
def test_rejects_oversized_duration_and_silence_before_encoding(data):
    with pytest.raises(ValueError):
        decode_source_audio(data)


def test_cache_records_actual_audio_bytes_and_frames(tmp_path):
    source = wave_bytes()
    manifest = {'cases': [label(45)], 'reserved_speakers': [], 'excluded': []}
    saved = prepare_human_features(manifest, lambda _: np.zeros((80, 3000), np.float32),
                                   lambda mel: np.zeros((len(mel), 1500, 512), np.float32),
                                   tmp_path / 'cache', tmp_path / 'out', {},
                                   fetch=lambda _: source)
    row = saved['cases'][0]
    assert row['source_sha256'] == hashlib.sha256(source).hexdigest()
    assert row['sample_count'] == 5120
    with np.load(row['feature_path'], allow_pickle=False) as f:
        assert f['features'].shape == (16, 512)
    assert saved['label_type'] == 'human_binary_word_error'


def test_duplicate_real_pcm_stops_before_optimization(tmp_path):
    manifest = {'cases': [label(45), label(46)], 'reserved_speakers': [], 'excluded': []}
    with pytest.raises(ValueError, match='Duplicate'):
        prepare_human_features(manifest, lambda _: np.zeros((80, 3000), np.float32),
                               lambda mel: np.zeros((len(mel), 1500, 512), np.float32),
                               tmp_path / 'cache', tmp_path / 'out', {},
                               fetch=lambda _: wave_bytes())


def test_invalid_audio_is_reported_not_fed_to_encoder(tmp_path):
    manifest = {'cases': [label(45)], 'reserved_speakers': [], 'excluded': []}
    def unexpected_encode(_):
        pytest.fail('Silence reached encoder')
    saved = prepare_human_features(manifest, unexpected_encode, unexpected_encode,
                                   tmp_path / 'cache', tmp_path / 'out', {},
                                   fetch=lambda _: wave_bytes(amplitude=0))
    assert saved['cases'] == []
    assert saved['excluded'][0]['source_file'] == manifest['cases'][0]['source_file']
