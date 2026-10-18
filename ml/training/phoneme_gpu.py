"""Split and temporal-head primitives for experimental audio-only phone training."""
from __future__ import annotations

import hashlib
import re
import unicodedata

import torch
from torch import nn

from ml.training.phoneme_ctc_pilot import altered_targets


def reference_group(text: str) -> str:
    """Normalize presentation for leakage grouping, never acoustic correctness."""
    if not isinstance(text, str):
        raise ValueError('A known reference group is required')
    text = unicodedata.normalize('NFKC', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn' and char != 'ـ')
    text = text.translate(str.maketrans('أإآٱ', 'اااا'))
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        raise ValueError('A nonempty reference group is required')
    return text


def source_role(row: dict, *, held_voice: str = 'Jessica') -> str | None:
    """Reserve one voice and15% of normalized reference groups independently."""
    altered_targets(row)
    voice = row.get('speaker')
    if not isinstance(voice, str) or not voice.strip():
        raise ValueError('A known synthetic voice is required')
    group = reference_group(row.get('sentence_ref'))
    held_group = int.from_bytes(hashlib.sha256(group.encode()).digest()[:8], 'big') / 2**64 < .15
    if voice == held_voice:
        return 'validation' if held_group else None
    return None if held_group else 'train'


class TemporalPhoneHead(nn.Module):
    """A small CTC head whose real-frame output does not depend on batch padding."""

    def __init__(self, vocabulary_size: int):
        super().__init__()
        if type(vocabulary_size) is not int or not 2 <= vocabulary_size <= 512:
            raise ValueError('A bounded phoneme vocabulary including blank is required')
        self.input_norm = nn.LayerNorm(512)
        self.project = nn.Linear(512, 256)
        self.dropout = nn.Dropout(.15)
        self.convolutions = nn.ModuleList([
            nn.Conv1d(256, 256, 5, padding=2*dilation, dilation=dilation, groups=256)
            for dilation in (1, 2)
        ])
        self.mix = nn.ModuleList([nn.Linear(256, 256) for _ in self.convolutions])
        self.norms = nn.ModuleList([nn.LayerNorm(256) for _ in self.convolutions])
        self.output = nn.Linear(256, vocabulary_size)

    def forward(self, features: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        if (features.ndim != 3 or features.shape[2] != 512
                or not features.is_floating_point() or not torch.isfinite(features).all()
                or lengths.ndim != 1 or len(lengths) != len(features)
                or lengths.dtype not in (torch.int32, torch.int64)
                or torch.any(lengths <= 0) or torch.any(lengths > features.shape[1])):
            raise ValueError('Invalid acoustic features or actual frame lengths')
        mask = (torch.arange(features.shape[1], device=features.device)[None, :]
                < lengths.to(features.device)[:, None])[:, :, None]
        x = self.dropout(torch.nn.functional.gelu(self.project(self.input_norm(features)))) * mask
        for convolution, mix, norm in zip(self.convolutions, self.mix, self.norms):
            temporal = convolution(x.transpose(1, 2)).transpose(1, 2)
            x = self.dropout(norm(x + torch.nn.functional.gelu(mix(temporal)))) * mask
        return self.output(x) * mask
