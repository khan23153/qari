"""Forced alignment using Wav2Vec2-CTC.

Aligns user audio against expected text to get per-word timestamps
and alignment scores for mispronunciation confirmation.
"""
import numpy as np
import torch
import torchaudio
from typing import Optional
import structlog

log = structlog.get_logger()

MODEL_ID = "jonatasgrosman/wav2vec2-large-xlsr-53-arabic"


class ForcedAligner:
    """Wav2Vec2-CTC forced alignment for per-word timestamps."""

    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_10M
        self.model = self.bundle.get_model().to(device)
        self.model.eval()
        self.tokenizer = torchaudio.pipelines.WAV2VEC2_ASR_BASE_10M.get_tokenizer()
        self.decoder = torchaudio.pipelines.WAV2VEC2_ASR_BASE_10M.get_decoder()
        log.info("Loaded Wav2Vec2 aligner", device=device)

    def align(self, audio: np.ndarray, expected_text: str,
              sample_rate: int = 16000) -> dict:
        """Force-align audio against expected text.

        Args:
            audio: mono audio at 16kHz
            expected_text: the expected Arabic text (normalized, no diacritics)

        Returns:
            {
                "word_timestamps": [{"word": str, "start_ms": int, "end_ms": int, "score": float}],
                "overall_score": float,
            }
        """
        assert sample_rate == 16000

        # Convert to tensor
        waveform = torch.from_numpy(audio).float().unsqueeze(0).to(self.device)

        # Get emission probabilities
        with torch.no_grad():
            emissions, _ = self.model(waveform)
            emissions = torch.log_softmax(emissions, dim=-1)

        emission = emissions[0].cpu().detach()

        # Tokenize expected text
        transcript = expected_text.replace(" ", "|")
        tokens = self.tokenizer(transcript)

        # Forced alignment
        alignment = torchaudio.functional.forced_align(
            emission, tokens
        )

        # Get word-level boundaries
        token_spans = alignment[0]
        word_spans = self._get_word_spans(token_spans, expected_text.split())

        # Calculate per-word scores and timestamps
        word_timestamps = []
        frame_rate = self.bundle.sample_rate // 320  # Wav2Vec2 downsampling factor

        for word, span in word_spans:
            start_sample = span[0].start * 320
            end_sample = span[-1].end * 320
            start_ms = int(start_sample / sample_rate * 1000)
            end_ms = int(end_sample / sample_rate * 1000)

            # Score = mean token score in this word
            scores = [s.score for s in span]
            word_score = float(np.mean(scores)) if scores else 0.0

            word_timestamps.append({
                "word": word,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "score": word_score,
            })

        overall_score = float(np.mean([w["score"] for w in word_timestamps])) if word_timestamps else 0.0

        return {
            "word_timestamps": word_timestamps,
            "overall_score": overall_score,
        }

    def _get_word_spans(self, token_spans, words):
        """Group token spans into word spans."""
        # Simple grouping: split tokens by space token
        word_spans = []
        current_span = []
        word_idx = 0

        for ts in token_spans:
            current_span.append(ts)
            # Check if this is a word boundary (space token or last token)
            if ts.token == self.tokenizer._space_token or word_idx == len(words) - 1:
                if word_idx < len(words):
                    word_spans.append((words[word_idx], current_span))
                    word_idx += 1
                    current_span = []

        return word_spans
