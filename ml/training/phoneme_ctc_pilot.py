"""Experimental frozen-encoder CTC phone pilot; never promotes a live model.

Only synthetic altered-phone targets are accepted. Canonical reference text is
used for split grouping, never as an acoustic recognition prompt or fallback.
"""
from __future__ import annotations

import math
import re
import numpy as np


def altered_targets(row):
    if (row.get('label') != 'augmented' or not isinstance(row.get('sentence_aug'), str)
            or not row['sentence_aug'].strip() or not isinstance(row.get('phoneme_mis'), str)):
        raise ValueError('An altered utterance with explicit realized-phone targets is required')
    phones = tuple(token for token in row['phoneme_mis'].split() if token != '<sil>')
    if not phones or len(phones) > 500:
        raise ValueError('Missing or oversized realized-phone target; no canonical fallback')
    return phones


def split_voices(rows, held_voice):
    if not isinstance(held_voice, str) or not held_voice:
        raise ValueError('A known validation voice is required')
    for row in rows:
        if not row.get('speaker') or not row.get('sentence_ref', '').strip():
            raise ValueError('Known voice and reference group are required')
    group = lambda row: re.sub(r'\s+', ' ', row['sentence_ref']).strip()
    validation = [row for row in rows if row['speaker'] == held_voice]
    groups = {group(row) for row in validation}
    train = [row for row in rows if row['speaker'] != held_voice and group(row) not in groups]
    if not train or not validation:
        raise ValueError('Training and voice/text-disjoint validation must both be nonempty')
    return train, validation


def validate_ctc_frames(phones, frames):
    needed = len(phones) + sum(a == b for a, b in zip(phones, phones[1:]))
    if not phones or type(frames) is not int or frames < needed:
        raise ValueError('CTC frames cannot represent this phone sequence')


def crop_encoder_frames(encoded, sample_count):
    encoded = np.asarray(encoded)
    if type(sample_count) is not int or not 0 < sample_count <= 30 * 16000:
        raise ValueError('A positive bounded sample count is required')
    count = math.ceil(sample_count / 320)
    if (encoded.ndim != 3 or encoded.shape[0] != 1 or encoded.shape[2] != 512
            or encoded.shape[1] < count or not np.isfinite(encoded).all()):
        raise ValueError('Invalid frozen-encoder output')
    return np.ascontiguousarray(encoded[0, :count], dtype=np.float32)


def greedy_phones(ids, vocabulary):
    result, previous = [], None
    for index in ids:
        index = int(index)
        if not 0 <= index < len(vocabulary):
            raise ValueError('CTC output outside vocabulary')
        if index != 0 and index != previous:
            result.append(vocabulary[index])
        previous = index
    return tuple(result)


def phoneme_distance(expected, actual):
    row = list(range(len(actual) + 1))
    for i, left in enumerate(expected, start=1):
        next_row = [i]
        for j, right in enumerate(actual, start=1):
            next_row.append(min(next_row[-1] + 1, row[j] + 1, row[j-1] + (left != right)))
        row = next_row
    return row[-1]


