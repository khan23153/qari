"""Unqualified research-only word-local vowel assessment."""
import hashlib
import json
import math
from pathlib import Path
import random
import time

import numpy as np
import torch
from torch import nn

from ml.training.human_word_data import REFERENCES, parse_label_row, select_threshold
from ml.training.local_vowel_data import vowel_word_labels
from ml.training.kaggle_phoneme_job import check_resources, file_sha, write_json


class LocalVowelHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.project = nn.Sequential(nn.LayerNorm(1024), nn.Linear(1024, 128), nn.GELU())
        self.temporal = nn.Conv1d(128, 128, 5, padding=2, groups=128)
        self.context_norm = nn.LayerNorm(128)
        self.reference_embedding = nn.Embedding(43, 32, padding_idx=0)
        self.reference_encoder = nn.GRU(32, 32, bidirectional=True, batch_first=True)
        self.output = nn.Sequential(nn.LayerNorm(320), nn.Linear(320, 128), nn.GELU(),
                                    nn.Dropout(.1), nn.Linear(128, 1))

    def forward(self, features, lengths, reference_ids, reference_lengths):
        if (features.ndim != 3 or features.shape[2] != 1024 or not 1 <= len(features) <= 32
                or not 2 <= features.shape[1] <= 150 or not features.is_floating_point()
                or lengths.shape != (len(features),) or lengths.dtype != torch.long
                or (lengths < 2).any() or (lengths > features.shape[1]).any()
                or reference_ids.ndim != 2 or len(reference_ids) != len(features)
                or reference_ids.dtype != torch.long or not 1 <= reference_ids.shape[1] <= 64
                or reference_lengths.shape != lengths.shape or reference_lengths.dtype != torch.long
                or (reference_lengths < 1).any() or (reference_lengths > reference_ids.shape[1]).any()):
            raise ValueError('Invalid bounded word/reference tensors')
        valid = torch.arange(features.shape[1], device=features.device)[None] < lengths.to(features.device)[:, None]
        features = features.masked_fill(~valid[:, :, None], 0.)
        if not torch.isfinite(features).all():
            raise ValueError('Nonfinite real word features')
        x = self.project(features).masked_fill(~valid[:, :, None], 0.)
        x = self.context_norm(x + self.temporal(x.transpose(1, 2)).transpose(1, 2))
        mean = x.masked_fill(~valid[:, :, None], 0.).sum(1) / lengths.to(features.device)[:, None]
        maximum = x.masked_fill(~valid[:, :, None], -torch.inf).amax(1)
        ref_valid = (torch.arange(reference_ids.shape[1], device=reference_ids.device)[None]
                     < reference_lengths.to(reference_ids.device)[:, None])
        reference_ids = reference_ids.masked_fill(~ref_valid, 0)
        if ((reference_ids[ref_valid] < 1) | (reference_ids[ref_valid] > 42)).any():
            raise ValueError('Real reference must contain native nonblank phonemes')
        embedded = self.reference_embedding(reference_ids)
        packed = nn.utils.rnn.pack_padded_sequence(embedded, reference_lengths.cpu(),
                                                   batch_first=True, enforce_sorted=False)
        _, hidden = self.reference_encoder(packed)
        reference = torch.cat((hidden[-2], hidden[-1]), dim=-1)
        return self.output(torch.cat((mean, maximum, reference), dim=-1)).squeeze(-1)


def _json_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _is_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _require_kaggle_cpu(output=None):
    """Prevent accidental full CPU work on the VPS; not an authentication claim."""
    import platform
    roots = [Path('/kaggle/working'),Path('/kaggle/temp'),Path('/kaggle/input')]
    if (platform.system()!='Linux' or platform.machine().lower() not in ('x86_64','amd64')
            or not all(path.is_dir() for path in roots)
            or (output is not None and not Path(output).resolve().is_relative_to(roots[0].resolve()))):
        raise RuntimeError('Full CPU research requires explicit Kaggle context and working output')


