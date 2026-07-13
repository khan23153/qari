#!/usr/bin/env python3
"""Build recitation reference bundles from the bundled mobile Quran corpus.

The recitation ML engine needs an expected word sequence per ayah. The backend
corpus DB is frequently empty, so instead of fetching from core_api we build
the reference files directly from ``assets/quran_corpus.json.gz`` (which ships
with the mobile app and contains full word-level Arabic).

Writes one JSON per ayah: ``{out}/{surah}_{ayah}.json`` in the shape consumed
by ``ml.tajweed.reference_store.ReferenceStore``.

Arabic is normalized (harakat stripped, alef/ya/hamza/ta-marbuta folded) so it
matches the normalization applied to ASR hypotheses during alignment.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re

HARAKAT = re.compile(
    "[\u0618-\u061A\u064B-\u065F\u0670"
    "\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]"
)
TATWEEL = "\u0640"
ALEF = {"\u0622": "ا", "\u0623": "ا", "\u0625": "ا", "\u0671": "ا"}
YA = {"\u0649": "ي", "\u06CC": "ي"}
NON_ARABIC = re.compile("[^\u0621-\u064A\u0660-\u0669 ]")


def normalize(text: str) -> str:
    if not text:
        return ""
    text = HARAKAT.sub("", text)
    text = text.replace(TATWEEL, "")
    for k, v in ALEF.items():
        text = text.replace(k, v)
    for k, v in YA.items():
        text = text.replace(k, v)
    text = text.replace("\u0629", "ه")  # ta marbuta -> ha
    text = text.replace("\u0624", "و")  # waw hamza
    text = text.replace("\u0626", "ي")  # ya hamza
    text = text.replace("\u0621", "")  # standalone hamza
    text = NON_ARABIC.sub(" ", text)
    return " ".join(text.split())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="mobile/assets/quran_corpus.json.gz")
    ap.add_argument("--out", default="backend/recitation_api/reference_data")
    args = ap.parse_args()

    raw = gzip.decompress(open(args.corpus, "rb").read())
    root = json.loads(raw)
    out = args.out
    import os
    os.makedirs(out, exist_ok=True)

    count = 0
    for surah in root["surahs"]:
        snum = surah["surah_number"]
        for ayah in surah["ayahs"]:
            anum = ayah["ayah_number"]
            text = ayah.get("ayah_text") or ""
            norm_text = normalize(text)
            words = []
            for w in ayah.get("words", []):
                wt = w.get("text") or ""
                if not wt:
                    continue
                words.append({
                    "word": normalize(wt),
                    "phonemes": [],
                    "tajweed_checks": [],
                    "ref_start_ms": 0,
                    "ref_end_ms": 0,
                })
            if not words:
                continue
            ref = {
                "text": text,
                "normalized_text": norm_text,
                "words": words,
                "reference_audio_url": ayah.get("audio_url") or "",
                "reference_qari": "",
            }
            with open(f"{out}/{snum}_{anum}.json", "w", encoding="utf-8") as f:
                json.dump(ref, f, ensure_ascii=False)
            count += 1
    print(f"Wrote {count} reference files to {out}")


if __name__ == "__main__":
    main()
