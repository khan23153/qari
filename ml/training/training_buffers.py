"""Resume differentiable training after evaluation expands an inference cache."""


def release_completed_optimizer(optimizer) -> None:
    """Discard completed training state before memory-heavy evaluation.

    Adam moments can retain twice the trainable model's parameter memory even
    after gradients are cleared. Call only after the final update: this also
    discards optimizer history, so further training would start fresh.
    Model parameters and their learned values remain intact.
    """
    optimizer.zero_grad(set_to_none=True)
    optimizer.state.clear()


def restore_training_buffers(model) -> None:
    """Clone inference-created buffers into ordinary tensors, retaining aliases.

    NeMo's relative-position cache can grow under inference_mode during a long
    validation decode. Its later linear projection needs an ordinary tensor to
    save for backward. Values, parameters, buffer persistence and normal buffers
    remain unchanged. This helper belongs at the evaluation-to-training boundary.
    """
    import torch

    replacements = {}
    with torch.inference_mode(False):
        for module in model.modules():
            for name, buffer in module.named_buffers(recurse=False, remove_duplicate=False):
                if torch.is_inference(buffer):
                    key = id(buffer)
                    if key not in replacements:
                        replacements[key] = buffer.clone()
                    setattr(module, name, replacements[key])
