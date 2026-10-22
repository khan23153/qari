import copy
import hashlib
import json

import numpy as np
import pytest
import torch

from ml.training.human_word_data import parse_label_row
from ml.training.human_word_head import HumanWordHead, masked_word_loss, train_word_features, validate_word_manifest


def manifest(tmp_path):
    cases = []
    counts = {'train': 0, 'validation': 0, 'test': 0}
    for speaker in range(1000, 1200):
        row = dict(file_name=f'data/ID{speaker}V1T.wav', label='1', label_name='correct',
                   verse_number='1', verse_text='قُلْ هُوَ اللَّهُ أَحَدٌ',
                   error_location='', error_type='', error_explanation='')
        parsed = parse_label_row(row, set())
        role = parsed['role']
        if role not in counts or counts[role] >= 2:
            continue
        if counts[role] == 1:
            row.update(file_name=f'data/ID{speaker}V1F.wav', label='0', label_name='error',
                       error_location='قُلْ', error_type='حركات')
            parsed = parse_label_row(row, set())
        counts[role] += 1
        x = np.random.default_rng(speaker).normal(0, .2, (16, 512)).astype(np.float16)
        x[:, :32] += parsed['targets'][0]
        path = tmp_path / (parsed['id'] + '.npz')
        np.savez_compressed(path, features=x)
        cases.append({**parsed, 'feature_path': str(path), 'feature_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'float_pcm_sha256': hashlib.sha256(str(speaker).encode()).hexdigest(), 'sample_count': 5120})
        if all(n == 2 for n in counts.values()):
            break
    return {'label_type': 'human_binary_word_error', 'reserved_speakers': [], 'cases': cases}


def test_padding_peer_and_poisoned_tail_do_not_change_word_logits():
    torch.manual_seed(3)
    head = HumanWordHead().eval()
    real = torch.randn(1, 17, 512)
    alone = head(real, torch.tensor([17]))
    peers = torch.randn(2, 41, 512)
    peers[0, :17] = real[0]
    peers[0, 17:] = float('nan')
    batched = head(peers, torch.tensor([17, 41]))
    torch.testing.assert_close(alone[0], batched[0], atol=1e-5, rtol=1e-5)
    assert not torch.allclose(alone, head(-real, torch.tensor([17])))


def test_unknown_word_logits_have_no_loss_or_gradient():
    logits = torch.zeros(1, 15, requires_grad=True)
    targets = torch.zeros(1, 15)
    mask = torch.zeros(1, 15, dtype=torch.bool)
    mask[0, 0] = True
    loss = masked_word_loss(logits, targets, mask)
    loss.backward()
    assert loss.item() == pytest.approx(.69314718)
    assert logits.grad[0, 0].item() == pytest.approx(.5)
    assert logits.grad[0, 1:].abs().sum().item() == 0
    poisoned = logits.detach().clone(); poisoned[0, 1:] = 1000.
    assert masked_word_loss(poisoned, targets, mask).item() == pytest.approx(loss.item())


def test_finite_gradients_on_variable_length_word_batches():
    head = HumanWordHead()
    logits = head(torch.randn(2, 21, 512), torch.tensor([13, 21]))
    loss = masked_word_loss(logits, torch.zeros_like(logits), torch.ones_like(logits, dtype=torch.bool))
    loss.backward()
    norm = torch.nn.utils.clip_grad_norm_(head.parameters(), 1., error_if_nonfinite=True)
    assert torch.isfinite(norm) and norm > 0


@pytest.mark.parametrize('change', ['pcm', 'speaker', 'feature_sha', 'word_mask'])
def test_manifest_rejects_audio_speaker_and_label_leakage(tmp_path, change):
    data = manifest(tmp_path)
    left, right = data['cases'][0], next(r for r in data['cases'] if r['role'] != data['cases'][0]['role'])
    if change == 'pcm': right['float_pcm_sha256'] = left['float_pcm_sha256']
    if change == 'speaker': right['speaker_id'] = left['speaker_id']
    if change == 'feature_sha': right['feature_sha256'] = '0' * 64
    if change == 'word_mask': right['mask'][14] = 1
    with pytest.raises(ValueError):
        validate_word_manifest(data, 'cpu')


def test_test_labels_cannot_change_checkpoint_or_threshold(tmp_path):
    data = manifest(tmp_path)
    out1, out2 = tmp_path / 'first', tmp_path / 'second'
    first = train_word_features(data, out1, device='cpu', epochs=1)
    altered = copy.deepcopy(data)
    # A test utterance retains a legal positive source annotation, but at another word.
    for r in altered['cases']:
        if r['role'] == 'test' and r['source_label'] == 'error':
            r['targets'] = [0, 1] + [0] * 13
            r['mask'] = [0, 1] + [0] * 13
            r['source_error_location'] = 'هُوَ'
    second = train_word_features(altered, out2, device='cpu', epochs=1)
    a = torch.load(out1 / 'candidate-head.pt', weights_only=True)['state_dict']
    b = torch.load(out2 / 'candidate-head.pt', weights_only=True)['state_dict']
    assert first['threshold'] == second['threshold']
    for name in a:
        assert torch.equal(a[name], b[name])
    assert first['qualified'] is False and first['production_changed'] is False
    assert first['epochs_completed'] == 1


def test_nonfinite_real_frames_fail_before_optimization():
    with pytest.raises(ValueError):
        HumanWordHead()(torch.full((1, 16, 512), float('nan')), torch.tensor([16]))
