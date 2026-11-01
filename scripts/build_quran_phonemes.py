#!/usr/bin/env python3
"""Build ml/assets/quran_phonemes.json.gz: IqraEval-style phonemes per Quran word.

Uses the plain vowelled ayah text (``ayah_text_simple``) when its words line up
one-to-one with the Mushaf words, else the Mushaf (Uthmani) words. Each ayah is
phonemized as one connected utterance, so word-boundary effects are right.

    python scripts/build_quran_phonemes.py
"""
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.alignment.quran_g2p import phonemize_words  # noqa: E402

LETTER = re.compile("[ء-ي]")


def main() -> None:
    corpus = json.load(gzip.open(ROOT / "mobile/assets/quran_corpus.json.gz"))
    ayahs, from_simple = {}, 0
    for s in corpus["surahs"]:
        for a in s["ayahs"]:
            mushaf = [w["text"] for w in a["words"] if LETTER.search(w["text"])]
            simple = [t for t in (a.get("ayah_text_simple") or "").split() if LETTER.search(t)]
            words = simple if len(simple) == len(mushaf) else mushaf
            from_simple += words is simple
            ayahs[f'{s["surah_number"]}:{a["ayah_number"]}'] = [" ".join(p) for p in phonemize_words(words)]
    out = ROOT / "ml/assets/quran_phonemes.json.gz"
    with gzip.open(out, "wt", encoding="utf-8") as f:
        json.dump({"source": "mobile/assets/quran_corpus.json.gz via ml/alignment/quran_g2p.py (style=quran)",
                   "ayahs": ayahs}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(ayahs)} ayahs ({from_simple} from the plain text) -> {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
