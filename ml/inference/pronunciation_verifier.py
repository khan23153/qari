"""Reference-aware pronunciation verifier (Safha MDD v3).

Given audio and the phonemes the reciter SHOULD say, the v3 model returns, for
each expected phoneme, the probability that it was mispronounced. The live
session already knows the expected text (the user picks the surah), so this is
a second, independent opinion on words the ASR heard as "correct".

Model files (from the safha-latest bundle, ``models/safha-mdd-v3``):
  config.json, model.safetensors, preprocessor_config.json  (w2v-BERT 2.0 encoder + CTC head)
  verifier.pt                                                 (small transformer over expected phonemes)
  vocab.json                                                  (IqraEval phoneme set; index 0 = CTC blank)
  decision.json                                               ({"threshold": 0.35, "verifier": {...}})

QuranMB.v2 test (1,642 human-annotated recordings), end to end with the
phonemes from ``ml/alignment/quran_g2p.py``:

    threshold 0.35: precision 0.79, recall 0.45, false alarms 0.78% per phoneme
    threshold 0.50: precision 0.82, recall 0.44, false alarms 0.65%  (app default)
    (IqraEval's own phonemes at 0.35: precision 0.84, recall 0.48, 0.63%)

It is meant to ADD red marks only when confident, never to clear an ASR verdict.

Heavy imports (torch, transformers) happen in ``load``; importing this module
is cheap and safe in tests.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

# Training clipped utterances at 15 s; longer windows are scored in pieces.
MAX_WINDOW_S = 15.0


@dataclass(frozen=True)
class VerifierResult:
    """Per expected phoneme: probability it was said wrong."""
    probabilities: list[float]
    threshold: float

    def flags(self) -> list[bool]:
        return [p >= self.threshold for p in self.probabilities]


def word_verdicts(word_phonemes: Sequence[Sequence[str]], result: VerifierResult) -> list[Optional[float]]:
    """Fold phoneme probabilities back onto words: a word's score is its worst phoneme.

    ``None`` for a word with no phonemes (nothing to judge).
    """
    out: list[Optional[float]] = []
    k = 0
    for phonemes in word_phonemes:
        n = len(phonemes)
        chunk = result.probabilities[k:k + n]
        out.append(max(chunk) if chunk else None)
        k += n
    if k != len(result.probabilities):
        raise ValueError(f"{k} phonemes in words but {len(result.probabilities)} probabilities")
    return out


class PronunciationVerifier:
    """Loads the v3 model once; ``score`` is thread-safe for inference (no grad, eval mode)."""

    def __init__(self, model_dir: str | Path, *, device: str = "cpu", threshold: Optional[float] = None):
        self.model_dir = Path(model_dir)
        self.device = device
        decision = json.loads((self.model_dir / "decision.json").read_text())
        # decision.json holds the threshold picked with IqraEval's own phonemes (0.35).
        # With our phonemizer, 0.5 gives the same precision on QuranMB.v2 (0.82, false alarms 0.65%).
        self.threshold = float(threshold if threshold is not None else decision.get("threshold", 0.35))
        self._arch = decision.get("verifier", {})
        self.vocab: list[str] = json.loads((self.model_dir / "vocab.json").read_text())
        self.phoneme_id = {p: i for i, p in enumerate(self.vocab)}
        self._encoder = self._fe = self._verifier = self._torch = None

    # ------------------------------------------------------------------
    def load(self) -> "PronunciationVerifier":
        import torch
        import torch.nn as nn
        from transformers import AutoFeatureExtractor, Wav2Vec2BertForCTC

        self._torch = torch
        self._fe = AutoFeatureExtractor.from_pretrained(self.model_dir)
        enc = Wav2Vec2BertForCTC.from_pretrained(self.model_dir, torch_dtype=torch.float32)
        enc.float().eval().to(self.device)
        self._encoder = enc
        hid, v = int(self._arch.get("hidden", 1024)), int(self._arch.get("vocab", len(self.vocab)))
        d, layers, heads = int(self._arch.get("d", 256)), int(self._arch.get("layers", 3)), int(self._arch.get("heads", 4))

        class Verifier(nn.Module):  # must match train_mdd_v3.py exactly
            def __init__(self):
                super().__init__()
                self.mem = nn.Sequential(nn.Linear(hid, d), nn.LayerNorm(d))
                self.post = nn.Linear(v, d)
                self.emb = nn.Embedding(v + 1, d, padding_idx=v)
                layer = nn.TransformerDecoderLayer(d, heads, 4 * d, dropout=0.1, batch_first=True, norm_first=True)
                self.dec = nn.TransformerDecoder(layer, layers)
                self.head = nn.Sequential(nn.LayerNorm(d), nn.Linear(d, 1))
                self.d = d

            def forward(self, hidden, logp, frame_pad, ref, ref_pad):
                m = self.mem(hidden) + self.post(logp.exp()) + _sinusoid(torch, hidden.shape[1], self.d, hidden.device)
                q = self.emb(ref) + _sinusoid(torch, ref.shape[1], self.d, ref.device)
                h = self.dec(q, m, tgt_key_padding_mask=ref_pad, memory_key_padding_mask=frame_pad)
                return self.head(h).squeeze(-1)

        ver = Verifier()
        state = torch.load(self.model_dir / "verifier.pt", map_location="cpu")
        ver.load_state_dict({k: t.float() for k, t in state.items()})
        self._verifier = ver.eval().to(self.device)
        return self

    @property
    def loaded(self) -> bool:
        return self._verifier is not None

    # ------------------------------------------------------------------
    def score(self, audio_16k: Sequence[float], phonemes: Sequence[str]) -> VerifierResult:
        """Probabilities per expected phoneme for one window of audio (16 kHz mono floats).

        Phonemes outside the model's vocabulary get probability 0.0 (no evidence
        either way) rather than an automatic red mark.
        """
        if not self.loaded:
            self.load()
        torch = self._torch
        known = [i for i, p in enumerate(phonemes) if p in self.phoneme_id]
        probs = [0.0] * len(phonemes)
        if not known or len(audio_16k) < 1600:
            return VerifierResult(probs, self.threshold)
        import numpy as np
        feats = self._fe(np.asarray(audio_16k, dtype=np.float32), sampling_rate=16000, return_tensors="pt")
        x, m = feats["input_features"].to(self.device), feats["attention_mask"].to(self.device)
        ref = torch.tensor([[self.phoneme_id[phonemes[i]] for i in known]], device=self.device)
        pad = len(self.vocab)
        with torch.no_grad():
            out = self._encoder.wav2vec2_bert(input_features=x, attention_mask=m)
            hidden = out.last_hidden_state.float()
            logp = self._encoder.lm_head(hidden).float().log_softmax(-1)
            n = hidden.shape[1]
            length = max(1, min(n, math.ceil(float(m.sum()) * n / m.shape[1])))
            frame_pad = torch.arange(n, device=self.device)[None] >= length
            logit = self._verifier(hidden, logp, frame_pad, ref, ref == pad)
        p = torch.sigmoid(logit[0]).cpu().tolist()
        for k, i in enumerate(known):
            probs[i] = float(p[k])
        return VerifierResult(probs, self.threshold)


def _sinusoid(torch, n, d, device):
    pos = torch.arange(n, device=device).float()[:, None]
    i = torch.arange(0, d, 2, device=device).float()[None]
    ang = pos / torch.pow(10000.0, i / d)
    pe = torch.zeros(n, d, device=device)
    pe[:, 0::2] = torch.sin(ang)
    pe[:, 1::2] = torch.cos(ang)
    return pe


ScoreFn = Callable[[Sequence[float], Sequence[str]], VerifierResult]
