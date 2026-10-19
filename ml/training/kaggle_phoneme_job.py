"""Bounded synthetic-phone research job. This never promotes a live model."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
import torch
from torch import nn

from ml.training.phoneme_ctc_pilot import (
    altered_targets, crop_encoder_frames, greedy_phones, phoneme_distance, validate_ctc_frames,
)
from ml.training.phoneme_gpu import reference_group, source_role, TemporalPhoneHead

ENCODER_SHA = 'b47c0fc7cd202c24ad4c7816e29d06c7d37c3761c1dcc91690796227df01dfa0'
DATASET = 'IqraEval/Iqra_TTS'
REVISION = '97d27c2a575739e7aaffee2518d6817d203829c9'
MODEL_FILES = {'model.bin', 'config.json', 'tokenizer.json', 'vocabulary.json', 'preprocessor_config.json'}


def file_sha(path):
    with Path(path).open('rb') as asset:
        return hashlib.file_digest(asset, 'sha256').hexdigest()


def write_json(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def verify_encoder(path, *, expected_model_sha=ENCODER_SHA):
    path = Path(path)
    allowed = MODEL_FILES | {'encoder-manifest.json', 'dataset-metadata.json'}
    if any(p.is_symlink() or not p.is_file() or p.name not in allowed for p in path.iterdir()):
        raise ValueError('Unexpected encoder input; credentials and other files are forbidden')
    hashes = json.loads((path/'encoder-manifest.json').read_text())['files']
    if set(hashes) != MODEL_FILES or hashes.get('model.bin') != expected_model_sha:
        raise ValueError('Frozen encoder manifest identity mismatch')
    actual = {name: file_sha(path/name) for name in MODEL_FILES}
    if actual != hashes:
        raise ValueError('Frozen encoder input changed')
    return actual


def extract_batch(feature_extractor, encode, samples):
    if not 1 <= len(samples) <= 8:
        raise ValueError('Feature batch must contain1–8 utterances')
    for audio in samples:
        if (not isinstance(audio, np.ndarray) or audio.ndim != 1
                or not 4000 <= len(audio) <= 12*16000 or not np.isfinite(audio).all()
                or np.max(np.abs(audio)) > 1.01 or np.sqrt(np.mean(audio**2)) < .006):
            raise ValueError('Invalid or silent bounded16k speech')
    mel = np.ascontiguousarray(np.stack([feature_extractor(audio)[:, :3000] for audio in samples]), dtype=np.float32)
    if mel.shape != (len(samples), 80, 3000) or not np.isfinite(mel).all():
        raise ValueError('Unexpected frontend mel shape or values')
    encoded = np.asarray(encode(mel))
    if encoded.shape[0] != len(samples):
        raise ValueError('Encoder batch identity mismatch')
    result = []
    for index, audio in enumerate(samples):
        with np.errstate(over='ignore', invalid='ignore'):
            features = crop_encoder_frames(encoded[index:index+1], len(audio)).astype(np.float16)
        if not np.isfinite(features).all():
            raise ValueError('Nonfinite float16 cache features')
        result.append(features)
    return result


def load_features(row):
    with np.load(row['feature_path'], allow_pickle=False) as saved:
        features = saved['features']
    samples = row.get('sample_count')
    if (type(samples) is not int or not 4000 <= samples <= 12*16000
            or features.shape != (math.ceil(samples/320), 512)
            or features.dtype != np.float16 or not np.isfinite(features).all()):
        raise ValueError('Cached feature frame count or values mismatch original audio')
    validate_ctc_frames(altered_targets(row), len(features))
    return torch.from_numpy(features.astype(np.float32))


def validate_manifest(manifest, device):
    if manifest.get('label_type') != 'synthetic_altered_phones':
        raise ValueError('Only explicit synthetic altered-phone training is supported')
    cases = manifest['cases']
    if not 2 <= len(cases) <= 8192+512 or (device == 'cpu' and len(cases) > 128):
        raise ValueError('Training exceeds bounded GPU job or CPU smoke limits')
    seen_ids, seen_pcm = set(), set()
    for row in cases:
        if row['id'] in seen_ids:
            raise ValueError('Duplicate feature case')
        seen_ids.add(row['id'])
        pcm = row['float_pcm_sha256']
        if not isinstance(pcm, str) or len(pcm) != 64 or any(c not in '0123456789abcdef' for c in pcm):
            raise ValueError('Invalid source PCM hash')
        if pcm in seen_pcm:
            raise ValueError('Training/validation audio overlap or duplicate source')
        seen_pcm.add(pcm)
        if row['role'] != source_role(row) or row['reference_group'] != reference_group(row['sentence_ref']):
            raise ValueError('Leaked or invalid speaker/reference split')
        load_features(row)
    train = [r for r in cases if r['role'] == 'train']
    validation = [r for r in cases if r['role'] == 'validation']
    if not train or not validation or len(train) > 8192 or len(validation) > 512:
        raise ValueError('Both bounded training and validation sets are required')
    if {r['reference_group'] for r in train} & {r['reference_group'] for r in validation}:
        raise ValueError('Training/validation reference overlap')
    return train, validation


def check_resources(output, device, deadline):
    import resource
    import shutil
    if time.monotonic() >= deadline:
        raise TimeoutError('Bounded training deadline reached')
    if device == 'cuda':
        if shutil.disk_usage(output).free < 4*1024**3:
            raise RuntimeError('Remote4GiB disk reserve reached')
        free, _ = torch.cuda.mem_get_info()
        if free < 2*1024**3:
            raise RuntimeError('Remote2GiB GPU reserve reached')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 12*1024**2:
            raise RuntimeError('Remote12GiB resident-memory limit reached')


def train_features(manifest, output, *, epochs=40, device='cuda', deadline=None):
    # This small head fits in FP32; its first AMP GPU batch had nonfinite
    # gradients. Keep forward, backward and optimizer in FP32.
    if device not in ('cpu', 'cuda'):
        raise ValueError('Invalid bounded training configuration')
    with torch.autocast(device_type=device, enabled=False):
        return _train_features_fp32(manifest, output, epochs=epochs, device=device, deadline=deadline)


def _train_features_fp32(manifest, output, *, epochs=40, device='cuda', deadline=None):
    import random
    if device not in ('cpu', 'cuda') or type(epochs) is not int or not 1 <= epochs <= 40:
        raise ValueError('Invalid bounded training configuration')
    torch.set_num_threads(2)
    torch.manual_seed(42);random.seed(42)
    deadline = time.monotonic()+7200 if deadline is None else deadline
    output = Path(output);output.mkdir(parents=True, exist_ok=True)
    train, validation = validate_manifest(manifest, device)
    vocabulary = ['<blank>'] + sorted({phone for row in train for phone in altered_targets(row)})
    token_ids = {phone: i for i, phone in enumerate(vocabulary)}
    unknown = sorted({phone for row in validation for phone in altered_targets(row) if phone not in token_ids})
    head = TemporalPhoneHead(len(vocabulary)).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=1e-3)
    loss_fn = nn.CTCLoss(blank=0, zero_infinity=False)
    history, best, best_epoch = [], float('inf'), 0
    started = time.monotonic()

    def batch(rows):
        features = [load_features(row) for row in rows]
        lengths = torch.tensor([len(x) for x in features], dtype=torch.long)
        padded = nn.utils.rnn.pad_sequence(features, batch_first=True).to(device)
        return padded, lengths

    def ctc_loss(logits, lengths, rows):
        targets = torch.tensor([token_ids[p] for row in rows for p in altered_targets(row)],
                               dtype=torch.long, device=device)
        target_lengths = torch.tensor([len(altered_targets(row)) for row in rows], dtype=torch.long)
        return loss_fn(logits.float().log_softmax(-1).transpose(0, 1), targets, lengths, target_lengths)

    def evaluate():
        head.eval();distance = total = loss_total = 0;predictions = []
        with torch.inference_mode():
            for offset in range(0, len(validation), 16):
                check_resources(output, device, deadline)
                rows = validation[offset:offset+16];features, lengths = batch(rows)
                with torch.autocast(device_type=device, enabled=False):
                    logits = head(features, lengths)
                if not torch.isfinite(logits).all():
                    raise ValueError('Nonfinite validation phone logits')
                paths = logits.argmax(-1).cpu().tolist()
                for row, path, count in zip(rows, paths, lengths.tolist()):
                    heard = greedy_phones(path[:count], vocabulary);target = altered_targets(row)
                    distance += phoneme_distance(target, heard);total += len(target)
                    predictions.append({'case_id': row['id'], 'heard': heard, 'actual_target': target})
                if not unknown:
                    loss = ctc_loss(logits, lengths, rows)
                    if not torch.isfinite(loss):
                        raise ValueError('Nonfinite validation CTC loss')
                    loss_total += float(loss)*len(rows)
        return distance/max(1, total), None if unknown else loss_total/len(validation), predictions

    initial, _, _ = evaluate()
    report = {}
    for epoch in range(1, epochs+1):
        head.train();random.shuffle(train);loss_total = 0
        for offset in range(0, len(train), 16):
            check_resources(output, device, deadline)
            rows = train[offset:offset+16];features, lengths = batch(rows)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device, enabled=False):
                logits = head(features, lengths)
            loss = ctc_loss(logits, lengths, rows)
            if not torch.isfinite(loss):
                raise ValueError('Nonfinite training CTC loss')
            loss.backward()
            nn.utils.clip_grad_norm_(head.parameters(), 1., error_if_nonfinite=True)
            optimizer.step();loss_total += float(loss.detach())*len(rows)
        per, val_loss, predictions = evaluate()
        row = {'epoch': epoch, 'training_loss': loss_total/len(train),
               'validation_per': per, 'validation_loss': val_loss}
        history.append(row)
        if per < best:
            best, best_epoch = per, epoch
            checkpoint = {'state_dict': head.state_dict(), 'epoch': epoch, 'validation_per': per,
                          'vocabulary': vocabulary, 'architecture': 'temporal-phone-v1',
                          'feature_bundle_sha256': manifest['feature_bundle_sha256']}
            temporary = output/'candidate-head.pt.tmp';torch.save(checkpoint, temporary)
            temporary.replace(output/'candidate-head.pt')
            write_json(output/'validation-predictions.json', predictions)
        report = {'status': 'training', 'qualified': False, 'production_changed': False,
                  'human_qualification_pending': True, 'encoder_frozen': True, 'text_decoder_used': False,
                  'training_precision': 'float32', 'gradient_scaling': False,
                  'dataset': manifest['dataset'], 'dataset_revision': manifest['revision'],
                  'feature_bundle_sha256': manifest['feature_bundle_sha256'],
                  'vocabulary': vocabulary, 'training_clips': len(train), 'validation_clips': len(validation),
                  'training_voices': sorted({r['speaker'] for r in train}), 'validation_voice': 'Jessica',
                  'unknown_validation_phones': unknown, 'initial_validation_per': initial,
                  'best_validation_per': best, 'best_epoch': best_epoch, 'history': history,
                  'head_sha256': file_sha(output/'candidate-head.pt'),
                  'seconds': time.monotonic()-started}
        write_json(output/'training-report.json', report)
        print('CTC_EPOCH', json.dumps(row), flush=True)
        if epoch >= 6 and epoch-best_epoch >= 8:
            break
    report['status'] = 'completed_synthetic_experiment'
    write_json(output/'training-report.json', report)
    return report


def prepare_features(rows, feature_extractor, encode, cache, output, identity, *,
                     max_train=8192, min_train=4096, max_validation=512,
                     per_voice=1536, device='cuda', deadline=None):
    import collections
    import io
    import soundfile as sf
    if (not 1 <= min_train <= max_train <= 8192 or not 1 <= max_validation <= 512
            or not 1 <= per_voice <= 1536):
        raise ValueError('Invalid bounded source selection limits')
    cache, output = Path(cache), Path(output)
    cache.mkdir(parents=True, exist_ok=True);output.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic()+7200 if deadline is None else deadline
    counts = collections.Counter();voices = collections.Counter();excluded = collections.Counter()
    manifest = {'label_type': 'synthetic_altered_phones', 'dataset': DATASET, 'revision': REVISION,
                'feature_bundle_sha256': identity['feature_bundle_sha256'], 'feature_identity': identity,
                'qualified': False, 'production_changed': False, 'cases': []}
    seen_pcm, pending = {}, []
    began = time.monotonic()

    def flush():
        if not pending: return
        check_resources(output, device, deadline)
        features = extract_batch(feature_extractor, encode, [audio for _, audio in pending])
        for (record, _), encoded in zip(pending, features):
            key = hashlib.sha256((record['float_pcm_sha256']+identity['feature_bundle_sha256']).encode()).hexdigest()
            target = cache/(key+'.npz')
            np.savez_compressed(target, features=encoded)
            manifest['cases'].append(record | {'feature_path': str(target)})
        pending.clear()
        manifest.update(counts=dict(counts), training_voices=dict(voices), excluded=dict(excluded))
        write_json(output/'source-manifest.json', manifest)
        if len(manifest['cases']) <= 8 or len(manifest['cases']) % 64 == 0:
            print('CTC_FEATURES', dict(counts), 'seconds', round(time.monotonic()-began, 1), flush=True)

    for index, row in enumerate(rows):
        if index % 100 == 0: check_resources(output, device, deadline)
        try:
            role = source_role(row)
        except ValueError:
            excluded['missing_actual_altered_target'] += 1;continue
        if role is None:
            excluded['held_voice_or_reference_group'] += 1;continue
        if role == 'train' and (counts['train'] >= max_train or voices[row['speaker']] >= per_voice):
            excluded['training_cap'] += 1;continue
        if role == 'validation' and counts['validation'] >= max_validation:
            excluded['validation_cap'] += 1;continue
        encoded = row['audio'].get('bytes')
        if not isinstance(encoded, bytes) or not 1 <= len(encoded) <= 3_000_000:
            excluded['invalid_source_audio'] += 1;continue
        try:
            audio, rate = sf.read(io.BytesIO(encoded), dtype='float32')
        except (RuntimeError, ValueError):
            excluded['audio_decode_failed'] += 1;continue
        if (rate != 16000 or audio.ndim != 1 or not 4000 <= len(audio) <= 12*16000
                or not np.isfinite(audio).all() or np.max(np.abs(audio)) > 1.01
                or np.sqrt(np.mean(audio**2)) < .006):
            excluded['invalid_pcm_or_energy'] += 1;continue
        try:
            validate_ctc_frames(altered_targets(row), math.ceil(len(audio)/320))
        except ValueError:
            excluded['impossible_ctc_frames'] += 1;continue
        pcm_sha = hashlib.sha256(np.ascontiguousarray(audio, dtype='<f4').tobytes()).hexdigest()
        if pcm_sha in seen_pcm:
            if seen_pcm[pcm_sha] != role:
                raise ValueError('Training/validation source PCM overlap')
            excluded['duplicate_pcm'] += 1;continue
        seen_pcm[pcm_sha] = role
        record = {key: row[key] for key in ('speaker', 'sentence_ref', 'sentence_aug', 'label', 'phoneme_mis')}
        record.update(id=f'tts-{index}', role=role, sample_count=len(audio),
                      source_audio_sha256=hashlib.sha256(encoded).hexdigest(), float_pcm_sha256=pcm_sha,
                      reference_group=reference_group(row['sentence_ref']))
        counts[role] += 1
        if role == 'train': voices[row['speaker']] += 1
        pending.append((record, audio))
        if len(pending) == 8: flush()
        if counts['train'] >= max_train and counts['validation'] >= max_validation: break
    flush()
    if counts['train'] < min_train or counts['validation'] < max_validation:
        raise ValueError(f'Insufficient independently split altered speech: {dict(counts)}')
    manifest.update(counts=dict(counts), training_voices=dict(voices), excluded=dict(excluded))
    write_json(output/'source-manifest.json', manifest)
    return manifest


def main(*, deadline=None):
    import argparse
    import importlib.metadata
    import os
    os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
    os.environ['HF_HOME'] = '/kaggle/temp/qari-hf'
    import ctranslate2
    from datasets import Audio, load_dataset
    from faster_whisper import WhisperModel
    from ml.training.frozen_whisper_frontend import FeatureExtractor as FrozenFrontend
    from ml.training.phoneme_ctc_pilot import feature_identity

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--encoder', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('/kaggle/working'))
    parser.add_argument('--cache', type=Path, default=Path('/kaggle/temp/qari-phone-features'))
    args = parser.parse_args()
    if deadline is None:
        from ml.training.kaggle_job_budget import job_budget
        with job_budget(args.output) as whole_job_deadline:
            return main(deadline=whole_job_deadline)
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        hashes = verify_encoder(args.encoder)
        if not torch.cuda.is_available():
            raise RuntimeError('A GPU was requested; CPU fallback is forbidden')
        torch.cuda.set_device(0)
        if 'int8_float32' not in ctranslate2.get_supported_compute_types('cuda', device_index=0):
            raise RuntimeError('Requested native INT8/FP32 CUDA compute is unsupported')
        model = WhisperModel(str(args.encoder), device='cuda', device_index=0,
                             compute_type='int8_float32', cpu_threads=2, local_files_only=True)
        model.feature_extractor = FrozenFrontend()
        identity = feature_identity(args.encoder, model.feature_extractor)
        identity.update(encoder_files=hashes, device='cuda:0', compute_type='int8_float32',
                        gpu_name=torch.cuda.get_device_name(0),
                        versions={name: importlib.metadata.version(name) for name in
                                  ['numpy', 'torch', 'ctranslate2', 'faster-whisper', 'datasets', 'soundfile']},
                        training_code_sha256={name: file_sha(Path(__file__).parent/name) for name in
                                              ['kaggle_phoneme_job.py', 'phoneme_gpu.py', 'phoneme_ctc_pilot.py']})
        identity['feature_bundle_sha256'] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        write_json(args.output/'feature-identity.json', identity)
        print('GPU_SETUP', json.dumps(identity), flush=True)
        rows = load_dataset(DATASET, split='train', revision=REVISION,
                            streaming=True).cast_column('audio', Audio(decode=False))

        def encode(mel):
            return np.asarray(model.model.encode(ctranslate2.StorageView.from_array(mel), to_cpu=True))

        manifest = prepare_features(rows, model.feature_extractor, encode, args.cache,
                                    args.output, identity, deadline=deadline)
        del rows, model
        report = train_features(manifest, args.output, deadline=deadline)
        if verify_encoder(args.encoder) != hashes:
            raise RuntimeError('Frozen encoder changed during training')
        print('GPU_SYNTHETIC_EXPERIMENT_COMPLETE', json.dumps({
            key: report[key] for key in ['qualified', 'training_clips', 'validation_clips',
                                       'best_epoch', 'best_validation_per', 'head_sha256']}), flush=True)
    except Exception as error:
        write_json(args.output/'failure.json', {'status': 'failed', 'qualified': False,
                                              'production_changed': False,
                                              'error_type': type(error).__name__, 'message': str(error)})
        raise


if __name__ == '__main__':
    main()