def validate_local_vowel_manifest(manifest, device):
    if manifest.get('label_type') != 'human_vowel_word_error' or device not in ('cpu', 'cuda','kaggle_cpu'):
        raise ValueError('Explicit vowel-word research manifest required')
    if device=='kaggle_cpu':
        _require_kaggle_cpu()
    cases, sources = manifest['cases'], manifest['sources']
    if not 3 <= len(cases) <= (64 if device == 'cpu' else 7500) or not 3 <= len(sources) <= 1506:
        raise ValueError('Local vowel research manifest exceeds bounded size')
    identity = manifest['encoder_identity']
    if not identity or not _is_sha(identity.get('model_sha256')) or not _is_sha(identity.get('crop_implementation_sha256')):
        raise ValueError('Immutable encoder and crop identities required')
    crop_policy = manifest.get('crop_policy', 'exact_only_v1')
    if (crop_policy not in ('exact_only_v1','unique_substitution_v1')
            or crop_policy != identity.get('crop_policy','exact_only_v1')):
        raise ValueError('Local vowel crop policy differs from immutable feature identity')
    identity_sha = _json_sha(identity)
    references = manifest['references']
    reserved = set(manifest['reserved_speakers'])
    source_map, pcm_owners, speakers, labels = {}, {}, {}, {}
    for source in sources:
        source_id = source['id']
        if source_id in source_map or source.get('ayah') not in REFERENCES:
            raise ValueError('Duplicate or invalid source case')
        parsed = parse_label_row(dict(file_name=source['source_file'], verse_number=str(source['ayah']),
                                 verse_text=REFERENCES[source['ayah']], label_name=source['source_label'],
                                 label='1' if source['source_label'] == 'correct' else '0',
                                 error_type=source['source_error_type'], error_location=source['source_error_location']), reserved)
        if any(source[key] != parsed[key] for key in ('id', 'speaker_id', 'role', 'ayah', 'targets', 'mask')):
            raise ValueError('Source speaker split or binary word labels changed')
        pcm = source.get('float_pcm_sha256')
        if not _is_sha(pcm) or not _is_sha(source.get('source_sha256')) or pcm in pcm_owners:
            raise ValueError('Missing or duplicated actual source PCM')
        pcm_owners[pcm] = source_id
        if speakers.setdefault(source['speaker_id'], source['role']) != source['role']:
            raise ValueError('Speaker crosses training/held partitions')
        expected = references.get(str(source['ayah']))
        if (not isinstance(expected, list) or len(expected) != len(REFERENCES[source['ayah']].split())
                or any(not 1 <= len(ids) <= 64 or any(type(t) is not int or not 1 <= t <= 42 for t in ids)
                       for ids in expected)):
            raise ValueError('Original-word reference phonemes required')
        source_map[source_id] = source
        labels[source_id] = vowel_word_labels(source)
    known = {(source_id, r['word_index']) for source_id, values in labels.items()
             for r in values if r['target'] is not None}
    seen, ids, paths, rows, cache = set(), set(), set(), [], {}
    for case in cases:
        source_id, index = case['source_case_id'], case['word_index']
        if source_id not in source_map or type(index) is not int or not 0 <= index < len(labels[source_id]):
            raise ValueError('Unknown original word source')
        key = source_id, index
        if key in seen or case['id'] in ids or case['id'] != f'{source_id}:w{index}':
            raise ValueError('Duplicate or changed word identity')
        seen.add(key); ids.add(case['id'])
        source = source_map[source_id]
        target = labels[source_id][index]['target']
        if (case['target'] != target or (target is not None and type(case['target']) is not int)
                or case['reference_ids'] != references[str(source['ayah'])][index]
                or case.get('encoder_identity_sha256') != identity_sha
                or type(case['available']) is not bool):
            raise ValueError('Changed word supervision, reference or feature identity')
        row = {**case, 'role': source['role'], 'speaker_id': source['speaker_id'], 'ayah': source['ayah']}
        if case['available']:
            start, end = case['frame_start'], case['frame_end']
            if (type(start) is not int or type(end) is not int
                    or not 0 <= start < end <= source.get('encoder_frame_count', 600)
                    or not 2 <= end-start <= 150):
                raise ValueError('Word feature interval differs from native crop')
            path = Path(case['feature_path'])
            if str(path) in paths or file_sha(path) != case['feature_sha256']:
                raise ValueError('Word feature cache identity changed or reused')
            paths.add(str(path))
            with np.load(path, allow_pickle=False) as data:
                features = data['features']
            if features.dtype != np.float16 or features.shape != (end-start, 1024) or not np.isfinite(features).all():
                raise ValueError('Invalid native local acoustic features')
            cache[case['id']] = torch.from_numpy(features.astype(np.float32))
        elif (not isinstance(case.get('reason'), str) or not case['reason']
              or any(case.get(k) is not None for k in ('feature_path', 'feature_sha256', 'frame_start', 'frame_end'))):
            raise ValueError('Unavailable crop must have a reason and no fabricated features')
        rows.append(row)
    if not known.issubset(seen):
        raise ValueError('Missing supervised words would hide held coverage failures')
    if any(not any(r['role'] == role for r in rows) for role in ('train', 'validation', 'test')):
        raise ValueError('Disjoint train/validation/test word partitions required')
    return rows, cache


