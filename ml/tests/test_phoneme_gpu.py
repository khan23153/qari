"""Leakage and padding must not create apparent pronunciation improvements."""
import pytest
import torch


def source(voice='Amer', text='قُلْ هُوَ اللَّهُ أَحَدٌ'):
    return {'speaker': voice, 'sentence_ref': text, 'sentence_aug': 'altered speech',
            'label': 'augmented', 'phoneme_mis': 'q a l h u w a',
            'phoneme_ref': 'q u l h u w a'}


def test_reference_group_ignores_diacritics_and_presentation_variants():
    from ml.training.phoneme_gpu import reference_group
    assert reference_group('ٱللَّهُ   أَحَدٌ') == reference_group('الله احد')
    assert reference_group('بِسْمِ اللَّهِ') == reference_group('بسم ﷲ')
    assert reference_group('عَلِيمٌ') != reference_group('عالم')


@pytest.mark.parametrize('text', ['', '   ', None, 'َُِ'])
def test_reference_group_requires_real_content(text):
    from ml.training.phoneme_gpu import reference_group
    with pytest.raises(ValueError):
        reference_group(text)


def test_held_voice_and_reference_groups_never_train():
    from ml.training.phoneme_gpu import source_role, reference_group
    train_refs, validation_refs = set(), set()
    for i in range(200):
        text = 'مرجع رقم ' + str(i)
        for voice in ['Amer', 'Nabil', 'Jessica']:
            row = source(voice, text);role = source_role(row)
            if role == 'train':
                assert voice != 'Jessica';train_refs.add(reference_group(text))
            elif role == 'validation':
                assert voice == 'Jessica';validation_refs.add(reference_group(text))
            else:
                assert role is None
    assert len(train_refs) > 100 and len(validation_refs) > 10
    assert not train_refs & validation_refs


@pytest.mark.parametrize('change', [{'speaker': ''}, {'phoneme_mis': ''},
                                   {'label': 'original'}, {'sentence_aug': ''}])
def test_source_role_rejects_missing_altered_speech_truth(change):
    from ml.training.phoneme_gpu import source_role
    with pytest.raises(ValueError):
        source_role(source() | change)


def test_temporal_head_real_frames_are_invariant_to_padding_and_batch_peers():
    from ml.training.phoneme_gpu import TemporalPhoneHead
    torch.manual_seed(29);head = TemporalPhoneHead(12).eval()
    short = torch.randn(1, 9, 512)
    batch = torch.randn(2, 21, 512) * 2000
    batch[0, :9] = short[0]
    with torch.inference_mode():
        solo = head(short, torch.tensor([9]))
        padded = head(batch, torch.tensor([9, 21]))
    torch.testing.assert_close(solo[0], padded[0, :9], atol=1e-5, rtol=1e-4)
    assert torch.count_nonzero(padded[0, 9:]) == 0


def test_temporal_head_has_finite_ctc_gradients_on_real_frames():
    from ml.training.phoneme_gpu import TemporalPhoneHead
    head = TemporalPhoneHead(5)
    lengths = torch.tensor([20, 17]);features = torch.randn(2, 20, 512)
    logits = head(features, lengths)
    loss = torch.nn.CTCLoss(blank=0, zero_infinity=False)(
        logits.log_softmax(-1).transpose(0, 1), torch.tensor([1, 1, 2, 3, 4]),
        lengths, torch.tensor([3, 2]))
    assert torch.isfinite(loss)
    loss.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in head.parameters())


@pytest.mark.parametrize('shape,lengths', [((1, 5, 511), [5]), ((1, 5, 512), [0]),
                                        ((1, 5, 512), [6]), ((2, 5, 512), [5])])
def test_temporal_head_rejects_invalid_feature_lengths(shape, lengths):
    from ml.training.phoneme_gpu import TemporalPhoneHead
    with pytest.raises(ValueError):
        TemporalPhoneHead(5)(torch.zeros(shape), torch.tensor(lengths))


def test_temporal_head_rejects_nonfinite_acoustic_features():
    from ml.training.phoneme_gpu import TemporalPhoneHead
    features = torch.zeros(1, 8, 512);features[0, 4, 3] = float('nan')
    with pytest.raises(ValueError):
        TemporalPhoneHead(5)(features, torch.tensor([8]))
