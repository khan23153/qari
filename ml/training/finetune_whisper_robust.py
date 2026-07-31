#!/usr/bin/env python3
"""Continue Whisper fine-tuning with explicit train/eval manifests.

When the dataset changes, point --model_id at the previous FINAL Hugging Face
model directory and use a new --output_dir. This keeps the learned weights but
starts a fresh optimizer and scheduler. --resume_from_checkpoint is only for
resuming an interrupted run in the new output directory.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy import signal

LOGGER = logging.getLogger("qari.robust_train")
SAMPLE_RATE = 16_000
MAX_LABEL_LENGTH = 448
_HARAKAT = re.compile("[\u0618-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_NON_ARABIC = re.compile(r"[^\u0621-\u064A\u0660-\u0669\u066E-\u06D5 ]")
_SPACES = re.compile(r"\s+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_id", required=True)
    parser.add_argument("--train_manifest", required=True)
    parser.add_argument("--eval_manifest", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--grad_accum", type=int, default=2)
    parser.add_argument("--learning_rate", type=float, default=5e-6)
    parser.add_argument("--warmup_ratio", type=float, default=0.05)
    parser.add_argument("--weight_decay", type=float, default=0.01)
    parser.add_argument("--eval_steps", type=int, default=500)
    parser.add_argument("--save_steps", type=int, default=500)
    parser.add_argument("--logging_steps", type=int, default=25)
    parser.add_argument("--num_workers", type=int, default=4)
    parser.add_argument("--early_stopping_patience", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fp16", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        "--gradient_checkpointing",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--resume_from_checkpoint",
        default=None,
        help="Checkpoint from this phase-two output directory only",
    )
    return parser.parse_args()


def normalize_arabic(text: str) -> str:
    text = _HARAKAT.sub("", text or "").replace("ـ", "")
    for source, target in {
        "آ": "ا", "أ": "ا", "إ": "ا", "ٱ": "ا", "ى": "ي", "ی": "ي",
        "ؤ": "و", "ئ": "ي", "ء": "", "ة": "ه",
    }.items():
        text = text.replace(source, target)
    return _SPACES.sub(" ", _NON_ARABIC.sub(" ", text)).strip()


def read_manifest(path: str) -> list[dict[str, str]]:
    manifest = Path(path).expanduser().resolve()
    rows: list[dict[str, str]] = []
    with manifest.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            audio_path = Path(str(row["audio_path"])).expanduser()
            if not audio_path.is_absolute():
                audio_path = manifest.parent / audio_path
            if not audio_path.exists():
                raise FileNotFoundError(
                    f"Missing audio at {manifest}:{line_number}: {audio_path}"
                )
            text = str(row.get("text") or row.get("normalized_text") or "").strip()
            if not text:
                raise ValueError(f"Missing text at {manifest}:{line_number}")
            rows.append({"audio_path": str(audio_path.resolve()), "text": text})
    if not rows:
        raise ValueError(f"No rows in {manifest}")
    return rows


def load_audio(path: str) -> np.ndarray:
    audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sample_rate != SAMPLE_RATE:
        divisor = math.gcd(int(sample_rate), SAMPLE_RATE)
        audio = signal.resample_poly(
            audio, SAMPLE_RATE // divisor, int(sample_rate) // divisor
        ).astype(np.float32)
    return np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)


class ManifestDataset:
    """Lazy audio dataset so a large robust corpus is not preloaded into RAM."""

    def __init__(self, rows: list[dict[str, str]], processor: Any) -> None:
        self.rows = rows
        self.processor = processor

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        audio = load_audio(row["audio_path"])
        features = self.processor.feature_extractor(
            audio,
            sampling_rate=SAMPLE_RATE,
            return_tensors="np",
            padding="max_length",
            truncation=True,
        ).input_features[0]
        labels = self.processor.tokenizer(
            row["text"],
            max_length=MAX_LABEL_LENGTH,
            truncation=True,
        ).input_ids
        return {"input_features": features, "labels": labels}


@dataclass
class SpeechCollator:
    processor: Any
    decoder_start_token_id: int

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        input_features = [
            {"input_features": feature["input_features"]} for feature in features
        ]
        label_features = [{"input_ids": feature["labels"]} for feature in features]
        batch = self.processor.feature_extractor.pad(
            input_features, return_tensors="pt"
        )
        labels_batch = self.processor.tokenizer.pad(
            label_features, return_tensors="pt"
        )
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )
        if labels.shape[1] and (
            labels[:, 0] == self.decoder_start_token_id
        ).all().item():
            labels = labels[:, 1:]
        batch["labels"] = labels
        return batch


def make_metrics(processor: Any):
    import jiwer

    def compute(eval_prediction) -> dict[str, float]:
        prediction_ids = eval_prediction.predictions
        label_ids = np.array(eval_prediction.label_ids, copy=True)
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        predictions = processor.tokenizer.batch_decode(
            prediction_ids, skip_special_tokens=True
        )
        references = processor.tokenizer.batch_decode(
            label_ids, skip_special_tokens=True
        )
        return {
            "wer": float(
                jiwer.wer(
                    [normalize_arabic(text) for text in references],
                    [normalize_arabic(text) for text in predictions],
                )
            )
        }

    return compute


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    import torch
    from transformers import (
        EarlyStoppingCallback,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        WhisperForConditionalGeneration,
        WhisperProcessor,
        set_seed,
    )

    if args.fp16 and args.bf16:
        raise ValueError("Choose fp16 or bf16, not both")
    if args.batch_size < 1 or args.grad_accum < 1:
        raise ValueError("batch_size and grad_accum must be positive")
    set_seed(args.seed)

    train_rows = read_manifest(args.train_manifest)
    eval_rows = read_manifest(args.eval_manifest)
    LOGGER.info("train rows=%d eval rows=%d", len(train_rows), len(eval_rows))

    processor = WhisperProcessor.from_pretrained(args.model_id)
    model = WhisperForConditionalGeneration.from_pretrained(args.model_id)
    forced_decoder_ids = processor.get_decoder_prompt_ids(
        language="ar", task="transcribe"
    )
    model.config.forced_decoder_ids = forced_decoder_ids
    model.generation_config.forced_decoder_ids = forced_decoder_ids
    model.config.use_cache = not args.gradient_checkpointing
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    training_arguments = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=max(1, args.batch_size // 2),
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        lr_scheduler_type="cosine",
        max_grad_norm=1.0,
        fp16=args.fp16 and torch.cuda.is_available(),
        bf16=args.bf16 and torch.cuda.is_available(),
        gradient_checkpointing=args.gradient_checkpointing,
        evaluation_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        save_total_limit=3,
        predict_with_generate=True,
        generation_max_length=MAX_LABEL_LENGTH,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        report_to=["tensorboard"],
        dataloader_num_workers=args.num_workers,
        remove_unused_columns=False,
        label_smoothing_factor=0.05,
        seed=args.seed,
        data_seed=args.seed,
    )

    callbacks = []
    if args.early_stopping_patience > 0:
        callbacks.append(
            EarlyStoppingCallback(
                early_stopping_patience=args.early_stopping_patience
            )
        )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_arguments,
        train_dataset=ManifestDataset(train_rows, processor),
        eval_dataset=ManifestDataset(eval_rows, processor),
        data_collator=SpeechCollator(
            processor, model.config.decoder_start_token_id
        ),
        compute_metrics=make_metrics(processor),
        processing_class=processor,
        callbacks=callbacks,
    )
    train_result = trainer.train(
        resume_from_checkpoint=args.resume_from_checkpoint
    )
    trainer.save_model(args.output_dir)
    processor.save_pretrained(args.output_dir)
    trainer.save_metrics("train", train_result.metrics)
    evaluation_metrics = trainer.evaluate()
    trainer.save_metrics("eval", evaluation_metrics)
    trainer.save_state()
    LOGGER.info("finished: %s", evaluation_metrics)


if __name__ == "__main__":
    main()
