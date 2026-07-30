from types import SimpleNamespace

import pytest

from ml.training.finetune_whisper import (
    configure_whisper_model,
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
