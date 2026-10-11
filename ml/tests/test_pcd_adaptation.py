import pytest
import torch


def _model():
    model = torch.nn.Linear(1, 1, bias=False)
    with torch.no_grad():
        model.weight.zero_()
    return model, torch.optim.SGD(model.parameters(), lr=1.0)


def _loss(model, size, target):
    return (model(torch.ones(size, 1)) - target).square().mean()


def test_partial_accumulation_averages_actual_samples_including_last_small_batch():
    from ml.training.pcd_adaptation import SampleGradientAccumulator
    model, optimizer = _model()
    accumulation = SampleGradientAccumulator(model, optimizer, microbatches=4, clip_norm=100)
    accumulation.backward(_loss(model, 2, 1), 2)
    accumulation.backward(_loss(model, 1, 3), 1)
    assert model.weight.item() == 0
    accumulation.flush()
    # Independent gradients: (-2 * 2 - 6 * 1) / 3 = -10/3.
    assert model.weight.item() == pytest.approx(10 / 3)


def test_full_accumulation_steps_after_four_microbatches():
    from ml.training.pcd_adaptation import SampleGradientAccumulator
    model, optimizer = _model()
    accumulation = SampleGradientAccumulator(model, optimizer, microbatches=4, clip_norm=100)
    for _ in range(3):
        accumulation.backward(_loss(model, 2, 1), 2)
        assert model.weight.item() == 0
    accumulation.backward(_loss(model, 2, 1), 2)
    assert model.weight.item() == pytest.approx(2)


def test_repeated_empty_flush_does_not_apply_stale_gradients():
    from ml.training.pcd_adaptation import SampleGradientAccumulator
    model, optimizer = _model()
    accumulation = SampleGradientAccumulator(model, optimizer, microbatches=4, clip_norm=100)
    accumulation.backward(_loss(model, 1, 1), 1)
    accumulation.flush()
    accumulation.flush()
    assert model.weight.item() == pytest.approx(2)


def test_nonfinite_loss_cannot_create_an_optimizer_update():
    from ml.training.pcd_adaptation import SampleGradientAccumulator
    model, optimizer = _model()
    accumulation = SampleGradientAccumulator(model, optimizer, microbatches=4)
    with pytest.raises(ValueError, match='finite'):
        accumulation.backward(_loss(model, 1, float('nan')), 1)
    accumulation.flush()
    assert model.weight.item() == 0


def test_filename_inferred_label_cannot_enter_native_training_even_with_verified_flag():
    from ml.training.pcd_adaptation import require_curated_sources
    with pytest.raises(ValueError, match='label'):
        require_curated_sources([{'source':'tlog_clean_bucket','speaker_id':'train',
                                 'label_verified':True}],
                                [{'source':'retasy_correct','speaker_id':'eval'}])


def test_native_evaluation_cannot_use_augmented_clips():
    from ml.training.pcd_adaptation import require_curated_sources
    with pytest.raises(ValueError, match='evaluation'):
        require_curated_sources([{'source':'retasy_correct','speaker_id':'train'}],
                                [{'source':'retasy_phase3_aug','speaker_id':'eval'}])


def test_curated_native_splits_reject_shared_speaker_identity():
    from ml.training.pcd_adaptation import require_curated_sources
    with pytest.raises(ValueError, match='speaker'):
        require_curated_sources([{'source':'retasy_correct','speaker_id':'same'}],
                                [{'source':'retasy_correct','speaker_id':'same'}])


def test_clean_curated_speech_and_its_augmentations_remain_usable():
    from ml.training.pcd_adaptation import require_curated_sources
    require_curated_sources([{'source':'retasy_correct','speaker_id':'train'},
                             {'source':'retasy_phase3_aug','speaker_id':'train'}],
                            [{'source':'retasy_correct','speaker_id':'eval'}])