def _metrics(rows, threshold):
    known = [r for r in rows if r['target'] is not None]
    bad = [r for r in known if r['target'] == 1]
    good = [r for r in known if r['target'] == 0]
    detected = sum(r['score'] is not None and r['score'] >= threshold for r in bad)
    alarms = sum(r['score'] is not None and r['score'] >= threshold for r in good)
    unassessed_bad = sum(r['score'] is None for r in bad)
    return {'known_words': len(known), 'unknown_words': len(rows)-len(known),
            'error_words': len(bad), 'correct_words': len(good), 'detected_errors': detected,
            'false_accepts': len(bad)-detected-unassessed_bad, 'false_alarms': alarms,
            'unassessed_errors': unassessed_bad, 'unassessed_correct': sum(r['score'] is None for r in good),
            'recall': detected/len(bad) if bad else None,
            'precision': detected/(detected+alarms) if detected+alarms else None,
            'false_alarm_rate': alarms/len(good) if good else None,
            'assessed_coverage': sum(r['score'] is not None for r in known)/len(known) if known else 0.}


def train_local_vowel_features(manifest, output, device='cpu', epochs=30, deadline=None):
    if device not in ('cpu', 'cuda','kaggle_cpu') or type(epochs) is not int or not 1 <= epochs <= (3 if device == 'cpu' else 30):
        raise ValueError('Bounded local vowel training configuration required')
    if device=='kaggle_cpu':
        _require_kaggle_cpu(output)
    actual_device='cpu' if device=='kaggle_cpu' else device
    with torch.autocast(device_type=actual_device, enabled=False):
        return _train(manifest, Path(output), actual_device, epochs, deadline,execution_scope=device)


