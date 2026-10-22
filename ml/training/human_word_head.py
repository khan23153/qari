"""Research-only binary word-error head. This never changes live grading."""
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from ml.training.human_word_data import OFFSETS, REFERENCES, parse_label_row, select_threshold
from ml.training.kaggle_phoneme_job import check_resources, file_sha, write_json


class HumanWordHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.project = nn.Sequential(nn.LayerNorm(512), nn.Linear(512, 128), nn.GELU())
        self.temporal = nn.Conv1d(128, 128, 5, padding=2, groups=128)
        self.context_norm = nn.LayerNorm(128)
        self.queries = nn.Parameter(torch.randn(15, 128) * .02)
        self.attention = nn.MultiheadAttention(128, 4, dropout=.1, batch_first=True)
        self.output = nn.Sequential(nn.LayerNorm(128), nn.Linear(128, 1))
        self.register_buffer('frequencies', torch.exp(torch.arange(0, 128, 2) * (-math.log(10000.) / 128)), persistent=False)

    def forward(self, features, lengths):
        if (features.ndim != 3 or features.shape[2] != 512 or not 1 <= features.shape[1] <= 600
                or lengths.shape != (len(features),) or lengths.dtype != torch.long
                or (lengths < 1).any() or (lengths > features.shape[1]).any()):
            raise ValueError('Invalid bounded word acoustic frames')
        positions = torch.arange(features.shape[1], device=features.device)
        valid = positions[None, :] < lengths.to(features.device)[:, None]
        features = features.masked_fill(~valid[:, :, None], 0.)
        if not torch.isfinite(features).all():
            raise ValueError('Nonfinite real acoustic frames')
        x = self.project(features).masked_fill(~valid[:, :, None], 0.)
        x = self.context_norm(x + self.temporal(x.transpose(1, 2)).transpose(1, 2))
        phase = positions[:, None] * self.frequencies[None, :]
        positional = torch.stack((phase.sin(), phase.cos()), dim=-1).flatten(1)
        x = (x + positional[None]).masked_fill(~valid[:, :, None], 0.)
        query = self.queries[None].expand(len(features), -1, -1)
        attended, _ = self.attention(query, x, x, key_padding_mask=~valid, need_weights=False)
        return self.output(attended + query).squeeze(-1)


def masked_word_loss(logits, targets, mask):
    if logits.shape != targets.shape or logits.shape != mask.shape or mask.dtype != torch.bool or not mask.any():
        raise ValueError('Known human word labels required')
    selected = targets[mask]
    if not torch.isfinite(logits[mask]).all() or not ((selected == 0) | (selected == 1)).all():
        raise ValueError('Invalid known word logits or targets')
    return nn.functional.binary_cross_entropy_with_logits(logits[mask].float(), selected.float())


def validate_word_manifest(manifest, device):
    if manifest.get('label_type') != 'human_binary_word_error':
        raise ValueError('Explicit human binary word labels required')
    rows = manifest['cases']
    if not 3 <= len(rows) <= (64 if device == 'cpu' else 1506):
        raise ValueError('Bounded word experiment case limit exceeded')
    ids, pcm, speakers, features = set(), set(), {}, {}
    reserved = set(manifest['reserved_speakers'])
    for row in rows:
        if row['id'] in ids or row['float_pcm_sha256'] in pcm:
            raise ValueError('Duplicate source PCM or case across partitions')
        ids.add(row['id']); pcm.add(row['float_pcm_sha256'])
        if len(row['float_pcm_sha256']) != 64 or any(c not in '0123456789abcdef' for c in row['float_pcm_sha256']):
            raise ValueError('Missing actual source PCM identity')
        previous = speakers.setdefault(row['speaker_id'], row['role'])
        if previous != row['role']:
            raise ValueError('Speaker leakage across partitions')
        label = row['source_label']
        if label not in ('correct', 'error') or row['ayah'] not in REFERENCES:
            raise ValueError('Invalid source label')
        verified = parse_label_row({'file_name': row['source_file'], 'verse_number': str(row['ayah']),
                                    'verse_text': REFERENCES[row['ayah']], 'label_name': label,
                                    'label': '1' if label == 'correct' else '0',
                                    'error_type': row['source_error_type'],
                                    'error_location': row['source_error_location']}, reserved)
        if any(row[k] != verified[k] for k in ('id', 'speaker_id', 'role', 'ayah', 'targets', 'mask')):
            raise ValueError('Changed source word labels or speaker split')
        path = Path(row['feature_path'])
        if file_sha(path) != row['feature_sha256']:
            raise ValueError('Feature cache identity mismatch')
        with np.load(path, allow_pickle=False) as saved:
            x = saved['features']
        count = row['sample_count']
        if (type(count) is not int or not 4000 <= count <= 192000 or x.dtype != np.float16
                or x.shape != (math.ceil(count / 320), 512) or not np.isfinite(x).all()):
            raise ValueError('Feature frames differ from actual bounded PCM')
        features[row['id']] = torch.from_numpy(x.astype(np.float32))
    if any(not any(r['role'] == role for r in rows) for role in ('train', 'validation', 'test')):
        raise ValueError('Disjoint train/validation/test partitions required')
    return rows, features


