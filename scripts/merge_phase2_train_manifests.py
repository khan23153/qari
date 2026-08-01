#!/usr/bin/env python3
"""Mix TLOG real-user and professional/amateur training manifests deterministically.

The input ``base_train_manifest`` is produced by ``prepare_robust_qari_data.py``
and can contain professional, RetaSy-train, and augmented rows. TLOG rows are
training-only. This mixer caps each source so the requested TLOG share is real
rather than being overwhelmed by duplicated professional augmentation.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tlog_manifest", required=True)
    parser.add_argument("--base_train_manifest", required=True)
    parser.add_argument("--output_manifest", required=True)
    parser.add_argument("--tlog_fraction", type=float, default=0.75)
    parser.add_argument("--max_total", type=int, default=0)
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
            audio = Path(str(row.get("audio_path") or "")).expanduser()
            if not audio.is_absolute():
                audio = path.parent / audio
            if not audio.exists():
                raise FileNotFoundError(
                    f"Missing audio at {path}:{line_number}: {audio}"
                )
            text = str(row.get("text") or "").strip()
            if not text:
                raise ValueError(f"Missing text at {path}:{line_number}")
            item = dict(row)
            item["audio_path"] = str(audio.resolve())
            item["text"] = text
            item["split"] = "train"
            rows.append(item)
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(temporary, path)


def main() -> None:
    args = parse_args()
    if not 0.5 <= args.tlog_fraction < 1.0:
        raise ValueError("tlog_fraction must be in [0.5, 1.0)")
    if args.max_total < 0:
        raise ValueError("max_total must be non-negative")

    rng = random.Random(args.seed)
    tlog = read_jsonl(Path(args.tlog_manifest).expanduser().resolve())
    base = read_jsonl(Path(args.base_train_manifest).expanduser().resolve())
    rng.shuffle(tlog)
    rng.shuffle(base)

    if args.max_total:
        target_total = min(args.max_total, len(tlog) + len(base))
        desired_tlog = min(len(tlog), round(target_total * args.tlog_fraction))
        desired_base = min(len(base), target_total - desired_tlog)
        # If one side is short, fill remaining capacity from the other side.
        remaining = target_total - desired_tlog - desired_base
        if remaining:
            extra_tlog = min(len(tlog) - desired_tlog, remaining)
            desired_tlog += extra_tlog
            remaining -= extra_tlog
            desired_base += min(len(base) - desired_base, remaining)
    else:
        # Keep all TLOG and downsample the base corpus to the requested share.
        desired_tlog = len(tlog)
        desired_base = min(
            len(base),
            round(desired_tlog * (1.0 - args.tlog_fraction) / args.tlog_fraction),
        )

    selected = tlog[:desired_tlog] + base[:desired_base]
    rng.shuffle(selected)
    output = Path(args.output_manifest).expanduser().resolve()
    write_jsonl(output, selected)

    counts = Counter(str(row.get("source") or "unknown") for row in selected)
    actual_tlog = sum(1 for row in selected if row.get("source") == "tlog_clean")
    report = {
        "seed": args.seed,
        "requested_tlog_fraction": args.tlog_fraction,
        "rows": len(selected),
        "tlog_rows": actual_tlog,
        "actual_tlog_fraction": round(actual_tlog / len(selected), 4),
        "sources": dict(counts),
        "output_manifest": str(output),
    }
    report_path = output.with_suffix(".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
