#!/usr/bin/env python3
"""Build recitation reference bundles for the ML pipeline.

The recitation engine needs an expected word sequence + tajweed positions per
ayah (see ``ml.tajweed.reference_store``). This script fetches ayah word data
from core_api (GET /v1/surahs/{n}/ayahs) and writes one JSON file per ayah in
the format ``ReferenceStore`` consumes: ``{data_dir}/{surah}_{ayah}.json``.

MVP scope (per the master spec): Al-Fatihah (1:1-7) + Juz 30 (surahs 78-114).

Usage:
    python scripts/build_reference_bundle.py \
        --core-api http://localhost:8000 \
        --out /tmp/qari_reference \
        --scope juz30
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import httpx
except ImportError:  # pragma: no cover
    sys.exit("httpx is required: pip install httpx")


HARAKAT = re.compile(r"[\u064B-\u065F\u0670]")


def normalize(text: str) -> str:
    return HARAKAT.sub("", text or "")


# (surah, ayah_start, ayah_end) ranges for the MVP scope.
SCOPES = {
    "fatihah": [(1, 1, 7)],
    "juz30": [(s, 1, 9999) for s in range(78, 115)],
    "mvp": [(1, 1, 7)] + [(s, 1, 9999) for s in range(78, 115)],
}


def fetch_ayah(client: httpx.Client, base: str, surah: int, ayah: int) -> dict | None:
    url = f"{base}/v1/surahs/{surah}/ayahs"
    resp = client.get(url, params={"from": ayah, "to": ayah}, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    ayahs = payload.get("ayahs") or payload.get("data") or []
    return ayahs[0] if ayahs else None


def build_reference(ayah_obj: dict) -> dict:
    words = []
    for w in ayah_obj.get("words", []):
        spans = w.get("tajweed_spans") or []
        tajweed_checks = [
            {
                "rule": s.get("rule", ""),
                "letter": s.get("letter", ""),
                "position": int(s.get("char_start", 0)),
                "expected_duration_ms": 0,
            }
            for s in spans
        ]
        words.append(
            {
                "word": normalize(w.get("text_arabic", "")),
                "phonemes": [],
                "tajweed_checks": tajweed_checks,
                "ref_start_ms": 0,
                "ref_end_ms": 0,
            }
        )
    return {
        "surah": ayah_obj.get("surah_number"),
        "ayah": ayah_obj.get("ayah_number"),
        "text": ayah_obj.get("text_arabic", ""),
        "normalized_text": normalize(ayah_obj.get("text_arabic", "")),
        "reference_audio_url": ayah_obj.get("audio_url", ""),
        "reference_qari": "",
        "words": words,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-api", default="http://localhost:8000")
    parser.add_argument("--out", required=True)
    parser.add_argument("--scope", choices=list(SCOPES), default="mvp")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    ranges = SCOPES[args.scope]
    written = 0
    with httpx.Client() as client:
        for surah, start, end in ranges:
            # Discover ayah count via the surah meta.
            meta = client.get(f"{args.core_api}/v1/surahs/{surah}", timeout=30).json()
            ayah_count = int(meta.get("ayah_count") or end)
            ayah_count = min(ayah_count, end)
            for ayah in range(start, ayah_count + 1):
                try:
                    ayah_obj = fetch_ayah(client, args.core_api, surah, ayah)
                except Exception as exc:
                    print(f"skip {surah}:{ayah} ({exc})", file=sys.stderr)
                    continue
                if not ayah_obj:
                    continue
                ref = build_reference(ayah_obj)
                path = out_dir / f"{surah}_{ayah}.json"
                path.write_text(json.dumps(ref, ensure_ascii=False), encoding="utf-8")
                written += 1
    print(f"Wrote {written} reference files to {out_dir}")


if __name__ == "__main__":
    main()
