#!/usr/bin/env python3
"""Build phase-two Quran ASR manifests with phone/noise augmentation.

The script combines:
- an existing professional-reciter manifest (training only),
- optional correctly-labelled RetaSy amateur recordings,
- optional local phone recordings described by JSONL metadata,
- optional background noises and room impulse responses.

Amateur speakers are split by speaker ID, not by clip. Evaluation and test
recordings are always left clean. The output is three explicit manifests for
``ml.training.finetune_whisper_robust``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import soundfile as sf
from scipy import signal

SAMPLE_RATE = 16_000
AUDIO_SUFFIXES = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac", ".amr", ".opus"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--professional_manifest", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--include_retasy", action="store_true")
    parser.add_argument("--retasy_max_samples", type=int, default=6000)
    parser.add_argument("--phone_metadata", default=None)
    parser.add_argument("--noise_dir", default=None)
    parser.add_argument("--rir_dir", default=None)
    parser.add_argument("--augment_copies", type=int, default=1)
    parser.add_argument("--max_professional", type=int, default=0)
    parser.add_argument("--amateur_eval_fraction", type=float, default=0.15)
    parser.add_argument("--amateur_test_fraction", type=float, default=0.15)
    parser.add_argument("--min_duration", type=float, default=0.6)
    parser.add_argument("--max_duration", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(temporary, path)


def stable_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def find_audio_files(root: str | None) -> list[Path]:
    if not root:
        return []
    directory = Path(root).expanduser().resolve()
    if not directory.exists():
        raise FileNotFoundError(directory)
    return sorted(
        path for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
    )


def ffmpeg_decode(path: Path) -> tuple[np.ndarray, int]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(f"Install FFmpeg to decode {path.suffix} files")
    with tempfile.TemporaryDirectory() as temporary_directory:
        wav_path = Path(temporary_directory) / "decoded.wav"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(path), "-ac", "1", "-ar", str(SAMPLE_RATE),
                "-sample_fmt", "flt", str(wav_path),
            ],
            check=True,
        )
        audio, sample_rate = sf.read(
            wav_path, dtype="float32", always_2d=False
        )
    return np.asarray(audio, dtype=np.float32), int(sample_rate)


def load_audio(path: str | Path) -> np.ndarray:
    audio_path = Path(path).expanduser().resolve()
    try:
        audio, sample_rate = sf.read(
            audio_path, dtype="float32", always_2d=False
        )
    except Exception:
        audio, sample_rate = ffmpeg_decode(audio_path)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sample_rate != SAMPLE_RATE:
        divisor = math.gcd(int(sample_rate), SAMPLE_RATE)
        audio = signal.resample_poly(
            audio, SAMPLE_RATE // divisor, int(sample_rate) // divisor
        ).astype(np.float32)
    audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 1.0:
        audio = audio / peak
    return audio.astype(np.float32)


def save_wav(path: Path, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.wav")
    sf.write(
        temporary,
        np.clip(np.asarray(audio, dtype=np.float32), -0.999, 0.999),
        SAMPLE_RATE,
        subtype="PCM_16",
    )
    os.replace(temporary, path)


def valid_duration(audio: np.ndarray, minimum: float, maximum: float) -> bool:
    duration = len(audio) / SAMPLE_RATE
    return minimum <= duration <= maximum


def rms(audio: np.ndarray) -> float:
    if not audio.size:
        return 0.0
    return float(np.sqrt(np.mean(np.square(audio, dtype=np.float64)) + 1e-12))


def fit_noise(noise: np.ndarray, length: int, rng: np.random.Generator) -> np.ndarray:
    if not noise.size:
        return np.zeros(length, dtype=np.float32)
    if len(noise) >= length:
        start = int(rng.integers(0, len(noise) - length + 1))
        return noise[start:start + length]
    return np.tile(noise, math.ceil(length / len(noise)))[:length]


def synthetic_noise(length: int, rng: np.random.Generator) -> np.ndarray:
    white = rng.normal(0, 1, length).astype(np.float32)
    if rng.random() < 0.5:
        return white
    numerator, denominator = signal.butter(1, 0.12)
    return signal.lfilter(numerator, denominator, white).astype(np.float32)


def mix_noise(
    clean: np.ndarray,
    noise: np.ndarray,
    snr_db: float,
    rng: np.random.Generator,
) -> np.ndarray:
    noise = fit_noise(noise, len(clean), rng)
    scale = max(rms(clean), 1e-5) / (
        max(rms(noise), 1e-5) * (10.0 ** (snr_db / 20.0))
    )
    return (clean + noise * scale).astype(np.float32)


def synthetic_rir(rng: np.random.Generator) -> np.ndarray:
    length = int(rng.uniform(0.12, 0.50) * SAMPLE_RATE)
    times = np.arange(length) / SAMPLE_RATE
    decay = np.exp(-times / rng.uniform(0.06, 0.22))
    response = np.zeros(length, dtype=np.float32)
    response[0] = 1.0
    for _ in range(int(rng.integers(5, 18))):
        index = int(rng.integers(1, length))
        response[index] += float(rng.uniform(-0.5, 0.5)) * decay[index]
    return response


def apply_rir(audio: np.ndarray, response: np.ndarray) -> np.ndarray:
    if not response.size:
        return audio
    response = response[int(np.argmax(np.abs(response))): SAMPLE_RATE * 2]
    response = response / (
        np.sqrt(np.sum(response.astype(np.float64) ** 2)) + 1e-8
    )
    return signal.fftconvolve(audio, response, mode="full")[:len(audio)].astype(np.float32)


def phone_simulation(audio: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    low = float(rng.uniform(180, 350))
    high = min(float(rng.uniform(3200, 4800)), SAMPLE_RATE * 0.46)
    filters = signal.butter(
        4, [low, high], btype="bandpass", fs=SAMPLE_RATE, output="sos"
    )
    output = signal.sosfilt(filters, audio).astype(np.float32)
    reduced_rate = int(rng.choice([8000, 12000]))
    first = math.gcd(SAMPLE_RATE, reduced_rate)
    output = signal.resample_poly(
        output, reduced_rate // first, SAMPLE_RATE // first
    )
    second = math.gcd(reduced_rate, SAMPLE_RATE)
    output = signal.resample_poly(
        output, SAMPLE_RATE // second, reduced_rate // second
    ).astype(np.float32)
    output = output[:len(audio)] if len(output) >= len(audio) else np.pad(
        output, (0, len(audio) - len(output))
    )
    drive = float(rng.uniform(1.2, 2.8))
    output = np.tanh(drive * output) / np.tanh(drive)
    output += rng.normal(0, rng.uniform(0.0003, 0.0025), len(output))
    return output.astype(np.float32)


def augment(
    audio: np.ndarray,
    rng: np.random.Generator,
    noise_files: list[Path],
    rir_files: list[Path],
) -> tuple[np.ndarray, list[str]]:
    output = audio.copy() * (10.0 ** (float(rng.uniform(-8, 5)) / 20.0))
    operations: list[str] = []
    if rng.random() < 0.65:
        response = load_audio(rng.choice(rir_files)) if rir_files else synthetic_rir(rng)
        output = apply_rir(output, response)
        operations.append("rir")
    if rng.random() < 0.85:
        noise = load_audio(rng.choice(noise_files)) if noise_files else synthetic_noise(len(output), rng)
        snr_db = float(rng.uniform(8, 25))
        output = mix_noise(output, noise, snr_db, rng)
        operations.append(f"noise@{snr_db:.1f}dB")
    if rng.random() < 0.75:
        output = phone_simulation(output, rng)
        operations.append("phone")
    leading = int(rng.uniform(0, 0.45) * SAMPLE_RATE)
    trailing = int(rng.uniform(0, 0.55) * SAMPLE_RATE)
    output = np.pad(output, (leading, trailing))
    operations.append(f"silence={leading / SAMPLE_RATE:.2f}/{trailing / SAMPLE_RATE:.2f}s")
    peak = float(np.max(np.abs(output))) if output.size else 0.0
    if peak > 0.98:
        output = 0.98 * output / peak
    return output.astype(np.float32), operations


def resolve_audio(row: dict[str, Any], manifest: Path) -> Path:
    value = row.get("audio_path") or (row.get("audio") or {}).get("path")
    if not value:
        raise ValueError("Manifest row has no audio path")
    path = Path(value).expanduser()
    return (manifest.parent / path).resolve() if not path.is_absolute() else path.resolve()


def load_professional(args: argparse.Namespace, rng: random.Random) -> list[dict[str, Any]]:
    manifest = Path(args.professional_manifest).expanduser().resolve()
    rows = read_jsonl(manifest)
    rng.shuffle(rows)
    if args.max_professional:
        rows = rows[:args.max_professional]
    output = []
    for row in rows:
        audio_path = resolve_audio(row, manifest)
        text = str(row.get("text") or row.get("normalized_text") or "").strip()
        if not audio_path.exists() or not text:
            continue
        reciter = str(row.get("reciter") or "professional_unknown")
        output.append({
            "audio_path": str(audio_path),
            "text": text,
            "speaker_id": f"pro:{reciter}",
            "source": "professional",
            "surah": row.get("surah"),
            "ayah": row.get("ayah"),
            "split": "train",
            "augmentation": "clean",
        })
    return output


def import_retasy(args: argparse.Namespace, output_root: Path, rng: random.Random) -> list[dict[str, Any]]:
    if not args.include_retasy:
        return []
    from datasets import load_dataset

    dataset = load_dataset("RetaSy/quranic_audio_dataset", split="train")
    indices = list(range(len(dataset)))
    rng.shuffle(indices)
    accepted = []
    for index in indices:
        row = dataset[index]
        # A reviewed/golden flag alone does not mean the recitation is correct.
        if str(row.get("final_label") or "").strip().lower() != "correct":
            continue
        speaker = str(row.get("reciter_id") or "").strip()
        text = str(row.get("Aya") or row.get("text") or "").strip()
        if not speaker or speaker.lower() == "unknown" or not text:
            continue
        audio_value = row.get("audio")
        try:
            if isinstance(audio_value, dict) and audio_value.get("array") is not None:
                audio = np.asarray(audio_value["array"], dtype=np.float32)
                sample_rate = int(audio_value["sampling_rate"])
                if sample_rate != SAMPLE_RATE:
                    divisor = math.gcd(sample_rate, SAMPLE_RATE)
                    audio = signal.resample_poly(
                        audio, SAMPLE_RATE // divisor, sample_rate // divisor
                    ).astype(np.float32)
            elif isinstance(audio_value, dict) and audio_value.get("path"):
                audio = load_audio(audio_value["path"])
            else:
                raise TypeError("Unsupported Hugging Face audio value")
            if not valid_duration(audio, args.min_duration, args.max_duration):
                continue
        except Exception as exc:
            print(f"skip RetaSy row {index}: {exc}")
            continue
        destination = output_root / "amateur_clean" / speaker / f"{stable_id(speaker, str(index), text)}.wav"
        save_wav(destination, audio)
        accepted.append({
            "audio_path": str(destination.resolve()),
            "text": text,
            "speaker_id": f"amateur:{speaker}",
            "source": "retasy_amateur",
            "split": None,
            "augmentation": "clean",
        })
        if args.retasy_max_samples and len(accepted) >= args.retasy_max_samples:
            break
    return accepted


def import_phone(args: argparse.Namespace, output_root: Path) -> list[dict[str, Any]]:
    if not args.phone_metadata:
        return []
    metadata = Path(args.phone_metadata).expanduser().resolve()
    output = []
    for index, row in enumerate(read_jsonl(metadata), 1):
        source = Path(str(row["audio_path"])).expanduser()
        if not source.is_absolute():
            source = metadata.parent / source
        text = str(row.get("text") or "").strip()
        speaker = str(row.get("speaker_id") or "").strip()
        split_name = str(row.get("split") or "test").strip().lower()
        if split_name not in {"train", "eval", "test"}:
            raise ValueError(f"Invalid split at {metadata}:{index}")
        if not text or not speaker:
            raise ValueError(f"Missing text or speaker_id at {metadata}:{index}")
        audio = load_audio(source)
        if not valid_duration(audio, args.min_duration, args.max_duration):
            print(f"skip phone recording outside duration range: {source}")
            continue
        destination = output_root / "phone_clean" / speaker / f"{stable_id(speaker, str(source), text)}.wav"
        save_wav(destination, audio)
        output.append({
            "audio_path": str(destination.resolve()),
            "text": text,
            "speaker_id": f"phone:{speaker}",
            "source": "local_phone",
            "split": split_name,
            "augmentation": "clean",
        })
    return output


def assign_speaker_splits(rows: list[dict[str, Any]], args: argparse.Namespace, rng: random.Random) -> None:
    speakers = sorted({row["speaker_id"] for row in rows})
    rng.shuffle(speakers)
    if len(speakers) < 3:
        raise RuntimeError("At least three amateur speakers are required")
    test_count = max(1, round(len(speakers) * args.amateur_test_fraction))
    eval_count = max(1, round(len(speakers) * args.amateur_eval_fraction))
    if test_count + eval_count >= len(speakers):
        test_count = eval_count = 1
    test_speakers = set(speakers[:test_count])
    eval_speakers = set(speakers[test_count:test_count + eval_count])
    for row in rows:
        speaker = row["speaker_id"]
        row["split"] = "test" if speaker in test_speakers else "eval" if speaker in eval_speakers else "train"


def validate_no_leak(train: list[dict[str, Any]], evaluation: list[dict[str, Any]], test: list[dict[str, Any]]) -> None:
    speakers = {
        "train": {row["speaker_id"] for row in train if row["source"] != "professional"},
        "eval": {row["speaker_id"] for row in evaluation},
        "test": {row["speaker_id"] for row in test},
    }
    for left, right in (("train", "eval"), ("train", "test"), ("eval", "test")):
        overlap = speakers[left] & speakers[right]
        if overlap:
            raise RuntimeError(f"Speaker leakage between {left} and {right}: {sorted(overlap)[:5]}")


def main() -> None:
    args = parse_args()
    if args.augment_copies < 0:
        raise ValueError("augment_copies must be non-negative")
    if not 0 <= args.amateur_eval_fraction < 1 or not 0 <= args.amateur_test_fraction < 1:
        raise ValueError("split fractions must be in [0, 1)")
    if args.amateur_eval_fraction + args.amateur_test_fraction >= 1:
        raise ValueError("eval + test fractions must be less than 1")

    output_root = Path(args.output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    python_rng = random.Random(args.seed)
    noise_files = find_audio_files(args.noise_dir)
    rir_files = find_audio_files(args.rir_dir)

    professional = load_professional(args, python_rng)
    amateur = import_retasy(args, output_root, python_rng)
    if amateur:
        assign_speaker_splits(amateur, args, python_rng)
    phone = import_phone(args, output_root)

    clean_rows = professional + amateur + phone
    train_clean = [row for row in clean_rows if row["split"] == "train"]
    evaluation = [row for row in clean_rows if row["split"] == "eval"]
    test = [row for row in clean_rows if row["split"] == "test"]

    augmented = []
    for index, row in enumerate(train_clean):
        clean = load_audio(row["audio_path"])
        for copy_index in range(args.augment_copies):
            seed = int(stable_id(str(args.seed), row["audio_path"], str(copy_index)), 16) % (2**32)
            audio, operations = augment(
                clean, np.random.default_rng(seed), noise_files, rir_files
            )
            destination = output_root / "augmented" / row["source"] / f"{stable_id(row['audio_path'], str(copy_index), ','.join(operations))}.wav"
            save_wav(destination, audio)
            new_row = dict(row)
            new_row.update({
                "audio_path": str(destination.resolve()),
                "source": f"{row['source']}_augmented",
                "augmentation": operations,
                "parent_audio_path": row["audio_path"],
                "split": "train",
            })
            augmented.append(new_row)
        if (index + 1) % 500 == 0:
            print(f"augmented {index + 1}/{len(train_clean)}")

    train = train_clean + augmented
    python_rng.shuffle(train)
    python_rng.shuffle(evaluation)
    python_rng.shuffle(test)
    if not train:
        raise RuntimeError("No training rows were produced")
    if not evaluation:
        raise RuntimeError("No evaluation rows; add unseen amateur/phone eval speakers")
    if not test:
        raise RuntimeError("No test rows; add unseen amateur/phone test speakers")
    validate_no_leak(train, evaluation, test)

    write_jsonl(output_root / "train_manifest.jsonl", train)
    write_jsonl(output_root / "eval_manifest.jsonl", evaluation)
    write_jsonl(output_root / "test_manifest.jsonl", test)
    report = {
        "seed": args.seed,
        "counts": {
            "train_clean": len(train_clean),
            "train_augmented": len(augmented),
            "train_total": len(train),
            "eval": len(evaluation),
            "test": len(test),
        },
        "sources_train": dict(Counter(row["source"] for row in train)),
        "sources_eval": dict(Counter(row["source"] for row in evaluation)),
        "sources_test": dict(Counter(row["source"] for row in test)),
        "speakers": {
            "train": len({row["speaker_id"] for row in train}),
            "eval": len({row["speaker_id"] for row in evaluation}),
            "test": len({row["speaker_id"] for row in test}),
        },
        "noise_files": len(noise_files),
        "rir_files": len(rir_files),
    }
    (output_root / "dataset_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
