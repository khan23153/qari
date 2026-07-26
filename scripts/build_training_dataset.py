#!/usr/bin/env python3
"""Build a Whisper fine-tuning dataset for Quran recitation from everyayah.com.

Pairs professional per-ayah recitations (everyayah.com CDN — the same source
the app streams playback audio from) with the bundled corpus text
(mobile/assets/quran_corpus.json.gz, Uthmani script), producing exactly the
manifest format ml/training/finetune_whisper.py consumes:

    <out>/audio/<reciter>/<surah:03d><ayah:03d>.wav   (16 kHz mono PCM16)
    <out>/manifest.jsonl   {"audio_path", "text", "surah", "ayah", "reciter"}

Multiple reciters give the model voice diversity — the main gap between a
generic Whisper-Quran checkpoint and Tarteel-level live tracking robustness.

Requirements: ffmpeg on PATH (mp3 -> 16k wav).

Usage:
    # everything (all 114 surahs x 5 reciters, ~31k clips — takes a while):
    python scripts/build_training_dataset.py --out /data/quran_train

    # a quick subset to smoke-test the training loop:
    python scripts/build_training_dataset.py --out /data/quran_train \
        --surahs 1-2 --reciters Alafasy_64kbps

Then fine-tune (see ml/training/README.md):
    python -m ml.training.finetune_whisper \
        --model_id tarteel-ai/whisper-tiny-ar-quran \
        --data_dir /data/quran_train --output_dir /models/qari-whisper-tiny
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_GZ = REPO_ROOT / "mobile" / "assets" / "quran_corpus.json.gz"
CDN_BASE = "https://everyayah.com/data"

# Known-good everyayah folders (same reciters offered in the app's Voice picker).
DEFAULT_RECITERS = [
    "Abdul_Basit_Murattal_64kbps",
    "Abdurrahmaan_As-Sudais_64kbps",
    "Minshawy_Murattal_128kbps",
    "Husary_64kbps",
    "Alafasy_64kbps",
]


def parse_surah_range(spec: str) -> list[int]:
    """'1-114' / '1,2,36' / '1-2,112-114' -> sorted list of surah numbers."""
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return sorted(n for n in out if 1 <= n <= 114)


def load_corpus_texts() -> dict[tuple[int, int], str]:
    """(surah, ayah) -> Uthmani ayah text from the bundled corpus."""
    with gzip.open(CORPUS_GZ, "rt", encoding="utf-8") as f:
        data = json.load(f)
    texts: dict[tuple[int, int], str] = {}
    for surah in data["surahs"]:
        for ayah in surah["ayahs"]:
            texts[(ayah["surah_number"], ayah["ayah_number"])] = ayah["ayah_text"]
    return texts


def fetch_and_convert(
    reciter: str, surah: int, ayah: int, out_dir: Path
) -> Path | None:
    """Download one ayah mp3 and convert to 16k mono WAV. Returns the wav path,
    or None on failure (missing file / network error) — the caller just skips it.
    Already-converted files are reused, so re-runs resume where they stopped."""
    stem = f"{surah:03d}{ayah:03d}"
    wav_path = out_dir / f"{stem}.wav"
    if wav_path.exists() and wav_path.stat().st_size > 44:
        return wav_path
    url = f"{CDN_BASE}/{reciter}/{stem}.mp3"
    mp3_path = out_dir / f"{stem}.mp3"
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            mp3_path.write_bytes(resp.read())
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3_path),
             "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", str(wav_path)],
            check=True,
        )
        return wav_path
    except Exception as e:  # noqa: BLE001 — skip-and-continue is the contract
        print(f"  ! skip {reciter}/{stem}: {e}", file=sys.stderr)
        wav_path.unlink(missing_ok=True)
        return None
    finally:
        mp3_path.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="Dataset output directory")
    ap.add_argument("--surahs", default="1-114", help="Surah range, e.g. 1-2,36")
    ap.add_argument(
        "--reciters", nargs="*", default=DEFAULT_RECITERS,
        help="everyayah.com folder names (default: the app's 5 reciters)",
    )
    ap.add_argument("--workers", type=int, default=8, help="Parallel downloads")
    args = ap.parse_args()

    surahs = parse_surah_range(args.surahs)
    out_root = Path(args.out)
    texts = load_corpus_texts()
    targets = [(s, a) for (s, a) in sorted(texts) if s in surahs]
    print(f"Corpus loaded: {len(targets)} ayahs across {len(surahs)} surahs, "
          f"{len(args.reciters)} reciters -> up to {len(targets) * len(args.reciters)} clips")

    entries: list[dict] = []
    for reciter in args.reciters:
        audio_dir = out_root / "audio" / reciter
        audio_dir.mkdir(parents=True, exist_ok=True)
        print(f"== {reciter}")
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(fetch_and_convert, reciter, s, a, audio_dir): (s, a)
                for (s, a) in targets
            }
            done = 0
            for fut in as_completed(futures):
                s, a = futures[fut]
                wav = fut.result()
                done += 1
                if done % 500 == 0:
                    print(f"  {done}/{len(targets)}")
                if wav is None:
                    continue
                entries.append({
                    "audio_path": str(wav.relative_to(out_root)),
                    "text": texts[(s, a)],
                    "surah": s,
                    "ayah": a,
                    "reciter": reciter,
                })

    entries.sort(key=lambda e: (e["reciter"], e["surah"], e["ayah"]))
    manifest = out_root / "manifest.jsonl"
    with open(manifest, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"Wrote {len(entries)} entries -> {manifest}")


if __name__ == "__main__":
    main()
