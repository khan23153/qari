import hashlib
import io
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf
import torch
from torch import nn

from ml.training.human_word_data import parse_label_row
from ml.training.kaggle_human_word_job import decode_source_audio
from ml.training.kaggle_local_vowel_job import native_frame_features, prepare_local_vowel_features


WORDS = [[21, 33, 23], [26, 33, 27, 32], [23, 23, 32, 29, 29, 26, 33], [1, 32, 6, 32, 8, 38]]
IDENTITY = {'model_sha256': '6'*64, 'crop_implementation_sha256': '7'*64}


def fixtures(amplitude=.1):
    out = io.BytesIO()
    samples = (amplitude*np.sin(2*np.pi*200*np.arange(20480)/16000)).astype(np.float32)
    sf.write(out, samples, 16000, format='WAV', subtype='PCM_16')
    raw = out.getvalue()
    row = parse_label_row(dict(file_name='data/ID45V1T.wav', label='1', label_name='correct',
                              verse_number='1', verse_text='قُلْ هُوَ اللَّهُ أَحَدٌ',
                              error_location='', error_type='', error_explanation=''), set())
    if amplitude:
        actual = decode_source_audio(raw)
    else:
        actual = samples
    row.update(source_sha256=hashlib.sha256(raw).hexdigest(), sample_count=len(actual),
               float_pcm_sha256=hashlib.sha256(actual.astype('<f4').tobytes()).hexdigest())
    audit = {'dataset': 'MuazAhmad7/Surah_Ikhlas-Labeled_Dataset',
             'revision': '973b5ef1d1532bcbe7e9a5a5b0dce125cc4d0dac',
             'cases': [row], 'reserved_speakers': []}
    ids = [t for word in WORDS for t in word]
    owners = [i for i, word in enumerate(WORDS) for _ in word]
    refs = {'ayahs': {'1': {'uthmani': 'قُلْ هُوَ اللَّهُ أَحَدٌ',
                           'reference_ids': ids, 'reference_word_indices': owners,
                           'word_reference_ids': WORDS}}}
    return raw, audit, refs


def encoded(samples):
    # Native-stack fixture only; no model accuracy claim from synthetic features.
    ids = [t for word in WORDS for t in word]
    records = []; frame = 0; previous = None
    for token in ids:
        if token == previous:
            frame += 1
        records.append(dict(id=token, start_frame=frame, end_frame=frame+1, confidence=.99))
        previous = token; frame += 1
    return np.ones((32, 1024), dtype=np.float16), records


class NativeStack(nn.Module):
    def __init__(self):
        super().__init__()
        self.dropout = nn.Identity()
        self.level_to_lm_head = nn.ModuleDict({'phonemes': nn.Linear(1024, 43, bias=False)})
        with torch.no_grad():
            self.level_to_lm_head['phonemes'].weight.zero_()
            self.level_to_lm_head['phonemes'].weight[:, :43] = torch.eye(43)

    def wav2vec2_bert(self, input_features):
        return SimpleNamespace(last_hidden_state=input_features)


def test_native_feature_tap_preserves_ctc_repeats_without_reference_input():
    path = [0, 21, 21, 0, 21, 33, 33, 0]
    features = torch.zeros(1, 8, 1024)
    for i, token in enumerate(path):
        features[0, i, token] = 12
    def frontend(samples, sampling_rate, return_tensors):
        assert len(samples) == 5120 and sampling_rate == 16000 and return_tensors == 'pt'
        return {'input_features': features}
    x, records = native_frame_features(np.ones(5120, np.float32)*.1, frontend, NativeStack(), device='cpu')
    assert x.dtype == np.float16 and x.shape == (8, 1024)
    assert [r['id'] for r in records] == [21, 21, 33]
    assert [(r['start_frame'], r['end_frame']) for r in records] == [(1, 3), (4, 5), (5, 7)]


def test_feature_cache_keeps_actual_source_pcm_and_word_frame_identity(tmp_path):
    raw, audit, refs = fixtures()
    identity = {'model_sha256': '6'*64, 'crop_implementation_sha256': '7'*64}
    manifest = prepare_local_vowel_features(audit, refs, encoded, tmp_path/'cache', tmp_path/'out',
                                           identity, fetch=lambda _: raw)
    assert len(manifest['cases']) == 4 and all(r['available'] for r in manifest['cases'])
    assert manifest['sources'][0]['float_pcm_sha256'] == audit['cases'][0]['float_pcm_sha256']
    for row in manifest['cases']:
        with np.load(row['feature_path'], allow_pickle=False) as data:
            assert data['features'].shape == (row['frame_end']-row['frame_start'], 1024)
        assert row['target'] == 0
        assert row['reference_ids'] == WORDS[row['word_index']]


@pytest.mark.parametrize('changed', ['source_sha', 'pcm_sha', 'silence', 'native_timebase'])
def test_wrong_identity_silence_or_native_frame_count_stops_before_cache(tmp_path, changed):
    raw, audit, refs = fixtures(amplitude=0 if changed == 'silence' else .1)
    if changed == 'source_sha': audit['cases'][0]['source_sha256'] = '0'*64
    if changed == 'pcm_sha': audit['cases'][0]['float_pcm_sha256'] = '0'*64
    def encode(samples):
        if changed != 'native_timebase':
            pytest.fail('Invalid source reached native encoder')
        _, records = encoded(samples)
        return np.ones((100, 1024), np.float16), records
    with pytest.raises(ValueError, match='SHA|PCM|speech|frame'):
        prepare_local_vowel_features(audit, refs, encode, tmp_path/'cache', tmp_path/'out',
                                     IDENTITY, fetch=lambda _: raw)
    assert not list((tmp_path/'cache').glob('*.npz'))


def test_missing_native_word_is_retained_as_unassessed_not_discarded(tmp_path):
    raw, audit, refs = fixtures()
    def blank(samples):
        return np.ones((32, 1024), np.float16), []
    manifest = prepare_local_vowel_features(audit, refs, blank, tmp_path/'cache', tmp_path/'out',
                                           IDENTITY, fetch=lambda _: raw)
    assert len(manifest['cases']) == 4
    assert all(r['available'] is False and r['feature_path'] is None for r in manifest['cases'])
    assert [r['target'] for r in manifest['cases']] == [0, 0, 0, 0]
