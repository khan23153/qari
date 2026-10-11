"""Validate and balance existing Kaggle phone-ASR pilot manifests."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

from ml.training.finetune_whisper_robust import normalize_arabic


def _metadata_rows(root: Path, name: str) -> list[dict]:
    return [json.loads(line) for line in (root / name).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _filename_label(row: dict) -> bool:
    # TLOG's clean split validates filenames/audio, not the spoken transcript.
    # A boolean clean/verified flag does not supply independent label evidence.
    return any(str(row.get(key) or "").lower().startswith("tlog")
               for key in ("source", "phase3_role"))


def _lineage_keys(root: Path, row: dict) -> set[tuple[str, str]]:
    keys = {("path", str((root / str(row.get("audio_path") or "")).resolve()))}
    if row.get("parent_audio_path"):
        keys.add(("path", str((root / str(row["parent_audio_path"])).resolve())))
    if row.get("clip_id"):
        keys.add(("clip", str(row["clip_id"])))
    return keys


def _partition_labels(root: Path, rows: list[dict], *, related: list[dict] | None = None) -> tuple[list[dict], list[dict]]:
    all_rows = rows + (related or [])
    unsafe = set().union(*(_lineage_keys(root, r) for r in all_rows if _filename_label(r)))
    # Propagate to descendants regardless of row order or an altered source tag.
    while True:
        expanded = set(unsafe)
        for row in all_rows:
            keys = _lineage_keys(root, row)
            if keys & unsafe:
                expanded.update(keys)
        if expanded == unsafe:
            break
        unsafe = expanded
    approved, quarantined = [], []
    for row in rows:
        if _lineage_keys(root, row) & unsafe:
            reason = "filename_label_unvalidated" if _filename_label(row) else "unvalidated_label_lineage"
            quarantined.append(dict(row, quarantine_reason=reason))
        else:
            approved.append(row)
    return approved, quarantined


def _read_rows(root: Path, name: str, metadata: list[dict] | None = None) -> list[dict]:
    rows = []
    for row in _metadata_rows(root, name) if metadata is None else metadata:
        text = str(row.get("text") or "").strip()
        if not normalize_arabic(text):
            raise ValueError("A spoken transcript is required; expected verse text is not a label")
        path = (root / str(row.get("audio_path") or "")).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Audio outside dataset: {path.name}")
        if not path.is_file():
            raise FileNotFoundError(f"Missing audio: {path}")
        info = sf.info(path)
        if not 0.6 <= info.duration <= 30.0:
            raise ValueError(f"Unsupported audio duration: {path.name}: {info.duration}")
        audio, _ = sf.read(path, dtype="float32")
        if not np.isfinite(audio).all() or not np.any(np.abs(audio) > 1e-5):
            raise ValueError(f"Silent/non-finite audio cannot have a speech label: {path.name}")
        row = dict(row)
        row["audio_path"] = str(path)
        row["text"] = text
        row["_audio_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(row)
    if not rows:
        raise ValueError(f"Empty manifest: {name}")
    return rows


def _speaker(row: dict) -> str:
    speaker = str(row.get("speaker_id") or "").strip()
    tail = speaker.lower().rsplit(":", 1)[-1]
    return speaker if tail not in ("", "unknown", "none") else ""


def _augmented(row: dict) -> bool:
    source = str(row.get("source") or "")
    return "aug" in source or "augmented" in str(row.get("phase3_role") or "")


def prepare_pilot_data(
    dataset_root: Path,
    output_dir: Path,
    *,
    max_augmented_per_parent: int = 1,
    max_per_text: int = 64,
    min_eval_speakers: int = 1,
    seed: int = 314159,
) -> dict:
    """Keep actual labels, cap augmentation, and reject train/eval leakage."""
    root = Path(dataset_root).resolve()
    output = Path(output_dir)
    original_train = _metadata_rows(root, "train_manifest.jsonl")
    original_eval = _metadata_rows(root, "eval_manifest.jsonl")
    _, unsafe_eval = _partition_labels(root, original_eval, related=original_train)
    if unsafe_eval:
        raise ValueError("Evaluation contains an unvalidated filename-label lineage")
    approved, quarantined = _partition_labels(root, original_train, related=original_eval)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "quarantined_train_manifest.jsonl").open("w", encoding="utf-8") as handle:
        for row in quarantined:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    if not approved:
        raise ValueError("No speech-validated training rows after label-source quarantine")
    train = _read_rows(root, "train_manifest.jsonl", approved)
    evaluation = _read_rows(root, "eval_manifest.jsonl", original_eval)
    train_speakers = {_speaker(r) for r in train} - {""}
    eval_speakers = {_speaker(r) for r in evaluation} - {""}
    if any(not _speaker(r) for r in evaluation) or len(eval_speakers) < min_eval_speakers:
        raise ValueError("Evaluation needs enough known speaker IDs")
    if train_speakers & eval_speakers:
        raise ValueError("Train/eval speaker leakage")
    if {r["_audio_sha256"] for r in train} & {r["_audio_sha256"] for r in evaluation}:
        raise ValueError("Train/eval duplicate audio leakage")
    if max_augmented_per_parent < 0 or max_per_text < 1:
        raise ValueError("Invalid balancing limits")

    lineages = defaultdict(list)
    for row in train:
        lineage = str(row.get("parent_audio_path") or row["audio_path"])
        lineages[lineage].append(row)
    rng = random.Random(seed)
    selected = []
    excluded_augmentations = 0
    for lineage in sorted(lineages):
        group = lineages[lineage]
        if len({normalize_arabic(r["text"]) for r in group}) != 1:
            raise ValueError("Different transcripts within one clean audio lineage")
        clean = [r for r in group if not _augmented(r)]
        augmented = [r for r in group if _augmented(r)]
        rng.shuffle(augmented)
        selected.extend(clean)
        selected.extend(augmented[:max_augmented_per_parent])
        excluded_augmentations += max(0, len(augmented) - max_augmented_per_parent)

    rng.shuffle(selected)
    counts = Counter()
    balanced = []
    for row in selected:
        key = normalize_arabic(row["text"])
        if counts[key] >= max_per_text:
            continue
        counts[key] += 1
        balanced.append(row)
    if not balanced:
        raise ValueError("No training rows survived balancing")

    output.mkdir(parents=True, exist_ok=True)
    for name, rows in [("train_manifest.jsonl", balanced), ("eval_manifest.jsonl", evaluation)]:
        with (output / name).open("w", encoding="utf-8") as handle:
            for row in rows:
                public = {k: v for k, v in row.items() if not k.startswith("_")}
                handle.write(json.dumps(public, ensure_ascii=False) + "\n")
    report = {
        "input_train_rows": len(original_train),
        "quarantined_training_rows": len(quarantined),
        "quarantined_sources": dict(Counter(r.get("source", "unknown") for r in quarantined)),
        "train_rows": len(balanced), "eval_rows": len(evaluation),
        "excluded_augmentations": excluded_augmentations,
        "excluded_transcript_cap": len(selected) - len(balanced),
        "max_augmented_per_parent": max_augmented_per_parent,
        "max_per_text": max_per_text, "eval_speakers": len(eval_speakers),
        "train_sources": dict(Counter(r.get("source", "unknown") for r in balanced)),
        "known_train_eval_speaker_overlap": 0, "train_eval_audio_overlap": 0,
        "unknown_train_speaker_rows": sum(not _speaker(r) for r in balanced),
        "full_speaker_disjoint_verified": all(_speaker(r) for r in balanced),
        "expected_text_prompt": False, "seed": seed,
    }
    (output / "dataset_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