def _train(manifest, output, device, epochs, deadline, *, execution_scope=None):
    execution_scope=execution_scope or device
    torch.set_num_threads(2); torch.manual_seed(42)
    generator = random.Random(42)
    deadline = time.monotonic()+7100 if deadline is None else deadline
    output.mkdir(parents=True, exist_ok=True)
    rows, cache = validate_local_vowel_manifest(manifest, execution_scope)
    train = [r for r in rows if r['role'] == 'train' and r['available'] and r['target'] is not None]
    validation = [r for r in rows if r['role'] == 'validation']
    positives = sum(r['target'] == 1 for r in train)
    negatives = sum(r['target'] == 0 for r in train)
    if not positives or not negatives:
        raise ValueError('Both eligible training label classes required')
    positive_weight = negatives/positives
    model = LocalVowelHead().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001)
    weight = torch.tensor(positive_weight, device=device)

    def batch(selected):
        xs = [cache[r['id']] for r in selected]
        refs = [torch.tensor(r['reference_ids'], dtype=torch.long) for r in selected]
        return (nn.utils.rnn.pad_sequence(xs, batch_first=True).to(device),
                torch.tensor([len(x) for x in xs], dtype=torch.long),
                nn.utils.rnn.pad_sequence(refs, batch_first=True).to(device),
                torch.tensor([len(x) for x in refs], dtype=torch.long))

    def evaluate(group):
        model.eval(); scores = {}; loss_sum = 0.; count = 0
        eligible = [r for r in group if r['available']]
        with torch.inference_mode():
            for offset in range(0, len(eligible), 16):
                check_resources(output, execution_scope, deadline)
                selected = eligible[offset:offset+16]
                logits = model(*batch(selected))
                if not torch.isfinite(logits).all():
                    raise ValueError('Nonfinite local vowel evaluation')
                for row, probability, logit in zip(selected, logits.sigmoid().tolist(), logits):
                    scores[row['id']] = probability
                    if row['target'] is not None:
                        loss = nn.functional.binary_cross_entropy_with_logits(logit, logit.new_tensor(row['target']))
                        loss_sum += float(loss); count += 1
        values = [{'case_id': r['id'], 'source_case_id': r['source_case_id'], 'role': r['role'],
                   'ayah': r['ayah'], 'word_index': r['word_index'], 'target': r['target'],
                   'reference_ids': r['reference_ids'], 'score': scores.get(r['id']),
                   'pronunciation_status': 'unassessed'} for r in group]
        return loss_sum/count if count else None, values

    history = []; best = math.inf; best_epoch = 0
    for epoch in range(1, epochs+1):
        model.train(); generator.shuffle(train); total = 0.
        for offset in range(0, len(train), 16):
            check_resources(output, execution_scope, deadline)
            selected = train[offset:offset+16]
            targets = torch.tensor([r['target'] for r in selected], dtype=torch.float32, device=device)
            optimizer.zero_grad(set_to_none=True)
            loss = nn.functional.binary_cross_entropy_with_logits(model(*batch(selected)), targets, pos_weight=weight)
            if not torch.isfinite(loss):
                raise ValueError('Nonfinite local vowel training loss')
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
            optimizer.step()
            if any(not torch.isfinite(p).all() for p in model.parameters()):
                raise ValueError('Nonfinite local vowel parameters')
            total += float(loss.detach())*len(selected)
        val_loss, _ = evaluate(validation)
        if val_loss is None or not math.isfinite(val_loss):
            raise ValueError('Finite eligible validation supervision required')
        if val_loss < best:
            best, best_epoch = val_loss, epoch
            temporary = output/'candidate-head.tmp.pt'
            torch.save({'state_dict': model.state_dict(), 'epoch': epoch,
                        'label_type': 'human_vowel_word_error', 'encoder_identity': manifest['encoder_identity'],
                        'references_sha256': _json_sha(manifest['references'])}, temporary)
            temporary.replace(output/'candidate-head.pt')
        history.append({'epoch': epoch, 'train_loss': total/len(train), 'validation_loss': val_loss,
                        'best_epoch': best_epoch})
        print('LOCAL_VOWEL_EPOCH', history[-1], flush=True)
        if epoch >= 6 and epoch-best_epoch >= 6:
            break
    checkpoint = torch.load(output/'candidate-head.pt', map_location=device, weights_only=True)
    model.load_state_dict(checkpoint['state_dict'], strict=True)
    _, val_predictions = evaluate(validation)
    threshold = select_threshold([r for r in val_predictions if r['target'] is not None and r['score'] is not None])
    prior_counts = {}
    for row in train:
        key = tuple(row['reference_ids'])
        positive, count = prior_counts.get(key, (1, 2))
        prior_counts[key] = positive+row['target'], count+1
    def prior_scores(group):
        return [{**r, 'score': (lambda pair: pair[0]/pair[1])(prior_counts.get(tuple(r['reference_ids']), (1, 2)))}
                for r in group]
    prior_threshold = select_threshold([r for r in prior_scores(val_predictions) if r['target'] is not None])
    metrics, baselines, predictions = {}, {}, []
    for role in ('validation', 'test', 'reserved'):
        group = [r for r in rows if r['role'] == role]
        if not group:
            continue
        _, values = evaluate(group)
        metrics[role] = _metrics(values, threshold)
        baselines[role] = _metrics(prior_scores(values), prior_threshold)
        predictions.extend(values)
    report = {'status': 'completed_narrow_local_vowel_experiment', 'qualified': False,
              'device':device,'execution_scope':execution_scope,
              'production_changed': False, 'epochs_completed': len(history), 'best_epoch': best_epoch,
              'threshold': threshold, 'text_prior_threshold': prior_threshold,
              'training_positive_weight': positive_weight, 'eligible_training_positive': positives,
              'eligible_training_negative': negatives, 'metrics': metrics,
              'text_prior_baseline': baselines, 'history': history,
              'head_sha256': file_sha(output/'candidate-head.pt'),
              'limitations': ['One-surah contributor vowel-word labels, not heard-phone annotations',
                             'Native local crops and full-context encoder do not establish streaming accuracy',
                             'Missing crops remain unassessed; unknown labels never become negatives',
                             'Original encoder upstream training overlap unknown']}
    write_json(output/'training-report.json', report)
    write_json(output/'word-predictions.json', predictions)
    return report
