#!/usr/bin/env python3
"""Build phase-two manifests from TLOG, professional anchors, and RetaSy.

TLOG is training-only because its public rows do not provide a stable speaker
identifier. RetaSy supplies speaker-disjoint evaluation and test speakers.
Local phone recordings can be appended to test through the existing robust-data
builder later, but are deliberately excluded from this first training build.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tlog_manifest", required=True)
    parser.add_argument("--professional_manifest", required=True)
    parser.add_argument("--retasy_manifest", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--professional_ratio", type=float, default=0.25)
    parser.add_argument("--retasy_train_ratio", type=float, default=0.10)
    parser.add_argument("--eval_speaker_fraction", type=float, default=0.15)
    parser.add_argument("--test_speaker_fraction", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            audio_path = Path(str(row.get("audio_path") or "")).expanduser()
            if not audio_path.is_absolute():
                audio_path = path.parent / audio_path
            if not audio_path.exists():
                raise FileNotFoundError(f"Missing audio at {path}:{line_number}: {audio_path}")
            text = str(row.get("text") or row.get("normalized_text") or "").strip()
            if not text:
                raise ValueError(f"Missing text at {path}:{line_number}")
            row["audio_path"] = str(audio_path.resolve())
            row["text"] = text
            rows.append(row)
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(path)


def sample_count_for_ratio(primary_count: int, ratio: float) -> int:
    if ratio <= 0:
        return 0
    if ratio >= 1:
        raise ValueError("Ratios must be below 1")
    return round(primary_count * ratio / (1.0 - ratio))


def main() -> None:
    args = parse_args()
    if args.professional_ratio < 0 or args.retasy_train_ratio < 0:
        raise ValueError("Training ratios must be non-negative")
    if args.professional_ratio + args.retasy_train_ratio >= 0.6:
        raise ValueError("Keep TLOG as the clear training majority")
    if not 0 < args.eval_speaker_fraction < 1 or not 0 < args.test_speaker_fraction < 1:
        raise ValueError("Evaluation/test speaker fractions must be in (0, 1)")
    if args.eval_speaker_fraction + args.test_speaker_fraction >= 1:
        raise ValueError("Evaluation + test fractions must be below 1")

    rng = random.Random(args.seed)
    tlog = read_jsonl(Path(args.tlog_manifest).expanduser().resolve())
    professional = read_jsonl(Path(args.professional_manifest).expanduser().resolve())
    retasy = read_jsonl(Path(args.retasy_manifest).expanduser().resolve())

    # Every RetaSy row must carry a stable speaker ID. This is the protection
    # against the misleading clip-random split used in phase one.
    by_speaker: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in retasy:
        speaker = str(row.get("speaker_id") or row.get("reciter_id") or "").strip()
        if not speaker or speaker.lower() == "unknown":
            continue
        row["speaker_id"] = speaker
        by_speaker[speaker].append(row)
    speakers = sorted(by_speaker)
    rng.shuffle(speakers)
    if len(speakers) < 5:
        raise RuntimeError("At least five RetaSy speakers are required")

    test_count = max(1, round(len(speakers) * args.test_speaker_fraction))
    eval_count = max(1, round(len(speakers) * args.eval_speaker_fraction))
    if test_count + eval_count >= len(speakers):
        raise RuntimeError("Not enough RetaSy speakers for disjoint train/eval/test")
    test_speakers = set(speakers[:test_count])
    eval_speakers = set(speakers[test_count:test_count + eval_count])
    train_speakers = set(speakers[test_count + eval_count:])

    retasy_train = [row for speaker in train_speakers for row in by_speaker[speaker]]
    evaluation = [row for speaker in eval_speakers for row in by_speaker[speaker]]
    test = [row for speaker in test_speakers for row in by_speaker[speaker]]

    rng.shuffle(professional)
    rng.shuffle(retasy_train)
    professional_target = min(
        len(professional), sample_count_for_ratio(len(tlog), args.professional_ratio)
    )
    retasy_target = min(
        len(retasy_train), sample_count_for_ratio(len(tlog), args.retasy_train_ratio)
    )

    train = list(tlog) + professional[:professional_target] + retasy_train[:retasy_target]
    for row in train:
        row["split"] = "train"
    for row in evaluation:
        row["split"] = "eval"
    for row in test:
        row["split"] = "test"
    rng.shuffle(train)
    rng.shuffle(evaluation)
    rng.shuffle(test)

    output = Path(args.output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "train_manifest.jsonl", train)
    write_jsonl(output / "eval_manifest.jsonl", evaluation)
    write_jsonl(output / "test_manifest.jsonl", test)

    report = {
        "seed": args.seed,
        "counts": {"train": len(train), "eval": len(evaluation), "test": len(test)},
        "training_sources": dict(Counter(str(row.get("source") or "unknown") for row in train)),
        "speaker_counts": {
            "retasy_train": len(train_speakers),
            "eval": len(eval_speakers),
            "test": len(test_speakers),
        },
        "tlog_training_only": True,
    }
    (output / "dataset_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