def train_word_features(manifest, output, device='cpu', epochs=30, deadline=None):
    if device not in ('cpu', 'cuda') or type(epochs) is not int or not 1 <= epochs <= (3 if device == 'cpu' else 30):
        raise ValueError('Invalid bounded word training configuration')
    with torch.autocast(device_type=device, enabled=False):
        return _train(manifest, Path(output), device, epochs, deadline)


def _metrics(rows, threshold):
    known = [r for r in rows if r['target'] is not None]
    good = [r for r in known if r['target'] == 0]
    bad = [r for r in known if r['target'] == 1]
    tp = sum(r['score'] >= threshold for r in bad)
    fp = sum(r['score'] >= threshold for r in good)
    return {'known_words': len(known), 'unknown_words': len(rows) - len(known),
            'error_words': len(bad), 'correct_words': len(good), 'detected_errors': tp,
            'false_accepts': len(bad) - tp, 'false_alarms': fp,
            'recall': tp / len(bad) if bad else None,
            'false_alarm_rate': fp / len(good) if good else None,
            'precision': tp / (tp + fp) if tp + fp else None}


def _train(manifest, output, device, epochs, deadline):
    torch.set_num_threads(2); torch.manual_seed(42)
    generator = random.Random(42)
    deadline = time.monotonic() + 7100 if deadline is None else deadline
    output.mkdir(parents=True, exist_ok=True)
    rows, cache = validate_word_manifest(manifest, device)
    train = [r for r in rows if r['role'] == 'train']
    validation = [r for r in rows if r['role'] == 'validation']
    model = HumanWordHead().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001)

    def batch(group):
        xs = [cache[r['id']] for r in group]
        padded = nn.utils.rnn.pad_sequence(xs, batch_first=True).to(device)
        lengths = torch.tensor([len(x) for x in xs], dtype=torch.long)
        targets = torch.tensor([r['targets'] for r in group], dtype=torch.float32, device=device)
        mask = torch.tensor([r['mask'] for r in group], dtype=torch.bool, device=device)
        return padded, lengths, targets, mask

    def evaluate(group):
        model.eval(); total_loss = 0.; total_known = 0; predictions = []
        with torch.inference_mode():
            for offset in range(0, len(group), 16):
                check_resources(output, device, deadline)
                selected = group[offset:offset + 16]
                x, lengths, targets, mask = batch(selected)
                logits = model(x, lengths)
                loss = masked_word_loss(logits, targets, mask)
                count = int(mask.sum())
                total_loss += float(loss) * count; total_known += count
                probabilities = logits.sigmoid().cpu().tolist()
                for row, scores in zip(selected, probabilities):
                    start = OFFSETS[row['ayah']]
                    for i in range(len(REFERENCES[row['ayah']].split())):
                        slot = start + i
                        predictions.append({'case_id': row['id'], 'speaker_id': row['speaker_id'],
                                            'role': row['role'], 'ayah': row['ayah'], 'word_index': i,
                                            'slot': slot, 'score': scores[slot],
                                            'target': row['targets'][slot] if row['mask'][slot] else None})
        return total_loss / total_known, predictions

    history = []; best = math.inf; best_epoch = 0
    for epoch in range(1, epochs + 1):
        model.train(); generator.shuffle(train); loss_sum = 0.; known_sum = 0
        for offset in range(0, len(train), 16):
            check_resources(output, device, deadline)
            selected = train[offset:offset + 16]
            x, lengths, targets, mask = batch(selected)
            optimizer.zero_grad(set_to_none=True)
            loss = masked_word_loss(model(x, lengths), targets, mask)
            if not torch.isfinite(loss):
                raise ValueError('Nonfinite human word training loss')
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
            optimizer.step()
            if any(not torch.isfinite(p).all() for p in model.parameters()):
                raise ValueError('Nonfinite human word parameters')
            count = int(mask.sum()); loss_sum += float(loss.detach()) * count; known_sum += count
        val_loss, _ = evaluate(validation)
        improved = val_loss < best
        if improved:
            best, best_epoch = val_loss, epoch
            temporary = output / 'candidate-head.tmp.pt'
            torch.save({'state_dict': model.state_dict(), 'epoch': epoch,
                        'word_slots': REFERENCES, 'label_type': 'human_binary_word_error'}, temporary)
            temporary.replace(output / 'candidate-head.pt')
        history.append({'epoch': epoch, 'train_loss': loss_sum / known_sum,
                        'validation_loss': val_loss, 'best_epoch': best_epoch})
        print('HUMAN_WORD_EPOCH', history[-1], flush=True)
        if epoch >= 6 and epoch - best_epoch >= 6:
            break
    checkpoint = torch.load(output / 'candidate-head.pt', map_location=device, weights_only=True)
    model.load_state_dict(checkpoint['state_dict'], strict=True)
    _, validation_predictions = evaluate(validation)
    threshold = select_threshold([r for r in validation_predictions if r['target'] is not None])
    # Compare against a model which knows only selected word positions, never audio.
    priors = [(1 + sum(r['targets'][i] for r in train if r['mask'][i])) /
              (2 + sum(r['mask'][i] for r in train)) for i in range(15)]
    prior_val = [{**r, 'score': priors[r['slot']]} for r in validation_predictions if r['target'] is not None]
    prior_threshold = select_threshold(prior_val)
    summaries = {}; predictions = []
    for role in ('validation', 'test', 'reserved'):
        selected = [r for r in rows if r['role'] == role]
        if not selected:
            continue
        _, values = evaluate(selected)
        predictions.extend(values)
        summaries[role] = {'metrics': _metrics(values, threshold),
                           'text_prior_baseline': _metrics([{**r, 'score': priors[r['slot']]} for r in values], prior_threshold),
                           'per_ayah': {str(ayah): _metrics([r for r in values if r['ayah'] == ayah], threshold)
                                        for ayah in sorted({r['ayah'] for r in values})}}
    report = {'status': 'completed_narrow_human_word_experiment', 'qualified': False,
              'production_changed': False, 'encoder_frozen': True, 'user_audio_trained': False,
              'scope': 'Ikhlas only, contributor binary word labels; not phone diagnosis',
              'epochs_completed': len(history), 'best_epoch': best_epoch, 'best_validation_loss': best,
              'threshold': threshold, 'text_prior_threshold': prior_threshold,
              'head_sha256': file_sha(output / 'candidate-head.pt'),
              'split_clip_counts': {role: sum(r['role'] == role for r in rows) for role in ('train', 'validation', 'test', 'reserved')},
              'metrics': summaries, 'history': history,
              'limitations': ['One surah cannot qualify general Quran pronunciation grading',
                             'Unlisted words in error utterances have unknown correctness',
                             'Contributor labels not independently adjudicated',
                             'Word query identities restricted to 15 Ikhlas positions',
                             'Original encoder upstream training overlap unknown']}
    write_json(output / 'word-predictions.json', predictions)
    write_json(output / 'training-report.json', report)
    return report
