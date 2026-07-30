from types import SimpleNamespace

import pytest

from ml.training.finetune_whisper import (
    configure_whisper_model,
    create_dataset,
    resolve_resume_checkpoint,
)


def test_auto_resume_selects_highest_numeric_checkpoint(tmp_path):
    (tmp_path / "checkpoint-20").mkdir()
    (tmp_path / "checkpoint-100").mkdir()
    (tmp_path / "checkpoint-invalid").mkdir()

    assert resolve_resume_checkpoint("auto", str(tmp_path)) == str(
        tmp_path / "checkpoint-100"
    )


def test_auto_resume_fails_when_no_checkpoint_exists(tmp_path):
    with pytest.raises(FileNotFoundError, match="No checkpoint"):
        resolve_resume_checkpoint("auto", str(tmp_path))


def test_configure_whisper_preserves_suppression_tokens():
    model = SimpleNamespace(
        config=SimpleNamespace(forced_decoder_ids=None, suppress_tokens=[1, 2]),
        generation_config=SimpleNamespace(
            forced_decoder_ids=None,
            suppress_tokens=[3, 4],
        ),
    )
    processor = SimpleNamespace(
        get_decoder_prompt_ids=lambda **kwargs: [[1, 42]],
    )

    configure_whisper_model(model, processor, "ar")

    assert model.config.forced_decoder_ids == [[1, 42]]
    assert model.generation_config.forced_decoder_ids == [[1, 42]]
    assert model.config.suppress_tokens == [1, 2]
    assert model.generation_config.suppress_tokens == [3, 4]


def test_create_dataset_can_limit_smoke_run_without_rewriting_manifest(tmp_path):
    entries = [
        {"audio_path": f"audio/{index}.wav", "text": str(index)}
        for index in range(1000)
    ]

    train, evaluation = create_dataset(
        entries,
        str(tmp_path),
        eval_split=0.1,
        max_samples=300,
    )

    assert len(train) == 270
    assert len(evaluation) == 30
    assert all(entry["audio_path"].startswith(str(tmp_path)) for entry in train)


def test_create_dataset_rejects_negative_sample_limit(tmp_path):
    with pytest.raises(ValueError, match="max_samples"):
        create_dataset(
            [{"audio_path": "one.wav"}, {"audio_path": "two.wav"}],
            str(tmp_path),
            max_samples=-1,
        )
