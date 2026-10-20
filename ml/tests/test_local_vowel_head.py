import copy
import hashlib
import json
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ml.training.human_word_data import parse_label_row
from ml.training.local_vowel_data import vowel_word_labels
from ml.training.local_vowel_head import (
    LocalVowelHead, train_local_vowel_features, validate_local_vowel_manifest,
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample_manifest(tmp_path, per_role=2):
    sources, cases = [], []
    counts = {'train': 0, 'validation': 0, 'test': 0}
    references = {'1': [[21, 33, 23], [26, 33, 27, 32],
                        [23, 23, 32, 29, 29, 26, 33], [1, 32, 6, 32, 8, 38]]}
    identity = {'model_sha256': '6' * 64, 'crop_implementation_sha256': '7' * 64}
    identity_sha = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    for speaker in range(1000, 1200):
        raw = dict(file_name=f'data/ID{speaker}V1T.wav', label='1', label_name='correct',
                   verse_number='1', verse_text='قُلْ هُوَ اللَّهُ أَحَدٌ',
                   error_location='', error_type='', error_explanation='')
        source = parse_label_row(raw, set())
        role = source['role']
        if counts[role] >= per_role:
            continue
        if counts[role] == 1:
            raw.update(file_name=f'data/ID{speaker}V1F.wav', label='0', label_name='error',
                       error_location='قُلْ', error_type='حركات')
            source = parse_label_row(raw, set())
        counts[role] += 1
        source.update(float_pcm_sha256=hashlib.sha256(str(speaker).encode()).hexdigest(),
                      source_sha256=hashlib.sha256(('source:' + str(speaker)).encode()).hexdigest())
        sources.append(source)
        for label in vowel_word_labels(source):
            if label['target'] is None:
                continue
            index = label['word_index']
            features = np.random.default_rng(speaker*10+index).normal(0, .2, (13, 1024)).astype(np.float16)
            features[:, :32] += label['target']
            path = tmp_path / (source['id'] + '-' + str(index) + '.npz')
            np.savez_compressed(path, features=features)
            cases.append({'id': f'{source["id"]}:w{index}', 'source_case_id': source['id'],
                          'word_index': index, 'target': label['target'],
                          'reference_ids': references['1'][index], 'available': True,
                          'frame_start': index*16, 'frame_end': index*16+13,
                          'feature_path': str(path), 'feature_sha256': digest(path),
                          'encoder_identity_sha256': identity_sha})
        if all(n == per_role for n in counts.values()):
            break
    return {'label_type': 'human_vowel_word_error', 'reserved_speakers': [],
            'encoder_identity': identity, 'references': references,
            'sources': sources, 'cases': cases}


def test_poisoned_padding_and_longer_peers_cannot_change_a_real_word():
    torch.manual_seed(3)
    model = LocalVowelHead().eval()
    features = torch.randn(1, 13, 1024)
    reference = torch.tensor([[21, 33, 23]])
    alone = model(features, torch.tensor([13]), reference, torch.tensor([3]))
    batch = torch.randn(2, 31, 1024)
    batch[0, :13] = features[0]; batch[0, 13:] = float('nan')
    refs = torch.tensor([[21, 33, 23, 99, 99], [26, 33, 27, 32, 26]])
    together = model(batch, torch.tensor([13, 31]), refs, torch.tensor([3, 5]))
    torch.testing.assert_close(alone[0], together[0], atol=1e-5, rtol=1e-5)
    assert not torch.allclose(alone, model(-features, torch.tensor([13]), reference, torch.tensor([3])))


def test_real_nonfinite_features_or_blank_reference_cannot_be_scored():
    model = LocalVowelHead()
    with pytest.raises(ValueError):
        model(torch.full((1, 13, 1024), float('nan')), torch.tensor([13]),
              torch.tensor([[21, 33, 23]]), torch.tensor([3]))
    with pytest.raises(ValueError):
        model(torch.zeros(1, 13, 1024), torch.tensor([13]), torch.tensor([[21, 0, 23]]), torch.tensor([3]))


def test_variable_word_and_reference_lengths_have_finite_gradients():
    model = LocalVowelHead()
    logits = model(torch.randn(2, 21, 1024), torch.tensor([13, 21]),
                   torch.tensor([[21, 33, 23, 0], [26, 33, 27, 32]]), torch.tensor([3, 4]))
    assert logits.shape == (2,)
    torch.nn.functional.binary_cross_entropy_with_logits(logits, torch.tensor([0., 1.])).backward()
    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
    assert torch.isfinite(norm) and norm > 0


@pytest.mark.parametrize('case',['valid','arm_vps','missing_kaggle_path','outside_output'])
def test_remote_full_cpu_requires_explicit_kaggle_context_and_output(monkeypatch,case):
    import platform
    from ml.training.local_vowel_head import _require_kaggle_cpu
    monkeypatch.setattr(platform,'system',lambda:'Linux')
    monkeypatch.setattr(platform,'machine',lambda:'aarch64' if case=='arm_vps' else 'x86_64')
    real_is_dir=Path.is_dir
    def is_dir(path):
        if str(path) in ('/kaggle/working','/kaggle/temp','/kaggle/input'):
            return not (case=='missing_kaggle_path' and str(path)=='/kaggle/input')
        return real_is_dir(path)
    monkeypatch.setattr(Path,'is_dir',is_dir)
    output=Path('/tmp/output') if case=='outside_output' else Path('/kaggle/working/run')
    if case=='valid':_require_kaggle_cpu(output)
    else:
        with pytest.raises(RuntimeError,match='Kaggle'):_require_kaggle_cpu(output)


def test_only_explicit_remote_cpu_can_train_75_words_four_epochs(tmp_path,monkeypatch):
    import shutil
    from ml.training import local_vowel_head as module
    manifest=sample_manifest(tmp_path,per_role=7)
    assert len(manifest['cases'])==75
    with pytest.raises(ValueError,match='bounded size'):
        validate_local_vowel_manifest(manifest,'cpu')
    with pytest.raises(ValueError,match='configuration'):
        train_local_vowel_features(manifest,tmp_path/'local',device='cpu',epochs=4)
    # Platform/filesystem checks are tested above; this test isolates training bounds.
    monkeypatch.setattr(module,'_require_kaggle_cpu',lambda output=None:None)
    monkeypatch.setattr(shutil,'disk_usage',lambda _:SimpleNamespace(free=8*1024**3))
    monkeypatch.setattr(torch.cuda,'mem_get_info',lambda:pytest.fail('Remote CPU called CUDA'))
    report=train_local_vowel_features(manifest,tmp_path/'remote',device='kaggle_cpu',epochs=4,
                                      deadline=time.monotonic()+30)
    assert report['device']=='cpu' and report['execution_scope']=='kaggle_cpu'
    assert report['epochs_completed']==4 and not report['qualified']
    assert all(np.isfinite(r['train_loss']) and np.isfinite(r['validation_loss']) for r in report['history'])


@pytest.mark.parametrize('change', ['pcm', 'speaker', 'feature_sha', 'target', 'reference', 'encoder',
                                   'omitted_held_word', 'policy_mismatch', 'unknown_policy'])
def test_manifest_rejects_leakage_changed_evidence_and_missing_held_labels(tmp_path, change):
    manifest = sample_manifest(tmp_path)
    source = manifest['sources'][0]
    other = next(r for r in manifest['sources'] if r['role'] != source['role'])
    row = manifest['cases'][0]
    if change == 'pcm': other['float_pcm_sha256'] = source['float_pcm_sha256']
    if change == 'speaker': other['speaker_id'] = source['speaker_id']
    if change == 'feature_sha': row['feature_sha256'] = '0' * 64
    if change == 'target': row['target'] = 1 - row['target']
    if change == 'reference': row['reference_ids'] = [1, 32, 6]
    if change == 'encoder': row['encoder_identity_sha256'] = '0' * 64
    if change == 'policy_mismatch': manifest['crop_policy'] = 'unique_substitution_v1'
    if change == 'unknown_policy': manifest['crop_policy'] = 'accept_all'
    if change == 'omitted_held_word':
        held = next(r for r in manifest['sources'] if r['role'] == 'test' and r['source_label'] == 'error')
        manifest['cases'] = [r for r in manifest['cases'] if r['source_case_id'] != held['id']]
    with pytest.raises(ValueError):
        validate_local_vowel_manifest(manifest, 'cpu')


def test_unavailable_held_error_stays_in_support_and_coverage(tmp_path):
    manifest = sample_manifest(tmp_path)
    held = next(s for s in manifest['sources'] if s['role'] == 'test' and s['source_label'] == 'error')
    row = next(r for r in manifest['cases'] if r['source_case_id'] == held['id'])
    row.update(available=False, reason='ambiguous_native_anchors', feature_path=None,
               feature_sha256=None, frame_start=None, frame_end=None)
    report = train_local_vowel_features(manifest, tmp_path/'out', device='cpu', epochs=1)
    test = report['metrics']['test']
    assert test['error_words'] == 1 and test['unassessed_errors'] == 1
    assert test['detected_errors'] == 0 and test['assessed_coverage'] == pytest.approx(.8)
    assert report['qualified'] is False and report['production_changed'] is False


def test_held_availability_never_selects_checkpoint_or_threshold(tmp_path):
    manifest = sample_manifest(tmp_path)
    first = train_local_vowel_features(manifest, tmp_path/'one', device='cpu', epochs=1)
    changed = copy.deepcopy(manifest)
    held_ids = {s['id'] for s in changed['sources'] if s['role'] == 'test'}
    for row in changed['cases']:
        if row['source_case_id'] in held_ids:
            row.update(available=False, reason='unavailable_control', feature_path=None,
                       feature_sha256=None, frame_start=None, frame_end=None)
    second = train_local_vowel_features(changed, tmp_path/'two', device='cpu', epochs=1)
    assert first['threshold'] == second['threshold']
    left = torch.load(tmp_path/'one/candidate-head.pt', weights_only=True)['state_dict']
    right = torch.load(tmp_path/'two/candidate-head.pt', weights_only=True)['state_dict']
    assert all(torch.equal(left[k], right[k]) for k in left)
