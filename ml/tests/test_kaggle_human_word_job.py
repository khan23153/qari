import hashlib
import io
import json
import threading
import time

import numpy as np
import pytest
import soundfile as sf

from ml.training.human_word_data import parse_label_row
from ml.training.kaggle_human_word_job import decode_source_audio, prepare_human_features


def wave_bytes(rate=16000, seconds=.32, amplitude=.1, frequency=200):
    x = amplitude * np.sin(2 * np.pi * frequency * np.arange(round(rate * seconds)) / rate)
    out = io.BytesIO(); sf.write(out, x.astype(np.float32), rate, format='WAV', subtype='PCM_16')
    return out.getvalue()


def label(speaker, ayah=1):
    return parse_label_row(dict(file_name=f'data/ID{speaker}V{ayah}T.wav', label='1', label_name='correct',
                               verse_number=str(ayah), verse_text='قُلْ هُوَ اللَّهُ أَحَدٌ' if ayah == 1 else 'اللَّهُ الصَّمَدُ',
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


def test_duplicate_cross_split_participants_are_quarantined_before_encoding(tmp_path):
    # Reproduces actual pinned source collision ID187V1T(test)/ID193V1T(train).
    # Unique clips from either ambiguous participant must be excluded too.
    manifest = {'cases': [label(187), label(193), label(187, 2)], 'reserved_speakers': [], 'excluded': []}
    def unexpected_encode(_):
        pytest.fail('Duplicate-participant audio reached encoder')
    saved = prepare_human_features(manifest, unexpected_encode, unexpected_encode,
                                   tmp_path / 'cache', tmp_path / 'out', {},
                                   fetch=lambda name: wave_bytes(frequency=210 if 'V2' in name else 200))
    assert saved['cases'] == []
    assert saved['quarantined_speakers'] == ['187', '193']
    assert len(saved['excluded']) == 3
    assert len(saved['duplicate_pcm_groups']) == 1


def test_invalid_audio_is_reported_not_fed_to_encoder(tmp_path):
    manifest = {'cases': [label(45)], 'reserved_speakers': [], 'excluded': []}
    def unexpected_encode(_):
        pytest.fail('Silence reached encoder')
    saved = prepare_human_features(manifest, unexpected_encode, unexpected_encode,
                                   tmp_path / 'cache', tmp_path / 'out', {},
                                   fetch=lambda _: wave_bytes(amplitude=0))
    assert saved['cases'] == []
    assert saved['excluded'][0]['source_file'] == manifest['cases'][0]['source_file']


def test_prefetch_is_ordered_and_never_exceeds_four_inflight_fetches():
    from ml.training.kaggle_human_word_job import prefetch_sources
    lock = threading.Lock(); active = 0; peak = 0
    def fetch(name):
        nonlocal active, peak
        with lock:
            active += 1; peak = max(peak, active)
        time.sleep(.03 if name == '0' else .01)
        with lock: active -= 1
        return name.encode()
    rows = [{'source_file': str(i)} for i in range(8)]
    result = list(prefetch_sources(rows, fetch))
    assert [data for _, data in result] == [str(i).encode() for i in range(8)]
    assert 2 <= peak <= 4


def test_download_budget_counts_partial_failed_reads_before_retry(monkeypatch):
    from ml.training import kaggle_human_word_job as job
    class Partial(io.BytesIO):
        def read(self, size=-1):
            if self.tell(): raise OSError('Temporary source disconnect')
            return super().read(min(size, 6))
    responses = iter([Partial(b'12345678'), io.BytesIO(b'1234567')])
    monkeypatch.setattr(job.urllib.request, 'urlopen', lambda *a, **k: next(responses))
    monkeypatch.setattr(job.time, 'sleep', lambda _: None)
    monkeypatch.setattr(job, 'MAX_FILE_BYTES', 8)
    monkeypatch.setattr(job, 'MAX_TOTAL_BYTES', 12)
    budget = {'bytes': 0}
    with pytest.raises(ValueError, match='byte limit'):
        job.fetch_public('metadata.csv', budget, time.monotonic() + 5)
    assert budget['bytes'] <= 12
    assert budget['bytes'] >= 6


def test_oversized_source_is_excluded_without_aborting_clean_audio_audit(tmp_path, monkeypatch):
    # The pinned dataset contains ID247V1T.wav (3,310,754 bytes). A per-file
    # rejection must not abort the other participants or relax the byte cap.
    from ml.training import kaggle_human_word_job as job
    valid = wave_bytes()
    rejected, accepted = label(247), label(45)
    sources = {rejected['source_file']: b'x' * (len(valid) + 1),
               accepted['source_file']: valid}
    monkeypatch.setattr(job, 'MAX_FILE_BYTES', len(valid))
    monkeypatch.setattr(job, 'MAX_TOTAL_BYTES', len(valid) * 4)
    monkeypatch.setattr(job.urllib.request, 'urlopen',
                        lambda url, **kwargs: io.BytesIO(sources['data/' + url.rsplit('/data/', 1)[1]]))
    budget = {'bytes': 0}
    saved = prepare_human_features(
        {'cases': [rejected, accepted], 'reserved_speakers': [], 'excluded': []},
        lambda _: np.zeros((80, 3000), np.float32),
        lambda mel: np.zeros((len(mel), 1500, 512), np.float32),
        tmp_path / 'cache', tmp_path / 'out', {},
        fetch=lambda name: job.fetch_public(name, budget, time.monotonic() + 5))
    assert [row['speaker_id'] for row in saved['cases']] == ['45']
    exclusion, = saved['excluded']
    assert exclusion['source_file'] == 'data/ID247V1T.wav'
    assert exclusion['reason'] == 'Source audio exceeds per-file byte limit'
    assert exclusion['downloaded_bytes'] == len(valid) + 1
    assert exclusion['source_sha256'] is None  # A prefix is not a full file hash.
    assert budget['bytes'] == saved['source_bytes'] == 2 * len(valid) + 1
    assert not (tmp_path / 'cache' / 'pcm' / (rejected['id'] + '.npy')).exists()


def test_total_download_budget_still_aborts_instead_of_becoming_an_exclusion(tmp_path, monkeypatch):
    from ml.training import kaggle_human_word_job as job
    source = wave_bytes()
    monkeypatch.setattr(job, 'MAX_FILE_BYTES', len(source))
    monkeypatch.setattr(job, 'MAX_TOTAL_BYTES', len(source) // 2)
    monkeypatch.setattr(job.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(source))
    budget = {'bytes': 0}
    with pytest.raises(ValueError, match='byte limit'):
        prepare_human_features(
            {'cases': [label(45)], 'reserved_speakers': [], 'excluded': []},
            lambda _: pytest.fail('Budget-exhausted audio reached encoder'),
            lambda _: pytest.fail('Budget-exhausted audio reached encoder'),
            tmp_path / 'cache', tmp_path / 'out', {},
            fetch=lambda name: job.fetch_public(name, budget, time.monotonic() + 5))
    assert budget['bytes'] <= len(source) // 2
    assert not (tmp_path / 'out' / 'source-manifest.json').exists()
