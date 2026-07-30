"""
Whisper fine-tuning script for Quran Arabic recitation.

Fine-tunes a pretrained Whisper model on Quranic Arabic recitation data
to improve recognition accuracy for Quran recitation. Uses Hugging Face
transformers + datasets with Word Error Rate (WER) as the primary metric.

Usage:
    python -m ml.training.finetune_whisper \\
        --model_id tarteel-ai/whisper-base-ar-quran \\
        --data_dir /data/quran_recitations \\
        --output_dir /models/whisper-quran-finetuned \\
        --language ar \\
        --epochs 3 \\
        --batch_size 16 \\
        --learning_rate 1e-5

Dataset format (HuggingFace datasets or local manifest):
    {
        "audio": {"path": "/data/audio/sample_001.wav", "sampling_rate": 16000},
        "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "normalized_text": "بسم الله الرحمن الرحيم",
        "surah": 1,
        "ayah": 1,
        "duration_s": 5.2
    }

Or a JSONL manifest file:
    {"audio_path": "/data/audio/sample_001.wav", "text": "...", "surah": 1, "ayah": 1}
    {"audio_path": "/data/audio/sample_002.wav", "text": "...", "surah": 1, "ayah": 2}
    ...
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)

# ── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_MODEL_ID = "tarteel-ai/whisper-base-ar-quran"
DEFAULT_LANGUAGE = "ar"
DEFAULT_TASK = "transcribe"
DEFAULT_EPOCHS = 3
DEFAULT_BATCH_SIZE = 16
DEFAULT_LR = 1e-5
DEFAULT_MAX_STEPS = -1      # -1 = use epochs
DEFAULT_WARMUP_STEPS = 500
DEFAULT_MAX_LABEL_LEN = 448
SAMPLE_RATE = 16000


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fine-tune Whisper on Quran Arabic recitation data"
    )
    parser.add_argument(
        "--model_id", type=str, default=DEFAULT_MODEL_ID,
        help="Pretrained Whisper model ID from Hugging Face"
    )
    parser.add_argument(
        "--data_dir", type=str, required=True,
        help="Directory containing training data (audio + manifest.jsonl)"
    )
    parser.add_argument(
        "--output_dir", type=str, default="./whisper-quran-finetuned",
        help="Output directory for the fine-tuned model"
    )
    parser.add_argument(
        "--language", type=str, default=DEFAULT_LANGUAGE,
        help="Language code for the Whisper decoder"
    )
    parser.add_argument(
        "--epochs", type=int, default=DEFAULT_EPOCHS,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch_size", type=int, default=DEFAULT_BATCH_SIZE,
        help="Training batch size (per device)"
    )
    parser.add_argument(
        "--learning_rate", type=float, default=DEFAULT_LR,
        help="Learning rate"
    )
    parser.add_argument(
        "--warmup_steps", type=int, default=DEFAULT_WARMUP_STEPS,
        help="Number of warmup steps for the learning rate scheduler"
    )
    parser.add_argument(
        "--max_steps", type=int, default=DEFAULT_MAX_STEPS,
        help="Maximum training steps (-1 = use epochs)"
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=0,
        help=(
            "Maximum manifest samples to prepare (0 = all). Useful for a "
            "smoke run without copying or rewriting the dataset."
        ),
    )
    parser.add_argument(
        "--eval_split", type=float, default=0.1,
        help="Fraction of data to use for evaluation"
    )
    parser.add_argument(
        "--use_fp16", action="store_true", default=True,
        help="Use mixed precision (FP16) training"
    )
    parser.add_argument(
        "--gradient_checkpointing", action="store_true", default=True,
        help="Enable gradient checkpointing to save memory"
    )
    parser.add_argument(
        "--push_to_hub", action="store_true",
        help="Push the fine-tuned model to Hugging Face Hub"
    )
    parser.add_argument(
        "--hub_model_id", type=str, default="",
        help="Model ID for pushing to Hugging Face Hub"
    )
    parser.add_argument(
        "--resume_from_checkpoint",
        nargs="?",
        const="auto",
        default=None,
        help=(
            "Resume training from a checkpoint path. Pass the flag without a "
            "value to use the newest checkpoint in --output_dir."
        ),
    )
    return parser.parse_args()


# ── Data preparation ─────────────────────────────────────────────────────────

def load_manifest(data_dir: str) -> list[dict]:
    """
    Load training data manifest from a JSONL file.

    Expected format (one JSON object per line):
        {"audio_path": "/path/to/audio.wav", "text": "Arabic text with diacritics", ...}

    Parameters
    ----------
    data_dir : str
        Directory containing manifest.jsonl and audio files.

    Returns
    -------
    list[dict]
        List of data entries.
    """
    manifest_path = Path(data_dir) / "manifest.jsonl"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    entries: list[dict] = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    logger.info("Loaded %d entries from %s", len(entries), manifest_path)
    return entries


def create_dataset(
    entries: list[dict],
    data_dir: str,
    eval_split: float = 0.1,
    max_samples: int = 0,
) -> tuple[list[dict], list[dict]]:
    """
    Split entries into train and evaluation sets.

    Parameters
    ----------
    entries : list[dict]
        Full data entries.
    data_dir : str
        Base data directory (for resolving relative audio paths).
    eval_split : float
        Fraction of data for evaluation.

    Returns
    -------
    train_entries, eval_entries : list[dict], list[dict]
    """
    import random

    random.seed(42)
    shuffled = entries.copy()
    random.shuffle(shuffled)

    if max_samples < 0:
        raise ValueError("max_samples must be 0 or greater")
    if max_samples:
        shuffled = shuffled[:max_samples]
        logger.info("Limited dataset to %d samples", len(shuffled))
    if len(shuffled) < 2:
        raise ValueError("At least 2 manifest samples are required")

    n_eval = max(1, int(len(shuffled) * eval_split))
    eval_entries = shuffled[:n_eval]
    train_entries = shuffled[n_eval:]

    # Resolve audio paths
    base = Path(data_dir)
    for entry in train_entries + eval_entries:
        audio_path = entry.get("audio_path", entry.get("audio", {}).get("path", ""))
        if audio_path and not Path(audio_path).is_absolute():
            entry["audio_path"] = str(base / audio_path)

    logger.info("Split: %d train, %d eval", len(train_entries), len(eval_entries))
    return train_entries, eval_entries


# ── Data collator ────────────────────────────────────────────────────────────

@dataclass
class DataCollatorSpeechSeq2Seq:
    """
    Data collator for Whisper fine-tuning.

    Pads input features (log-Mel spectrograms) and labels to the same length
    within a batch, and replaces padding tokens with -100 for loss masking.
    """
    processor: Any
    decoder_start_token_id: int

    def __call__(self, features: list[dict]) -> dict[str, Any]:
        import torch

        # Split into input features and labels
        input_features = [
            {"input_features": f["input_features"]} for f in features
        ]
        label_features = [
            {"input_ids": f["labels"]} for f in features
        ]

        # Pad input features (log-Mel spectrograms)
        batch = self.processor.feature_extractor.pad(
            input_features, return_tensors="pt"
        )

        # Pad labels
        labels_batch = self.processor.tokenizer.pad(
            label_features, return_tensors="pt"
        )

        # Replace padding with -100 for loss masking
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )

        # Remove BOS token if it was prepended during tokenization
        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels
        return batch


# ── Metric computation ───────────────────────────────────────────────────────

def compute_wer(preds: list[str], refs: list[str]) -> float:
    """
    Compute Word Error Rate using jiwer.

    Parameters
    ----------
    preds : list[str]
        Predicted transcriptions.
    refs : list[str]
        Reference transcriptions.

    Returns
    -------
    float
        Word Error Rate (lower is better).
    """
    try:
        import jiwer
        return float(jiwer.wer(refs, preds))
    except ImportError:
        # Fallback: simple WER computation
        total_errors = 0
        total_words = 0
        for pred, ref in zip(preds, refs):
            pred_words = pred.split()
            ref_words = ref.split()
            # Simple Levenshtein at word level
            total_errors += _word_edit_distance(pred_words, ref_words)
            total_words += len(ref_words)
        return total_errors / max(total_words, 1)


def _word_edit_distance(s1: list[str], s2: list[str]) -> int:
    """Compute word-level edit distance."""
    m, n = len(s1), len(s2)
    if m == 0:
        return n
    if n == 0:
        return m

    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if s1[i - 1] == s2[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(dp[j], dp[j - 1], prev)
            prev = temp
    return dp[n]


def make_compute_metrics(processor: Any, language: str, task: str):
    """
    Create a compute_metrics function for the Trainer.

    Returns a function that takes an EvalPrediction and returns {"wer": float}.
    """

    def compute_metrics(eval_pred) -> dict[str, float]:
        import numpy as np

        pred_ids = eval_pred.predictions
        label_ids = eval_pred.label_ids

        # Replace -100 with pad token
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id

        # Decode
        pred_str = processor.tokenizer.batch_decode(
            pred_ids, skip_special_tokens=True
        )
        label_str = processor.tokenizer.batch_decode(
            label_ids, skip_special_tokens=True
        )

        wer = compute_wer(pred_str, label_str)
        return {"wer": wer}

    return compute_metrics


# ── Training ─────────────────────────────────────────────────────────────────

def prepare_dataset(
    entries: list[dict],
    processor: Any,
    language: str,
    task: str,
) -> list[dict]:
    """
    Prepare dataset entries: load audio, extract log-Mel features, tokenize text.

    Parameters
    ----------
    entries : list[dict]
        Raw data entries with audio_path and text.
    processor : WhisperProcessor
        Whisper processor for feature extraction and tokenization.
    language : str
        Language code.
    task : str
        Task type ("transcribe" or "translate").

    Returns
    -------
    list[dict]
        Prepared entries with input_features and labels.
    """
    import soundfile as sf
    import numpy as np

    prepared: list[dict] = []

    for i, entry in enumerate(entries):
        try:
            audio_path = entry["audio_path"]
            audio, sr = sf.read(audio_path, dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)

            # Resample to 16kHz if needed
            if sr != SAMPLE_RATE:
                import torchaudio
                import torch
                tensor = torch.from_numpy(audio).float()
                tensor = torchaudio.functional.resample(tensor, sr, SAMPLE_RATE)
                audio = tensor.numpy()

            # Extract log-Mel spectrogram
            inputs = processor(
                audio, sampling_rate=SAMPLE_RATE, return_tensors="pt"
            )
            input_features = inputs.input_features.squeeze(0).numpy()

            # Tokenize text (with language and task tokens)
            text = entry.get("text", entry.get("normalized_text", ""))
            labels = processor.tokenizer(
                text, max_length=DEFAULT_MAX_LABEL_LEN, truncation=True
            ).input_ids

            prepared.append({
                "input_features": input_features,
                "labels": labels,
            })

        except Exception as e:
            logger.warning("Could not prepare entry %d (%s): %s", i, entry.get("audio_path", "?"), e)

    logger.info("Prepared %d/%d entries", len(prepared), len(entries))
    return prepared


def resolve_resume_checkpoint(value: str | None, output_dir: str) -> str | None:
    """Resolve an explicit or automatic Trainer checkpoint."""
    if value is None:
        return None
    if value != "auto":
        checkpoint = Path(value)
        if not checkpoint.is_dir():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint}")
        return str(checkpoint)

    candidates: list[tuple[int, Path]] = []
    for path in Path(output_dir).glob("checkpoint-*"):
        if not path.is_dir():
            continue
        try:
            step = int(path.name.removeprefix("checkpoint-"))
        except ValueError:
            continue
        candidates.append((step, path))
    if not candidates:
        raise FileNotFoundError(
            f"No checkpoint-* directory found in output directory: {output_dir}"
        )
    return str(max(candidates, key=lambda item: item[0])[1])


def configure_whisper_model(model: Any, processor: Any, language: str) -> None:
    """Set the decoder prompt without erasing Whisper token filters."""
    forced_decoder_ids = processor.get_decoder_prompt_ids(
        language=language,
        task=DEFAULT_TASK,
    )
    model.config.forced_decoder_ids = forced_decoder_ids
    if getattr(model, "generation_config", None) is not None:
        model.generation_config.forced_decoder_ids = forced_decoder_ids


def train(args: argparse.Namespace) -> None:
    """
    Main training function.

    Loads the pretrained model, prepares the dataset, sets up the trainer,
    and runs fine-tuning.
    """
    import torch
    from transformers import (
        WhisperForConditionalGeneration,
        WhisperProcessor,
        Seq2SeqTrainingArguments,
        Seq2SeqTrainer,
    )

    # ── Load model and processor ──────────────────────────────────────────────
    logger.info("Loading model: %s", args.model_id)
    processor = WhisperProcessor.from_pretrained(args.model_id)
    model = WhisperForConditionalGeneration.from_pretrained(args.model_id)

    # Configure model
    # Keep the checkpoint's suppress_tokens. Clearing them makes recent
    # Transformers releases crash during generated evaluation.
    configure_whisper_model(model, processor, args.language)

    if args.gradient_checkpointing:
        model.config.use_cache = False
        model.gradient_checkpointing_enable()

    # ── Load and prepare data ─────────────────────────────────────────────────
    entries = load_manifest(args.data_dir)
    train_entries, eval_entries = create_dataset(
        entries,
        args.data_dir,
        args.eval_split,
        args.max_samples,
    )

    logger.info("Preparing training dataset...")
    train_data = prepare_dataset(train_entries, processor, args.language, DEFAULT_TASK)
    logger.info("Preparing evaluation dataset...")
    eval_data = prepare_dataset(eval_entries, processor, args.language, DEFAULT_TASK)

    # ── Data collator ─────────────────────────────────────────────────────────
    data_collator = DataCollatorSpeechSeq2Seq(
        processor=processor,
        decoder_start_token_id=model.config.decoder_start_token_id,
    )

    # ── Training arguments ────────────────────────────────────────────────────
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=max(1, args.batch_size // 2),
        gradient_accumulation_steps=1,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        max_steps=args.max_steps if args.max_steps > 0 else -1,
        num_train_epochs=args.epochs,
        gradient_checkpointing=args.gradient_checkpointing,
        fp16=args.use_fp16 and torch.cuda.is_available(),
        evaluation_strategy="steps",
        eval_steps=500,
        save_strategy="steps",
        save_steps=500,
        save_total_limit=3,
        predict_with_generate=True,
        generation_max_length=DEFAULT_MAX_LABEL_LEN,
        report_to=["tensorboard"],
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_model_id or None,
    )

    # ── Trainer ───────────────────────────────────────────────────────────────
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=eval_data,
        data_collator=data_collator,
        compute_metrics=make_compute_metrics(processor, args.language, DEFAULT_TASK),
        tokenizer=processor.feature_extractor,
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    logger.info("Starting training...")
    resume_checkpoint = resolve_resume_checkpoint(
        args.resume_from_checkpoint,
        args.output_dir,
    )
    if resume_checkpoint:
        logger.info("Resuming from checkpoint: %s", resume_checkpoint)
    train_result = trainer.train(resume_from_checkpoint=resume_checkpoint)

    # ── Save ──────────────────────────────────────────────────────────────────
    logger.info("Saving model to %s", args.output_dir)
    trainer.save_model(args.output_dir)
    processor.save_pretrained(args.output_dir)

    # Log metrics
    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)
    trainer.save_state()

    # ── Final evaluation ──────────────────────────────────────────────────────
    logger.info("Running final evaluation...")
    eval_metrics = trainer.evaluate()
    trainer.log_metrics("eval", eval_metrics)
    trainer.save_metrics("eval", eval_metrics)

    logger.info("Fine-tuning complete! WER: %.4f", eval_metrics.get("eval_wer", -1))


def main() -> None:
    """Entry point for the Whisper fine-tuning script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    args = parse_args()
    train(args)


if __name__ == "__main__":
    main()
