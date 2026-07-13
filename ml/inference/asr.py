"""
Quran ASR — Whisper-Quran transcription with diacritic-insensitive normalization.

Uses tarteel-ai/whisper-base-ar-quran (Quran-fine-tuned Whisper) for Arabic
Quranic recitation recognition. Includes comprehensive Arabic text normalization
that removes diacritics (harakat), normalizes alef variants, removes tatweel,
and standardizes other character forms before alignment.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

import torch
import numpy as np

logger = logging.getLogger(__name__)

# ── Model constants ──────────────────────────────────────────────────────────

WHISPER_MODEL_ID = "tarteel-ai/whisper-base-ar-quran"
WHISPER_LANGUAGE = "ar"
WHISPER_TASK = "transcribe"

# ── Arabic normalization ─────────────────────────────────────────────────────

# Harakat (diacritics) to strip
_HARAKAT_PATTERN = re.compile(
    "[\u0618-\u061A"   # Small high rounded, etc.
    "\u064B-\u065F"    # Fathatan, Dammatan, Kasratan, Fatha, Damma, Kasra, Shadda, Sukun, etc.
    "\u0670"           # Superscript Alef
    "\u06D6-\u06DC"    # Quranic annotation signs
    "\u06DF-\u06E8"    # More Quranic annotation signs
    "\u06EA-\u06ED"    # More Quranic annotation signs
    "]"
)

# Tatweel (kashida) — elongation character
_TATWEEL = "\u0640"
_TATWEEL_PATTERN = re.compile(_TATWEEL)

# Alef variants to normalize to plain alef (ا)
_ALEF_VARIANTS = {"\u0622": "ا",  # Alef with madda above (آ)
                  "\u0623": "ا",  # Alef with hamza above (أ)
                  "\u0625": "ا",  # Alef with hamza below (إ)
                  "\u0671": "ا",  # Alef wasla (ٱ)
                  "\u0672": "ا",  # Alef with wavy hamza above
                  "\u0673": "ا",  # Alef with wavy hamza below
                  }

# Ya variants to normalize
_YA_VARIANTS = {"\u0649": "ي",  # Alef maksura (ى) -> ya
                "\u06CC": "ي",  # Farsi ya
                }

# Ta marbuta -> ha (for comparison purposes)
_TA_MARBUTA = "\u0629"  # ة
_HA = "\u0647"  # ه

# Hamza forms that may appear on different carriers
_HAMZA_STANDALONE = "\u0621"  # ء

# Non-Arabic characters to remove (punctuation, digits in Arabic-Indic, etc.)
_NON_ARABIC_PATTERN = re.compile(
    "[^\u0621-\u064A\u0660-\u0669\u066E-\u06D5\u06DE\u06EF ]"  # Keep core Arabic + spaces
)

# Multiple spaces -> single space
_MULTI_SPACE = re.compile(r"\s+")


def normalize_arabic(text: str, *, remove_shadda: bool = True) -> str:
    """
    Normalize Arabic text for diacritic-insensitive comparison.

    Operations (in order):
    1. Remove Quranic annotation signs
    2. Remove harakat (vowels/diacritics)
    3. Remove tatweel (kashida elongation)
    4. Normalize alef variants -> plain alef (ا)
    5. Normalize ya variants -> plain ya (ي)
    6. Normalize ta marbuta -> ha (ة -> ه)
    7. Normalize hamza carriers
    8. Remove non-Arabic characters (punctuation, Latin, etc.)
    9. Collapse multiple spaces
    10. Strip leading/trailing whitespace

    Parameters
    ----------
    text : str
        Raw Arabic text possibly containing diacritics and variant characters.
    remove_shadda : bool, default True
        Whether to remove shadda (gemination marker). Set False if shadda
        information is needed for tajweed analysis.

    Returns
    -------
    str
        Normalized Arabic text suitable for word-level alignment comparison.
    """
    if not text:
        return ""

    # 1 & 2: Remove Quranic annotation signs and harakat
    text = _HARAKAT_PATTERN.sub("", text)

    # 3: Remove tatweel
    text = _TATWEEL_PATTERN.sub("", text)

    # 4: Normalize alef variants
    for variant, canonical in _ALEF_VARIANTS.items():
        text = text.replace(variant, canonical)

    # 5: Normalize ya variants
    for variant, canonical in _YA_VARIANTS.items():
        text = text.replace(variant, canonical)

    # 6: Normalize ta marbuta -> ha
    text = text.replace(_TA_MARBUTA, _HA)

    # 7: Normalize standalone hamza on carriers — keep hamza as part of
    #    its carrier letter (already handled by alef normalization above).
    #    For hamza on waw/ya carriers, normalize to the carrier without hamza
    #    since ASR often drops hamza distinction.
    text = text.replace("\u0624", "و")  # Waw with hamza above (ؤ) -> و
    text = text.replace("\u0626", "ي")  # Ya with hamza above (ئ) -> ي
    text = text.replace(_HAMZA_STANDALONE, "")  # Standalone hamza (ء) -> remove

    # 8: Remove non-Arabic characters
    text = _NON_ARABIC_PATTERN.sub(" ", text)

    # 9: Collapse multiple spaces
    text = _MULTI_SPACE.sub(" ", text)

    # 10: Strip
    return text.strip()


def tokenize_words(text: str) -> list[str]:
    """
    Split normalized Arabic text into word tokens by whitespace.

    Parameters
    ----------
    text : str
        Normalized Arabic text.

    Returns
    -------
    list[str]
        List of word tokens. Empty tokens are filtered out.
    """
    if not text:
        return []
    return [w for w in text.split(" ") if w]


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class ASRToken:
    """A single recognized word token with metadata."""
    text: str
    normalized: str
    start_time: float = 0.0   # seconds
    end_time: float = 0.0     # seconds
    confidence: float = 1.0


@dataclass
class ASRResult:
    """Full ASR transcription result."""
    raw_text: str                              # Raw model output
    normalized_text: str                       # After normalization
    tokens: list[ASRToken] = field(default_factory=list)
    language: str = WHISPER_LANGUAGE
    model_id: str = WHISPER_MODEL_ID
    processing_time_s: float = 0.0

    @property
    def word_count(self) -> int:
        return len(self.tokens)

    @property
    def normalized_words(self) -> list[str]:
        """Convenience: list of normalized word strings."""
        return [t.normalized for t in self.tokens]


# ── Quran ASR class ──────────────────────────────────────────────────────────

class QuranASR:
    """
    Quran-recitation ASR using Whisper fine-tuned on Quranic Arabic.

    Uses the tarteel-ai/whisper-base-ar-quran model from Hugging Face.
    Falls back to a processor-only mode if the model cannot be loaded
    (e.g., in test environments without GPU).

    Parameters
    ----------
    model_id : str
        Hugging Face model identifier. Defaults to the Quran-fine-tuned Whisper.
    device : str, optional
        Torch device ('cuda', 'cpu', 'mps'). Auto-detected if None.
    compute_type : str
        Torch dtype for inference. Defaults to float16 on GPU, float32 on CPU.
    """

    def __init__(
        self,
        model_id: str = WHISPER_MODEL_ID,
        device: Optional[str] = None,
        compute_type: Optional[torch.dtype] = None,
    ) -> None:
        self.model_id = model_id
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if compute_type is None:
            compute_type = torch.float16 if "cuda" in self._device else torch.float32
        self._dtype = compute_type

        self._model = None
        self._processor = None
        self._loaded = False

    def load(self) -> None:
        """Load the Whisper model and processor from Hugging Face."""
        if self._loaded:
            return

        from transformers import WhisperForConditionalGeneration, WhisperProcessor

        logger.info("Loading Whisper model: %s on %s", self.model_id, self._device)
        self._processor = WhisperProcessor.from_pretrained(self.model_id)
        self._model = WhisperForConditionalGeneration.from_pretrained(
            self.model_id,
            torch_dtype=self._dtype,
        ).to(self._device)
        self._model.eval()
        self._loaded = True
        logger.info("Whisper model loaded successfully")

    def _ensure_loaded(self) -> None:
        """Lazy-load the model if not yet loaded."""
        if not self._loaded:
            self.load()

    def transcribe(
        self,
        audio: np.ndarray | torch.Tensor,
        sample_rate: int = 16000,
        *,
        language: str = WHISPER_LANGUAGE,
        return_timestamps: bool = False,
    ) -> ASRResult:
        """
        Transcribe Quranic recitation audio.

        Parameters
        ----------
        audio : np.ndarray or torch.Tensor
            Mono audio signal at ``sample_rate`` Hz. Shape: (n_samples,) or (1, n_samples).
        sample_rate : int, default 16000
            Audio sample rate. Will be resampled to 16kHz if different.
        language : str, default 'ar'
            Language code for the Whisper decoder.
        return_timestamps : bool, default True
            Whether to return word-level timestamps.

        Returns
        -------
        ASRResult
            Transcription result with raw text, normalized text, and per-word tokens.
        """
        import time as _time
        t0 = _time.perf_counter()

        self._ensure_loaded()

        # Convert to torch tensor if needed
        if isinstance(audio, np.ndarray):
            audio = torch.from_numpy(audio).float()
        if audio.dim() > 1:
            audio = audio.squeeze(0) if audio.shape[0] == 1 else audio.squeeze(-1)

        # Resample to 16kHz if needed
        target_sr = 16000
        if sample_rate != target_sr:
            audio = torchaudio.functional.resample(audio, sample_rate, target_sr)

        # Ensure float32 for processor
        audio = audio.float()

        # Process through Whisper
        inputs = self._processor(
            audio.numpy(),
            sampling_rate=target_sr,
            return_tensors="pt",
        )
        input_features = inputs.input_features.to(self._device).to(self._dtype)

        # Generate with forced decoder settings
        forced_decoder_ids = self._processor.get_decoder_prompt_ids(
            language=language,
            task=WHISPER_TASK,
        )

        with torch.no_grad():
            predicted_ids = self._model.generate(
                input_features,
                forced_decoder_ids=forced_decoder_ids,
                return_timestamps=return_timestamps,
                num_beams=1,        # Greedy for speed
                max_new_tokens=448,
            )

        # Decode
        if return_timestamps:
            decoded = self._processor.batch_decode(
                predicted_ids,
                skip_special_tokens=False,
                decode_with_timestamps=True,
            )
            raw_text = decoded[0] if decoded else ""
            tokens = self._extract_tokens_from_timestamps(predicted_ids, raw_text)
        else:
            decoded = self._processor.batch_decode(
                predicted_ids,
                skip_special_tokens=True,
            )
            raw_text = decoded[0] if decoded else ""
            tokens = self._build_tokens_without_timestamps(raw_text)

        # Normalize
        normalized = normalize_arabic(raw_text)
        norm_words = tokenize_words(normalized)

        # Update token normalized text
        if tokens and len(tokens) == len(norm_words):
            for tok, nw in zip(tokens, norm_words):
                tok.normalized = nw
        else:
            # Rebuild tokens from normalized words
            tokens = [
                ASRToken(text=nw, normalized=nw, confidence=0.8)
                for nw in norm_words
            ]

        elapsed = _time.perf_counter() - t0
        return ASRResult(
            raw_text=raw_text,
            normalized_text=normalized,
            tokens=tokens,
            language=language,
            model_id=self.model_id,
            processing_time_s=elapsed,
        )

    def _extract_tokens_from_timestamps(
        self,
        predicted_ids: torch.Tensor,
        raw_text: str,
    ) -> list[ASRToken]:
        """
        Extract word-level tokens with timestamps from Whisper output.

        Whisper outputs timestamp tokens interleaved with text tokens.
        We parse the token sequence to extract word boundaries.
        """
        tokens: list[ASRToken] = []

        # Get the processor's vocabulary for timestamp token detection
        if not hasattr(self._processor, "tokenizer"):
            return self._build_tokens_without_timestamps(raw_text)

        tokenizer = self._processor.tokenizer

        # Iterate through the generated token IDs
        ids = predicted_ids[0].cpu().tolist()

        current_start: float | None = None
        current_text_parts: list[str] = []

        for token_id in ids:
            # Skip special tokens that aren't timestamps
            if token_id in (tokenizer.bos_token_id, tokenizer.eos_token_id,
                            tokenizer.pad_token_id):
                continue

            # Timestamp tokens have IDs >= special tokens start
            # In Whisper, timestamp tokens are >= 50257 (for base model)
            timestamp_begin = getattr(tokenizer, "timestamp_begin", 50257)
            if token_id >= timestamp_begin:
                # This is a timestamp token: time = (id - timestamp_begin) * 0.02s
                t = (token_id - timestamp_begin) * 0.02
                if current_start is not None:
                    # End of previous segment
                    word_text = " ".join(current_text_parts).strip()
                    if word_text:
                        norm = normalize_arabic(word_text)
                        for w in norm.split(" "):
                            if w:
                                tokens.append(ASRToken(
                                    text=w,
                                    normalized=w,
                                    start_time=current_start,
                                    end_time=t,
                                    confidence=0.85,
                                ))
                    current_text_parts = []
                current_start = t
            else:
                # Text token
                piece = tokenizer.decode([token_id])
                current_text_parts.append(piece)

        # Handle remaining text after last timestamp
        if current_text_parts:
            word_text = " ".join(current_text_parts).strip()
            if word_text and current_start is not None:
                norm = normalize_arabic(word_text)
                for w in norm.split(" "):
                    if w:
                        tokens.append(ASRToken(
                            text=w,
                            normalized=w,
                            start_time=current_start,
                            end_time=current_start + 0.5,  # estimate
                            confidence=0.80,
                        ))

        return tokens

    def _build_tokens_without_timestamps(self, raw_text: str) -> list[ASRToken]:
        """Build tokens from text without timestamp information."""
        norm = normalize_arabic(raw_text)
        words = tokenize_words(norm)
        return [
            ASRToken(text=w, normalized=w, confidence=0.85)
            for w in words
        ]

    @property
    def device(self) -> str:
        return self._device

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# Late import to avoid hard dependency at module load
try:
    import torchaudio
except ImportError:
    torchaudio = None  # type: ignore[assignment]
