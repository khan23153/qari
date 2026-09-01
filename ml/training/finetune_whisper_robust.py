#!/usr/bin/env python3
"""Robust Qari Whisper fine-tuning with collapse-safety defaults.

V4 safety policy:
- FP32 by default (T4 FP16 previously produced unstable gradients).
- encoder-only adaptation by default to protect the Quran decoder.
- explicit audio attention masks.
- no hidden >30 s audio or >448-token label truncation.
- zero label smoothing by default.
- evaluation metrics detect repetition/overlong generation collapse.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy import signal

LOGGER = logging.getLogger("qari.robust_train")
SAMPLE_RATE = 16_000
MAX_AUDIO_SECONDS = 30.0
MAX_LABEL_LENGTH = 448
_HARAKAT = re.compile("[\u0618-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_NON_ARABIC = re.compile(r"[^\u0621-\u064A\u0660-\u0669\u066E-\u06D5 ]")
_SPACES = re.compile(r"\s+")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model_id", required=True)
    p.add_argument("--train_manifest", required=True)
    p.add_argument("--eval_manifest", required=True)
    p.add_argument("--output_dir", required=True)
    p.add_argument("--epochs", type=float, default=2.0)
    p.add_argument("--batch_size", type=int, default=4)
    p.add_argument("--grad_accum", type=int, default=4)
    p.add_argument("--learning_rate", type=float, default=2e-6)
    p.add_argument("--warmup_ratio", type=float, default=0.05)
    p.add_argument("--weight_decay", type=float, default=0.01)
    p.add_argument("--eval_steps", type=int, default=40)
    p.add_argument("--save_steps", type=int, default=40)
    p.add_argument("--logging_steps", type=int, default=10)
    p.add_argument("--num_workers", type=int, default=2)
    p.add_argument("--early_stopping_patience", type=int, default=0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--train_scope", choices=("encoder", "full"), default="encoder")
    p.add_argument("--label_smoothing_factor", type=float, default=0.0)
    p.add_argument("--fp16", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument(
        "--gradient_checkpointing",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    p.add_argument("--max_eval_word_ratio", type=float, default=1.75)
    p.add_argument("--max_eval_repetition_loop_rate", type=float, default=0.05)
    p.add_argument("--max_eval_overlong_rate", type=float, default=0.05)
    p.add_argument("--resume_from_checkpoint", default=None)
    return p.parse_args()


def normalize_arabic(text: str) -> str:
    text = _HARAKAT.sub("", text or "").replace("ـ", "")
    for source, target in {
        "آ": "ا", "أ": "ا", "إ": "ا", "ٱ": "ا", "ى": "ي", "ی": "ي",
        "ؤ": "و", "ئ": "ي", "ء": "", "ة": "ه",
    }.items():
        text = text.replace(source, target)
    return _SPACES.sub(" ", _NON_ARABIC.sub(" ", text)).strip()


def read_manifest(path: str) -> list[dict[str, Any]]:
    manifest = Path(path).expanduser().resolve()
    rows: list[dict[str, Any]] = []
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
            item = dict(row)
            item["audio_path"] = str(audio_path.resolve())
            item["text"] = text
            item["_manifest_line"] = line_number
            rows.append(item)
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


def validate_label_lengths(rows: list[dict[str, Any]], tokenizer: Any, split: str) -> None:
    bad: list[tuple[int, int]] = []
    max_seen = 0
    for row in rows:
        length = len(tokenizer(str(row["text"]), truncation=False).input_ids)
        max_seen = max(max_seen, length)
        if length > MAX_LABEL_LENGTH:
            bad.append((int(row.get("_manifest_line", -1)), length))
    LOGGER.info("%s max label tokens=%d", split, max_seen)
    if bad:
        raise ValueError(
            f"{split}: {len(bad)} labels exceed {MAX_LABEL_LENGTH}; "
            f"hidden truncation is forbidden. examples={bad[:8]}"
        )


def log_split_audit(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]]) -> None:
    train_text = {normalize_arabic(str(row["text"])) for row in train_rows}
    eval_text = {normalize_arabic(str(row["text"])) for row in eval_rows}
    LOGGER.info(
        "split audit: train_rows=%d eval_rows=%d train_unique_text=%d "
        "eval_unique_text=%d text_overlap=%d",
        len(train_rows), len(eval_rows), len(train_text), len(eval_text),
        len(train_text & eval_text),
    )
    if len(eval_text) < 25:
        LOGGER.warning(
            "Eval has only %d unique normalized transcripts; this is too narrow "
            "to serve as the final deployment gate.",
            len(eval_text),
        )


class ManifestDataset:
    def __init__(self, rows: list[dict[str, Any]], processor: Any) -> None:
        self.rows = rows
        self.processor = processor

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        audio = load_audio(str(row["audio_path"]))
        duration = len(audio) / SAMPLE_RATE
        if duration > MAX_AUDIO_SECONDS:
            raise ValueError(
                f"Audio {row['audio_path']} is {duration:.3f}s (>30s); "
                "hidden feature truncation is forbidden."
            )
        extracted = self.processor.feature_extractor(
            audio,
            sampling_rate=SAMPLE_RATE,
            return_tensors="np",
            return_attention_mask=True,
            padding="max_length",
            truncation=False,
        )
        labels = self.processor.tokenizer(str(row["text"]), truncation=False).input_ids
        if len(labels) > MAX_LABEL_LENGTH:
            raise ValueError(
                f"Label length {len(labels)} exceeds {MAX_LABEL_LENGTH} at "
                f"{row['audio_path']}"
            )
        return {
            "input_features": extracted.input_features[0],
            "attention_mask": extracted.attention_mask[0],
            "labels": labels,
        }


@dataclass
class SpeechCollator:
    processor: Any
    decoder_start_token_id: int

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        input_features = [
            {
                "input_features": feature["input_features"],
                "attention_mask": feature["attention_mask"],
            }
            for feature in features
        ]
        label_features = [{"input_ids": feature["labels"]} for feature in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )
        if labels.shape[1] and (
            labels[:, 0] == self.decoder_start_token_id
        ).all().item():
            labels = labels[:, 1:]
        batch["labels"] = labels
        return batch


def _repetition_loop(words: list[str]) -> bool:
    if len(words) < 8:
        return False
    longest = current = 1
    for previous, word in zip(words, words[1:]):
        if word == previous:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    if longest >= 8:
        return True
    common = max(Counter(words).values(), default=0)
    return len(words) >= 12 and common / len(words) >= 0.55


def make_metrics(processor: Any):
    import jiwer

    def compute(eval_prediction) -> dict[str, float]:
        prediction_ids = eval_prediction.predictions
        if isinstance(prediction_ids, tuple):
            prediction_ids = prediction_ids[0]
        label_ids = np.array(eval_prediction.label_ids, copy=True)
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        predictions = processor.tokenizer.batch_decode(
            prediction_ids, skip_special_tokens=True
        )
        references = processor.tokenizer.batch_decode(
            label_ids, skip_special_tokens=True
        )
        pred_norm = [normalize_arabic(text) for text in predictions]
        ref_norm = [normalize_arabic(text) for text in references]
        pred_words = [text.split() for text in pred_norm]
        ref_words = [text.split() for text in ref_norm]
        overlong = sum(
            len(pred) > max(12, 3 * max(1, len(ref)))
            for pred, ref in zip(pred_words, ref_words)
        )
        loops = sum(_repetition_loop(words) for words in pred_words)
        samples = max(1, len(predictions))
        return {
            "wer": float(jiwer.wer(ref_norm, pred_norm)),
            "word_count_ratio": float(
                sum(map(len, pred_words)) / max(1, sum(map(len, ref_words)))
            ),
            "overlong_rate": float(overlong / samples),
            "repetition_loop_rate": float(loops / samples),
        }

    return compute


def configure_train_scope(model: Any, scope: str) -> None:
    if scope == "encoder":
        for parameter in model.parameters():
            parameter.requires_grad = False
        for parameter in model.model.encoder.parameters():
            parameter.requires_grad = True
    else:
        for parameter in model.parameters():
            parameter.requires_grad = True
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    LOGGER.info(
        "train_scope=%s trainable=%d total=%d (%.2f%%)",
        scope, trainable, total, 100.0 * trainable / max(1, total),
    )


def release_gate(args: argparse.Namespace, metrics: dict[str, float]) -> dict[str, Any]:
    checks = {
        "word_count_ratio": (
            float(metrics.get("eval_word_count_ratio", float("inf"))),
            float(args.max_eval_word_ratio),
        ),
        "repetition_loop_rate": (
            float(metrics.get("eval_repetition_loop_rate", float("inf"))),
            float(args.max_eval_repetition_loop_rate),
        ),
        "overlong_rate": (
            float(metrics.get("eval_overlong_rate", float("inf"))),
            float(args.max_eval_overlong_rate),
        ),
    }
    result = {
        name: {"value": value, "max": maximum, "pass": value <= maximum}
        for name, (value, maximum) in checks.items()
    }
    return {
        "pass": all(item["pass"] for item in result.values()),
        "checks": result,
        "note": "Collapse-safety only; a new speaker-disjoint phone/amateur test is still required.",
    }


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

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
    if args.label_smoothing_factor < 0:
        raise ValueError("label_smoothing_factor must be >= 0")

    set_seed(args.seed)
    train_rows = read_manifest(args.train_manifest)
    eval_rows = read_manifest(args.eval_manifest)
    LOGGER.info("train rows=%d eval rows=%d", len(train_rows), len(eval_rows))
    log_split_audit(train_rows, eval_rows)

    processor = WhisperProcessor.from_pretrained(args.model_id)
    validate_label_lengths(train_rows, processor.tokenizer, "train")
    validate_label_lengths(eval_rows, processor.tokenizer, "eval")

    model = WhisperForConditionalGeneration.from_pretrained(args.model_id)
    forced_decoder_ids = processor.get_decoder_prompt_ids(language="ar", task="transcribe")
    model.config.forced_decoder_ids = forced_decoder_ids
    model.generation_config.forced_decoder_ids = forced_decoder_ids
    model.config.use_cache = not args.gradient_checkpointing
    configure_train_scope(model, args.train_scope)
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
        eval_strategy="steps",
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
        label_smoothing_factor=args.label_smoothing_factor,
        seed=args.seed,
        data_seed=args.seed,
    )

    callbacks = []
    if args.early_stopping_patience > 0:
        callbacks.append(
            EarlyStoppingCallback(early_stopping_patience=args.early_stopping_patience)
        )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_arguments,
        train_dataset=ManifestDataset(train_rows, processor),
        eval_dataset=ManifestDataset(eval_rows, processor),
        data_collator=SpeechCollator(processor, model.config.decoder_start_token_id),
        compute_metrics=make_metrics(processor),
        processing_class=processor,
        callbacks=callbacks,
    )

    train_result = trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)
    trainer.save_metrics("train", train_result.metrics)
    evaluation_metrics = trainer.evaluate()
    trainer.save_metrics("eval", evaluation_metrics)
    trainer.save_state()

    # Keep the best model for diagnosis even if the safety gate blocks deployment.
    trainer.save_model(args.output_dir)
    processor.save_pretrained(args.output_dir)

    gate = release_gate(args, evaluation_metrics)
    gate_path = Path(args.output_dir) / "qari_release_gate.json"
    gate_path.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("finished: %s", evaluation_metrics)
    LOGGER.info("release gate: %s", gate)

    if not gate["pass"]:
        raise RuntimeError(
            "Qari collapse-safety gate FAILED; do not deploy this checkpoint. "
            f"See {gate_path}."
        )

    LOGGER.info(
        "QARI TRAINING SAFETY GATE: PASS. A new speaker-disjoint phone/amateur "
        "release test is still required."
    )


if __name__ == "__main__":
    main()
