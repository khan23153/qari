"""Bounded public human-label experiment, never a production pronunciation grader."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import time
import urllib.request

import numpy as np

from ml.training.human_word_data import parse_label_row
from ml.training.human_word_head import train_word_features
from ml.training.kaggle_phoneme_job import check_resources, extract_batch, file_sha, verify_encoder, write_json

DATASET = 'MuazAhmad7/Surah_Ikhlas-Labeled_Dataset'
REVISION = '973b5ef1d1532bcbe7e9a5a5b0dce125cc4d0dac'
MAX_FILE_BYTES = 3000000
MAX_TOTAL_BYTES = 1000000000


def decode_source_audio(data):
    import soundfile as sf
    from scipy.signal import resample_poly
    if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_FILE_BYTES:
        raise ValueError('Oversized or empty source audio')
    try:
        with sf.SoundFile(io.BytesIO(data)) as sound:
            rate, channels = sound.samplerate, sound.channels
            if not 8000 <= rate <= 96000 or channels not in (1, 2) or not .25 <= sound.frames / rate <= 12:
                raise ValueError('Unbounded source audio format or duration')
            samples = sound.read(dtype='float32', always_2d=True).mean(axis=1)
    except (RuntimeError, sf.LibsndfileError) as error:
        raise ValueError('Source audio is not decodable PCM') from error
    if rate != 16000:
        divisor = math.gcd(rate, 16000)
        samples = resample_poly(samples, 16000 // divisor, rate // divisor).astype(np.float32)
    samples = np.ascontiguousarray(samples, dtype=np.float32)
    if (not 4000 <= len(samples) <= 192000 or not np.isfinite(samples).all()
            or np.max(np.abs(samples)) > 1.01 or np.sqrt(np.mean(samples ** 2)) < .006):
        raise ValueError('Invalid or below-guard source speech')
    return samples


def prepare_human_features(manifest, feature_extractor, encode, cache, output, identity, *, fetch, deadline=None, device='cpu'):
    cache, output = Path(cache), Path(output)
    cache.mkdir(parents=True, exist_ok=True); output.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + 7100 if deadline is None else deadline
    result = {'label_type': 'human_binary_word_error', 'dataset': DATASET, 'revision': REVISION,
              'reserved_speakers': manifest['reserved_speakers'], 'cases': [],
              'excluded': list(manifest['excluded']), 'encoder_identity': identity,
              'metadata_sha256': manifest.get('metadata_sha256'), 'qualified': False,
              'production_changed': False, 'labels': 'Contributor word labels, not independently adjudicated'}
    seen_pcm = {}; source_bytes = 0
    for row in manifest['cases']:
        check_resources(output, device, deadline)
        data = fetch(row['source_file'])
        source_bytes += len(data)
        if source_bytes > MAX_TOTAL_BYTES:
            raise ValueError('Public source byte budget exceeded')
        try:
            samples = decode_source_audio(data)
        except ValueError as error:
            result['excluded'].append({'source_file': row['source_file'], 'reason': str(error),
                                       'source_sha256': hashlib.sha256(data).hexdigest()})
            continue
        pcm_sha = hashlib.sha256(samples.astype('<f4', copy=False).tobytes()).hexdigest()
        if pcm_sha in seen_pcm:
            raise ValueError(f'Duplicate actual PCM: {seen_pcm[pcm_sha]} and {row["id"]}')
        seen_pcm[pcm_sha] = row['id']
        x = extract_batch(feature_extractor, encode, [samples])[0]
        target = cache / (row['id'] + '.npz')
        np.savez_compressed(target, features=x)
        result['cases'].append({**row, 'source_sha256': hashlib.sha256(data).hexdigest(),
                                'float_pcm_sha256': pcm_sha, 'sample_count': len(samples),
                                'rms': float(np.sqrt(np.mean(samples ** 2))),
                                'feature_path': str(target), 'feature_sha256': file_sha(target)})
        if len(result['cases']) % 32 == 0:
            write_json(output / 'source-manifest.json', result)
            print('HUMAN_WORD_FEATURES', len(result['cases']), 'source_bytes', source_bytes, flush=True)
    result['source_bytes'] = source_bytes
    write_json(output / 'source-manifest.json', result)
    return result


def fetch_public(source_file, budget, deadline):
    """Unauthenticated pinned public sources, counted bounded reads and retries."""
    url = f'https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/{source_file}'
    for attempt in range(3):
        if time.monotonic() >= deadline:
            raise TimeoutError('Source download deadline reached')
        try:
            with urllib.request.urlopen(url, timeout=25) as response:
                data = bytearray()
                while True:
                    remaining = min(MAX_FILE_BYTES - len(data), MAX_TOTAL_BYTES - budget['bytes'])
                    chunk = response.read(min(65536, remaining + 1))
                    budget['bytes'] += len(chunk); data.extend(chunk)
                    if len(data) > MAX_FILE_BYTES or budget['bytes'] > MAX_TOTAL_BYTES:
                        raise ValueError('Public source download byte limit exceeded')
                    if not chunk:
                        return bytes(data)
        except (OSError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def main(*, deadline=None):
    import argparse
    import importlib.metadata
    import ctranslate2
    import torch
    from faster_whisper import WhisperModel
    from ml.training.frozen_whisper_frontend import FeatureExtractor as FrozenFrontend
    from ml.training.phoneme_ctc_pilot import feature_identity
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--encoder', type=Path, required=True)
    parser.add_argument('--labels', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('/kaggle/working'))
    parser.add_argument('--cache', type=Path, default=Path('/kaggle/temp/qari-human-word-features'))
    args = parser.parse_args()
    if deadline is None:
        from ml.training.kaggle_job_budget import job_budget
        with job_budget(args.output) as whole_deadline:
            return main(deadline=whole_deadline)
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        labels = json.loads(args.labels.read_text())
        if labels['dataset'] != DATASET or labels['revision'] != REVISION:
            raise ValueError('Human source pin mismatch')
        budget = {'bytes': 0}
        raw_metadata = fetch_public('metadata.csv', budget, deadline)
        if hashlib.sha256(raw_metadata).hexdigest() != labels['metadata_sha256']:
            raise ValueError('Pinned public metadata SHA mismatch')
        parsed = []
        for row in csv.DictReader(io.StringIO(raw_metadata.decode('utf-8-sig'))):
            try:
                parsed.append(parse_label_row(row, set(labels['reserved_speakers'])))
            except ValueError:
                continue
        if parsed != labels['cases']:
            raise ValueError('Public human labels changed from audited manifest')
        hashes = verify_encoder(args.encoder)
        if not torch.cuda.is_available():
            raise RuntimeError('Private GPU job cannot fall back to VPS CPU')
        torch.cuda.set_device(0)
        if 'int8_float32' not in ctranslate2.get_supported_compute_types('cuda', device_index=0):
            raise RuntimeError('Native frozen encoder GPU compute unavailable')
        model = WhisperModel(str(args.encoder), device='cuda', device_index=0,
                             compute_type='int8_float32', cpu_threads=2, local_files_only=True)
        model.feature_extractor = FrozenFrontend()
        identity = feature_identity(args.encoder, model.feature_extractor)
        identity.update(encoder_files=hashes, device='cuda:0', compute_type='int8_float32',
                        gpu_name=torch.cuda.get_device_name(0),
                        versions={name: importlib.metadata.version(name) for name in
                                  ['numpy', 'torch', 'ctranslate2', 'faster-whisper', 'soundfile', 'scipy']},
                        code_sha256={name: file_sha(Path(__file__).parent / name) for name in
                                     ['human_word_data.py', 'human_word_head.py', 'kaggle_human_word_job.py']})
        identity['feature_bundle_sha256'] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        write_json(args.output / 'feature-identity.json', identity)
        print('HUMAN_WORD_GPU_SETUP', json.dumps(identity), flush=True)
        def encode(mel):
            return np.asarray(model.model.encode(ctranslate2.StorageView.from_array(mel), to_cpu=True))
        manifest = prepare_human_features(labels, model.feature_extractor, encode, args.cache,
                                          args.output, identity, device='cuda', deadline=deadline,
                                          fetch=lambda name: fetch_public(name, budget, deadline))
        counts = {role: sum(r['role'] == role for r in manifest['cases']) for role in ['train', 'validation', 'test']}
        if any(counts[role] < minimum for role, minimum in [('train', 800), ('validation', 80), ('test', 80)]):
            raise ValueError('Too few bounded human utterances after exclusions')
        del model
        report = train_word_features(manifest, args.output, device='cuda', epochs=30, deadline=deadline)
        if verify_encoder(args.encoder) != hashes:
            raise RuntimeError('Frozen original encoder changed')
        print('HUMAN_WORD_COMPLETE', json.dumps({k: report[k] for k in
              ['qualified', 'best_epoch', 'threshold', 'metrics']}), flush=True)
    except Exception as error:
        write_json(args.output / 'failure.json', {'status': 'failed', 'qualified': False,
                   'production_changed': False, 'error_type': type(error).__name__, 'message': str(error)})
        raise


if __name__ == '__main__':
    main()
