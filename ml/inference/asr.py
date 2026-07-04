"""ASR inference — Quran-fine-tuned Whisper for fluency checking.

Uses tarteel-ai/whisper-base-ar-quran for Quranic Arabic transcription.
Performs diacritic-insensitive normalization for word-level comparison.
"""
import numpy as np
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor
import structlog

log = structlog.get_logger()

MODEL_ID = "tarteel-ai/whisper-base-ar-quran"


class QuranASR:
    """Quran-fine-tuned Whisper ASR for recitation transcription."""

    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.processor = WhisperProcessor.from_pretrained(MODEL_ID)
        self.model = WhisperForConditionalGeneration.from_pretrained(MODEL_ID).to(device)
        self.model.eval()
        log.info("Loaded Quran ASR model", model=MODEL_ID, device=device)

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> dict:
        """Transcribe audio and return hypothesis tokens with confidence.

        Args:
            audio: mono audio array at 16kHz
            sample_rate: must be 16000

        Returns:
            {"text": str, "tokens": list[str], "confidence": float}
        """
        assert sample_rate == 16000, "Audio must be 16kHz"

        # Process audio
        inputs = self.processor(audio, sampling_rate=sample_rate, return_tensors="pt")
        input_features = inputs.input_features.to(self.device)

        # Generate with timestamps
        with torch.no_grad():
            predicted_ids = self.model.generate(
                input_features,
                language="ar",
                task="transcribe",
                return_timestamps=True,
            )

        # Decode
        result = self.processor.batch_decode(
            predicted_ids, skip_special_tokens=True
        )
        text = result[0] if result else ""

        # Tokenize for word-level comparison
        tokens = self._normalize_and_tokenize(text)

        return {
            "text": text,
            "tokens": tokens,
            "confidence": 0.85,  # TODO: extract actual confidence scores
        }

    def _normalize_and_tokenize(self, text: str) -> list[str]:
        """Normalize Arabic text (diacritic-insensitive) and tokenize.

        Removes harakat/diacritics for robust word-level comparison.
        """
        import re
        # Remove Arabic diacritics (harakat)
        diacritics_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670\u0640]')
        text = diacritics_pattern.sub("", text)
        # Remove tatweel (kashida)
        text = text.replace("\u0640", "")
        # Normalize alef variants
        text = text.replace("\u0623", "ا").replace("\u0625", "ا").replace("\u0622", "ا")
        # Tokenize by whitespace
        tokens = text.strip().split()
        return tokens
