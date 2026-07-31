#!/usr/bin/env python3
"""Evaluate a CTranslate2 Faster-Whisper model on an untouched JSONL manifest."""
from __future__ import annotations

import argparse
import json
import math
import re
import time
from pathlib import Path

import jiwer
import numpy as np
import soundfile as sf
from scipy import signal

SAMPLE_RATE = 16_000
_HARAKAT = re.compile("[\u0618-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_NON_ARABIC = re.compile(r"[^\u0621-\u064A\u0660-\u0669\u066E-\u06D5 ]")
_SPACES = re.compile(r"\s+")


def normalize_arabic(text: str) -> str:
    text = _HARAKAT.sub("", text or "").replace("ـ", "")
    for source, target in {
        "آ": "ا", "أ": "ا", "إ": "ا", "ٱ": "ا", "ى": "ي", "ی": "ي",
        "ؤ": "و", "ئ": "ي", "ء": "", "ة": "ه",
    }.items():
        text = text.replace(source, target)
    return _SPACES.sub(" ", _NON_ARABIC.sub(" ", text)).strip()


def load_audio(path: Path) -> np.ndarray:
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--compute_type", default="int8")
    parser.add_argument("--max_samples", type=int, default=0)
    parser.add_argument("--output_jsonl", default="predictions.jsonl")
    args = parser.parse_args()

    from faster_whisper import WhisperModel

    manifest = Path(args.manifest).expanduser().resolve()
    rows = [
        json.loads(line)
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.max_samples:
        rows = rows[: args.max_samples]
    if not rows:
        raise ValueError(f"No evaluation rows in {manifest}")

    model = WhisperModel(args.model_dir, device="cpu", compute_type=args.compute_type)
    references: list[str] = []
    predictions: list[str] = []
    results: list[dict] = []
    total_audio = 0.0
    total_decode = 0.0

    for index, row in enumerate(rows, 1):
        audio_path = Path(row["audio_path"]).expanduser()
        if not audio_path.is_absolute():
            audio_path = manifest.parent / audio_path
        audio = load_audio(audio_path)
        started = time.perf_counter()
        segments, _ = model.transcribe(
            audio,
            language="ar",
            task="transcribe",
            beam_size=1,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=False,
        )
        prediction = " ".join(segment.text.strip() for segment in segments).strip()
        elapsed = time.perf_counter() - started
        reference_normalized = normalize_arabic(row["text"])
        prediction_normalized = normalize_arabic(prediction)
        references.append(reference_normalized)
        predictions.append(prediction_normalized)
        duration = len(audio) / SAMPLE_RATE
        total_audio += duration
        total_decode += elapsed
        results.append({
            **row,
            "prediction": prediction,
            "reference_normalized": reference_normalized,
            "prediction_normalized": prediction_normalized,
            "decode_seconds": elapsed,
        })
        print(
            f"{index}/{len(rows)} WER={jiwer.wer(references, predictions):.3f} "
            f"RTF={total_decode / max(total_audio, 1e-9):.2f}"
        )

    output = Path(args.output_jsonl).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in results),
        encoding="utf-8",
    )
    print(json.dumps({
        "samples": len(rows),
        "wer": jiwer.wer(references, predictions),
        "audio_seconds": total_audio,
        "decode_seconds": total_decode,
        "rtf": total_decode / max(total_audio, 1e-9),
        "predictions": str(output),
    }, indent=2))


if __name__ == "__main__":
    main()