def feature_identity(encoder_dir, extractor, *, frontend_source=None):
    """Bind cached features to all model/frontend inputs and supported timing."""
    import hashlib
    import inspect
    import json
    from pathlib import Path

    supported = dict(sampling_rate=16000, hop_length=160, n_fft=400,
                     chunk_length=30, n_samples=480000, nb_max_frames=3000)
    if (any(getattr(extractor, key, None) != value for key, value in supported.items())
            or np.shape(getattr(extractor, 'mel_filters', None)) != (80, 201)):
        raise ValueError('Unsupported frontend: pilot requires16k/160hop/80mel/30seconds')
    def digest(path):
        with Path(path).open('rb') as asset:
            return hashlib.file_digest(asset, 'sha256').hexdigest()
    path = Path(encoder_dir)
    preprocessor = path/'preprocessor_config.json'
    identity = {
        'encoder_sha256': digest(path/'model.bin'),
        'encoder_config_sha256': digest(path/'config.json'),
        'preprocessor_config_sha256': digest(preprocessor) if preprocessor.exists() else None,
        'frontend_sha256': digest(frontend_source or inspect.getsourcefile(type(extractor))),
        'effective_frontend': supported | {'feature_size': 80},
        'cache_format': 'float16-cache-v2',
    }
    identity['feature_bundle_sha256'] = hashlib.sha256(
        json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return identity


def read_pcm16_bounded(path):
    import wave
    with wave.open(str(path), 'rb') as wav:
        if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (16000, 1, 2):
            raise ValueError('Pilot requires16k mono PCM16')
        count = wav.getnframes()
        if not 4000 <= count <= 12*16000:
            raise ValueError('Pilot requires bounded .25–12second PCM')
        pcm = wav.readframes(count)
        if len(pcm) != count*2:
            raise ValueError('Truncated training PCM')
    return pcm


def run_pilot(manifest_path, encoder_dir, output_dir, *, held_voice='Jessica', epochs=40):
    import hashlib
    import json
    import os
    from pathlib import Path
    import random
    import shutil
    import time
    import torch
    from torch import nn
    from faster_whisper import WhisperModel

    os.nice(19)
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(42)
    random.seed(42)
    if type(epochs) is not int or not 1 <= epochs <= 100:
        raise ValueError('Pilot epochs must be between1 and100')
    manifest = json.loads(Path(manifest_path).read_text())
    if manifest.get('label_type') != 'synthetic_altered_phones' or not 2 <= len(manifest['cases']) <= 128:
        raise ValueError('Pilot accepts at most128 explicitly synthetic clips')
    encoder_dir, output = Path(encoder_dir), Path(output_dir)
    def file_sha(path):
        with Path(path).open('rb') as asset:
            return hashlib.file_digest(asset, 'sha256').hexdigest()

    actual_encoder_sha = file_sha(encoder_dir / 'model.bin')
    if actual_encoder_sha != manifest.get('encoder_sha256'):
        raise ValueError('Frozen encoder identity mismatch')
    output.mkdir(parents=True, exist_ok=True)
    cache = output / 'features';cache.mkdir(exist_ok=True)
    train, validation = split_voices(manifest['cases'], held_voice)
    if {r['pcm_sha256'] for r in train} & {r['pcm_sha256'] for r in validation}:
        raise ValueError('Training/validation PCM overlap')
    vocabulary = ['<blank>'] + sorted({phone for row in train for phone in altered_targets(row)})
    token_ids = {phone: index for index, phone in enumerate(vocabulary)}
    model = WhisperModel(str(encoder_dir), device='cpu', compute_type='int8', cpu_threads=1, local_files_only=True)
    identity = feature_identity(encoder_dir, model.feature_extractor)
    feature_bundle_sha = identity['feature_bundle_sha256']
    prepared = []
    started = time.monotonic()
    for index, row in enumerate(train + validation):
        pcm = read_pcm16_bounded(row['audio'])
        if hashlib.sha256(pcm).hexdigest() != row['pcm_sha256'] or not 4000 <= len(pcm)//2 <= 12*16000:
            raise ValueError('Changed or unbounded training PCM')
        audio = np.frombuffer(pcm, dtype='<i2').astype(np.float32) / 32768.
        if float(np.sqrt(np.mean(audio ** 2))) < .006:
            raise ValueError('Silent speech-training sample')
        phones = altered_targets(row)
        key = hashlib.sha256((row['pcm_sha256'] + feature_bundle_sha).encode()).hexdigest()
        target = cache / (key + '.npz')
        if target.exists():
            with np.load(target, allow_pickle=False) as saved:
                features = saved['features'].astype(np.float32)
            if features.shape != (math.ceil(len(audio)/320), 512) or not np.isfinite(features).all():
                raise ValueError('Corrupt cached acoustic features')
        else:
            if shutil.disk_usage(output).free < 512*1024**2 + 5*1024**2:
                raise ValueError('Pilot disk reserve reached')
            # Whisper requires exactly3000mel frames. The extractor appends
            # silence; crop that padded input, then retain only actual audio.
            mel = model.feature_extractor(audio)[:, :3000]
            features = crop_encoder_frames(np.asarray(model.encode(mel)), len(audio))
            np.savez_compressed(target, features=features.astype(np.float16))
            features = features.astype(np.float16).astype(np.float32)
        validate_ctc_frames(phones, len(features))
        prepared.append((row, torch.from_numpy(features), phones))
        if index % 8 == 0:
            print('PILOT_FEATURES', index+1, len(train)+len(validation), 'seconds', round(time.monotonic()-started, 1), flush=True)
    del model
    train_data, validation_data = prepared[:len(train)], prepared[len(train):]
    head = nn.Sequential(nn.LayerNorm(512), nn.Linear(512, 256), nn.GELU(), nn.Linear(256, len(vocabulary)))
    optimizer = torch.optim.AdamW(head.parameters(), lr=1e-3)
    loss_fn = nn.CTCLoss(blank=0, zero_infinity=False)
    history = []
    best = float('inf')

    def evaluate():
        head.eval();distance = total = 0;predictions = [];losses = []
        with torch.inference_mode():
            for row, features, phones in validation_data:
                logits = head(features)
                heard = greedy_phones(logits.argmax(-1).tolist(), vocabulary)
                distance += phoneme_distance(phones, heard);total += len(phones)
                predictions.append({'case_id': row['id'], 'heard': heard, 'actual_target': phones})
                if all(phone in token_ids for phone in phones):
                    loss = loss_fn(logits.log_softmax(-1)[:, None, :],
                                   torch.tensor([token_ids[p] for p in phones]),
                                   torch.tensor([len(features)]), torch.tensor([len(phones)]))
                    if not torch.isfinite(loss):
                        raise ValueError('Nonfinite CTC validation loss')
                    losses.append(float(loss))
        # Unknown targets count in PER; no misleading partial validation loss.
        validation_loss = sum(losses)/len(losses) if len(losses) == len(validation_data) else None
        return distance / max(1, total), predictions, validation_loss

    initial_per, _, _ = evaluate()
    for epoch in range(1, epochs+1):
        head.train();random.shuffle(train_data);total_loss = 0.
        for offset in range(0, len(train_data), 8):
            batch = train_data[offset:offset+8]
            lengths = torch.tensor([len(features) for _, features, _ in batch], dtype=torch.long)
            inputs = nn.utils.rnn.pad_sequence([features for _, features, _ in batch], batch_first=True)
            targets = torch.tensor([token_ids[p] for _, _, phones in batch for p in phones], dtype=torch.long)
            target_lengths = torch.tensor([len(phones) for _, _, phones in batch], dtype=torch.long)
            optimizer.zero_grad(set_to_none=True)
            log_probs = head(inputs).log_softmax(-1).transpose(0, 1)
            loss = loss_fn(log_probs, targets, lengths, target_lengths)
            if not torch.isfinite(loss):
                raise ValueError('Nonfinite CTC training loss')
            loss.backward();nn.utils.clip_grad_norm_(head.parameters(), 1.);optimizer.step()
            total_loss += float(loss.detach()) * len(batch)
        per, predictions, validation_loss = evaluate()
        row = {'epoch': epoch, 'training_loss': total_loss/len(train_data),
               'synthetic_validation_per': per, 'synthetic_validation_loss': validation_loss}
        history.append(row)
        if per < best:
            best = per
            torch.save(head.state_dict(), output / 'experimental-head.pt')
            (output/'validation-predictions.json').write_text(json.dumps(predictions)+'\n')
        report = {'production_changed': False, 'qualified': False, 'human_evaluation_pending': True,
                  'training_source': manifest['dataset'], 'dataset_revision': manifest['revision'],
                  **identity, 'encoder_frozen': True, 'text_decoder_used': False,
                  'input_frames_ms': 20, 'vocabulary': vocabulary, 'training_clips': len(train_data),
                  'synthetic_validation_clips': len(validation_data), 'synthetic_validation_voice': held_voice,
                  'initial_synthetic_per': initial_per, 'best_synthetic_per': best, 'history': history,
                  'unknown_validation_phones': sorted({p for _,_,phones in validation_data for p in phones if p not in token_ids}),
                  'seconds': time.monotonic()-started}
        (output/'pilot-report.json').write_text(json.dumps(report, indent=2)+'\n')
        print('PILOT_EPOCH', json.dumps(row), flush=True)
    return report


if __name__ == '__main__':
    import argparse
    import signal
    signal.alarm(1800)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--encoder', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--held-voice', default='Jessica')
    parser.add_argument('--epochs', type=int, default=40)
    args = parser.parse_args()
    run_pilot(args.manifest, args.encoder, args.output, held_voice=args.held_voice, epochs=args.epochs)
