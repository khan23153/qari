"""Sample-weighted gradients for independently evaluated ASR adaptation."""
from __future__ import annotations

import torch


class SampleGradientAccumulator:
    """Average actual samples, including a short final microbatch/group."""

    def __init__(self, model, optimizer, *, microbatches=4, clip_norm=1.0):
        if microbatches < 1 or clip_norm <= 0:
            raise ValueError('Positive accumulation and clipping limits required')
        self.model = model
        self.optimizer = optimizer
        self.microbatches = microbatches
        self.clip_norm = clip_norm
        self.count = 0
        self.samples = 0
        self.optimizer.zero_grad(set_to_none=True)

    def backward(self, mean_loss, batch_size):
        if batch_size < 1 or mean_loss.numel() != 1 or not torch.isfinite(mean_loss):
            raise ValueError('A finite scalar loss and positive batch size are required')
        (mean_loss * batch_size).backward()
        self.count += 1
        self.samples += batch_size
        if self.count >= self.microbatches:
            return self.flush()
        return None

    def flush(self):
        if not self.samples:
            return None
        for parameter in self.model.parameters():
            if parameter.grad is not None:
                if not torch.isfinite(parameter.grad).all():
                    raise ValueError('Non-finite accumulated gradient')
                parameter.grad.div_(self.samples)
        norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.clip_norm)
        if not torch.isfinite(norm):
            raise ValueError('Non-finite gradient norm')
        self.optimizer.step()
        result = {'samples': self.samples, 'microbatches': self.count,
                  'gradient_norm_before_clip': float(norm)}
        self.optimizer.zero_grad(set_to_none=True)
        self.samples = self.count = 0
        return result


def require_curated_sources(train, evaluation):
    """Refuse the known filename-label source before loading training weights."""
    if not train or any(r.get('source') not in {'retasy_correct', 'retasy_phase3_aug'}
                        for r in train):
        raise ValueError('Native adaptation requires curated spoken labels')
    if not evaluation or any(r.get('source') != 'retasy_correct' for r in evaluation):
        raise ValueError('Native evaluation requires clean curated speech')

    def speakers(rows):
        values = {str(r.get('speaker_id') or '').strip() for r in rows}
        if any(v.lower().rsplit(':', 1)[-1] in {'', 'none', 'unknown'} for v in values):
            raise ValueError('Curated splits require known speaker identities')
        return values

    if speakers(train) & speakers(evaluation):
        raise ValueError('Curated splits contain shared speaker identities')
