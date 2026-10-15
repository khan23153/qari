"""Resume differentiable training after evaluation expands an inference cache."""


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
