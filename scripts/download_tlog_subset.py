#!/usr/bin/env python3
"""Download a bounded, balanced subset of Tarteel TLOG for Quran ASR training.

The official dataset is gated and very large. This importer streams only the
``clean`` split, keeps requested Surahs, caps samples per Ayah, verifies the
filename-derived label against the repository's Quran corpus, converts accepted
audio to mono 16 kHz PCM WAV, and writes a resumable JSONL manifest.

TLOG does not expose a stable speaker identifier, so every imported clip is
training-only. Use RetaSy/local recordings for speaker-disjoint eval/test.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy import signal

SAMPLE_RATE = 16_000
REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_GZ = REPO_ROOT / "mobile" / "assets" / "quran_corpus.json.gz"
AUDIO_NAME = re.compile(
    r"(?P<surah>\d{1,3})_(?P<ayah>\d{1,3})_(?P<clip>[^/\\.]+)\.(?:wav|flac|mp3|ogg|m4a|aac|opus)$",
    re.IGNORECASE,
)
_HARAKAT = re.compile("[\u0618-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_NON_ARABIC = re.compile(r"[^\u0621-\u064A\u0660-\u0669\u066E-\u06D5 ]")
_SPACES = re.compile(r"\s+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--surahs", default="1-20")
    parser.add_argument("--max_samples", type=int, default=20_000)
    parser.add_argument("--max_per_ayah", type=int, default=12)
    parser.add_argument("--max_scan_rows", type=int, default=450_000)
    parser.add_argument("--shuffle_buffer", type=int, default=10_000)
    parser.add_argument("--min_duration", type=float, default=0.6)
    parser.add_argument("--max_duration", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--verify_label",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require TLOG label to normalize to the repository Quran text.",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    return parser.parse_args()


def parse_surahs(spec: str) -> set[int]:
    values: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            values.update(range(int(left), int(right) + 1))
        else:
            values.add(int(part))
    invalid = sorted(value for value in values if not 1 <= value <= 114)
    if invalid:
        raise ValueError(f"Invalid Surah numbers: {invalid}")
    if not values:
        raise ValueError("No Surahs selected")
    return values


def normalize_arabic(text: str) -> str:
    text = _HARAKAT.sub("", text or "").replace("ـ", "")
    for source, target in {
        "آ": "ا", "أ": "ا", "إ": "ا", "ٱ": "ا", "ى": "ي", "ی": "ي",
        "ؤ": "و", "ئ": "ي", "ء": "", "ة": "ه",
    }.items():
        text = text.replace(source, target)
    return _SPACES.sub(" ", _NON_ARABIC.sub(" ", text)).strip()


def load_corpus() -> dict[tuple[int, int], str]:
    if not CORPUS_GZ.exists():
        raise FileNotFoundError(f"Bundled Quran corpus not found: {CORPUS_GZ}")
    with gzip.open(CORPUS_GZ, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    result: dict[tuple[int, int], str] = {}
    for surah in payload["surahs"]:
        for ayah in surah["ayahs"]:
            result[(int(ayah["surah_number"]), int(ayah["ayah_number"]))] = str(
                ayah["ayah_text"]
            ).strip()
    return result


def parse_audio_name(path_value: str | None) -> tuple[int, int, str] | None:
    if not path_value:
        return None
    match = AUDIO_NAME.search(Path(path_value).name)
    if not match:
        return None
    return (
        int(match.group("surah")),
        int(match.group("ayah")),
        match.group("clip"),
    )


def resample_mono(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    output = np.asarray(audio, dtype=np.float32)
    if output.ndim > 1:
        output = output.mean(axis=1)
    if sample_rate != SAMPLE_RATE:
        divisor = math.gcd(int(sample_rate), SAMPLE_RATE)
        output = signal.resample_poly(
            output, SAMPLE_RATE // divisor, int(sample_rate) // divisor
        ).astype(np.float32)
    output = np.nan_to_num(output, nan=0.0, posinf=0.0, neginf=0.0)
    peak = float(np.max(np.abs(output))) if output.size else 0.0
    if peak > 1.0:
        output = output / peak
    return output.astype(np.float32)


def decode_with_ffmpeg(raw: bytes, suffix: str) -> tuple[np.ndarray, int]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required for audio formats SoundFile cannot decode")
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary) / f"source{suffix or '.audio'}"
        target = Path(temporary) / "decoded.wav"
        source.write_bytes(raw)
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(source), "-ac", "1", "-ar", str(SAMPLE_RATE),
                "-sample_fmt", "flt", str(target),
            ],
            check=True,
        )
        audio, sample_rate = sf.read(target, dtype="float32", always_2d=False)
    return np.asarray(audio, dtype=np.float32), int(sample_rate)


def decode_audio(audio_value: Any) -> np.ndarray:
    if not isinstance(audio_value, dict):
        raise TypeError("TLOG audio field is not a dictionary")
    if audio_value.get("array") is not None:
        sample_rate = int(
            audio_value.get("sampling_rate") or audio_value.get("sample_rate") or 0
        )
        if sample_rate <= 0:
            raise ValueError("Decoded TLOG audio has no sample rate")
        return resample_mono(np.asarray(audio_value["array"], dtype=np.float32), sample_rate)

    path_value = str(audio_value.get("path") or "")
    raw = audio_value.get("bytes")
    if raw is not None:
        try:
            audio, sample_rate = sf.read(
                io.BytesIO(raw), dtype="float32", always_2d=False
            )
        except Exception:
            audio, sample_rate = decode_with_ffmpeg(
                bytes(raw), Path(path_value).suffix.lower()
            )
        return resample_mono(np.asarray(audio, dtype=np.float32), int(sample_rate))

    if path_value and Path(path_value).exists():
        audio, sample_rate = sf.read(
            path_value, dtype="float32", always_2d=False
        )
        return resample_mono(np.asarray(audio, dtype=np.float32), int(sample_rate))
    raise ValueError("TLOG audio row contains neither bytes, array, nor a local path")


def write_wav(path: Path, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.wav")
    sf.write(
        temporary,
        np.clip(np.asarray(audio, dtype=np.float32), -0.999, 0.999),
        SAMPLE_RATE,
        subtype="PCM_16",
    )
    os.replace(temporary, path)


def stable_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:20]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(temporary, path)


def main() -> None:
    args = parse_args()
    if args.max_samples < 1 or args.max_per_ayah < 1:
        raise ValueError("max_samples and max_per_ayah must be positive")
    if args.max_scan_rows < args.max_samples:
        raise ValueError("max_scan_rows must be at least max_samples")
    if not 0 <= args.min_duration < args.max_duration:
        raise ValueError("Invalid duration range")

    selected_surahs = parse_surahs(args.surahs)
    corpus = load_corpus()
    output_root = Path(args.output_dir).expanduser().resolve()
    audio_root = output_root / "audio"
    manifest_path = output_root / "manifest.jsonl"
    report_path = output_root / "dataset_report.json"
    output_root.mkdir(parents=True, exist_ok=True)

    existing = read_jsonl(manifest_path) if args.resume else []
    if not args.resume and output_root.exists():
        shutil.rmtree(audio_root, ignore_errors=True)
        manifest_path.unlink(missing_ok=True)
        existing = []

    accepted_ids: set[str] = set()
    per_ayah: Counter[tuple[int, int]] = Counter()
    valid_existing: list[dict[str, Any]] = []
    for row in existing:
        path = Path(str(row.get("audio_path") or ""))
        if not path.is_absolute():
            path = manifest_path.parent / path
        key = str(row.get("clip_id") or "")
        surah = int(row.get("surah") or 0)
        ayah = int(row.get("ayah") or 0)
        if key and path.exists() and surah in selected_surahs:
            accepted_ids.add(key)
            per_ayah[(surah, ayah)] += 1
            valid_existing.append(row)
    if len(valid_existing) != len(existing):
        with manifest_path.open("w", encoding="utf-8") as handle:
            for row in valid_existing:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    if len(valid_existing) >= args.max_samples:
        print(f"TLOG subset already complete: {len(valid_existing)} rows")
        return

    try:
        from datasets import Audio, load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "Install datasets and huggingface_hub before importing TLOG"
        ) from exc

    token = os.environ.get("HF_TOKEN") or True
    try:
        dataset = load_dataset(
            "tarteel-ai/tlog",
            split="clean",
            streaming=True,
            token=token,
        )
        dataset = dataset.cast_column("audio", Audio(decode=False))
        dataset = dataset.shuffle(seed=args.seed, buffer_size=args.shuffle_buffer)
    except Exception as exc:
        raise RuntimeError(
            "Unable to open gated tarteel-ai/tlog. Accept its access terms and "
            "run `hf auth login` on this machine."
        ) from exc

    counters: Counter[str] = Counter()
    scanned = 0
    accepted = len(valid_existing)
    with manifest_path.open("a", encoding="utf-8") as manifest:
        for row in dataset:
            scanned += 1
            if scanned > args.max_scan_rows or accepted >= args.max_samples:
                break
            counters["scanned"] += 1

            audio_value = row.get("audio")
            path_value = (
                str(audio_value.get("path") or "")
                if isinstance(audio_value, dict)
                else ""
            )
            parsed = parse_audio_name(path_value)
            if parsed is None:
                counters["invalid_filename"] += 1
                continue
            surah, ayah, source_clip = parsed
            if surah not in selected_surahs:
                counters["outside_surah_range"] += 1
                continue
            reference_text = corpus.get((surah, ayah))
            if not reference_text:
                counters["missing_corpus_reference"] += 1
                continue
            if per_ayah[(surah, ayah)] >= args.max_per_ayah:
                counters["ayah_cap_reached"] += 1
                continue

            label = str(row.get("label") or "").strip()
            if args.verify_label and normalize_arabic(label) != normalize_arabic(reference_text):
                counters["label_mismatch"] += 1
                continue

            clip_id = stable_id(str(surah), str(ayah), source_clip, path_value)
            if clip_id in accepted_ids:
                counters["duplicate"] += 1
                continue

            try:
                audio = decode_audio(audio_value)
            except Exception as exc:
                counters["decode_error"] += 1
                if counters["decode_error"] <= 10:
                    print(f"skip decode error {path_value}: {exc}")
                continue
            duration = len(audio) / SAMPLE_RATE
            if not args.min_duration <= duration <= args.max_duration:
                counters["duration_rejected"] += 1
                continue
            if not audio.size or float(np.max(np.abs(audio))) < 1e-5:
                counters["silent"] += 1
                continue

            destination = audio_root / f"s{surah:03d}" / f"a{ayah:03d}" / f"{clip_id}.wav"
            write_wav(destination, audio)
            manifest_row = {
                "audio_path": str(destination.resolve()),
                "text": reference_text,
                "speaker_id": "tlog:unknown",
                "source": "tlog_clean",
                "surah": surah,
                "ayah": ayah,
                "split": "train",
                "augmentation": "clean",
                "clip_id": clip_id,
                "source_path": path_value,
                "duration_seconds": round(duration, 3),
            }
            manifest.write(json.dumps(manifest_row, ensure_ascii=False) + "\n")
            manifest.flush()
            accepted_ids.add(clip_id)
            per_ayah[(surah, ayah)] += 1
            accepted += 1
            counters["accepted"] += 1
            if accepted % 100 == 0:
                print(
                    f"accepted={accepted}/{args.max_samples} scanned={scanned} "
                    f"covered_ayahs={len(per_ayah)}"
                )

    report = {
        "dataset": "tarteel-ai/tlog",
        "split": "clean",
        "surahs": sorted(selected_surahs),
        "seed": args.seed,
        "max_samples": args.max_samples,
        "max_per_ayah": args.max_per_ayah,
        "accepted_total": accepted,
        "scanned_this_run": scanned,
        "covered_ayahs": len(per_ayah),
        "counts": dict(counters),
        "per_surah": dict(
            sorted(
                Counter(
                    surah
                    for (surah, _ayah), count in per_ayah.items()
                    for _ in range(count)
                ).items()
            )
        ),
        "manifest": str(manifest_path),
    }
    write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if accepted == 0:
        raise RuntimeError("No TLOG rows were accepted")
    if accepted < args.max_samples:
        print(
            "Warning: requested sample target was not reached. Increase "
            "--max_scan_rows or lower --max_per_ayah only after reviewing the report."
        )


if __name__ == "__main__":
    main()
