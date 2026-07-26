#!/usr/bin/env python3
"""Generate the bundled vocabulary curriculum asset from the local corpus.

Groups the corpus' 83k word tokens by their diacritic-stripped form, ranks by
frequency, and emits levels of 10 words each — "learn the most common Quran
words first". Each level records its CUMULATIVE coverage of the whole Quran's
words, so the app can honestly show "after this level you recognise X% of the
Quran" all the way down the path.

Output: mobile/assets/vocab_curriculum.json (registered in pubspec.yaml and
consumed by mobile/lib/data/services/curriculum_service.dart).

Usage:
    python scripts/build_vocab_curriculum.py            # top 600 words, 60 levels
    python scripts/build_vocab_curriculum.py --top 1000
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "mobile" / "assets" / "quran_corpus.json.gz"
OUT = REPO / "mobile" / "assets" / "vocab_curriculum.json"

TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۨ-ۭـ]")
ARABIC_LETTER = re.compile(r"[ء-ي]")


def strip_tashkeel(s: str) -> str:
    return TASHKEEL.sub("", s)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=600, help="How many words to include")
    ap.add_argument("--per_level", type=int, default=10)
    args = ap.parse_args()

    data = json.loads(gzip.open(CORPUS, "rt", encoding="utf-8").read())

    counts: Counter[str] = Counter()
    # bare form -> Counter of (display, translit, meaning) variants
    variants: dict[str, Counter] = defaultdict(Counter)
    first_ref: dict[str, tuple[int, int]] = {}
    total_tokens = 0

    for surah in data["surahs"]:
        for ayah in surah["ayahs"]:
            for w in ayah["words"]:
                text = (w.get("text") or "").strip()
                bare = strip_tashkeel(text)
                if not ARABIC_LETTER.search(bare):
                    continue  # numerals / markers
                total_tokens += 1
                counts[bare] += 1
                meaning = (w.get("translation_en") or "").strip()
                translit = (w.get("transliteration") or "").strip()
                if meaning:
                    variants[bare][(text, translit, meaning)] += 1
                first_ref.setdefault(bare, (w["surah_number"], w["ayah_number"]))

    ranked = [w for w, _ in counts.most_common() if variants[w]][: args.top]

    levels = []
    cumulative = 0
    for i in range(0, len(ranked), args.per_level):
        chunk = ranked[i : i + args.per_level]
        words = []
        for bare in chunk:
            (display, translit, meaning), _n = variants[bare].most_common(1)[0]
            s, a = first_ref[bare]
            cumulative += counts[bare]
            words.append({
                "arabic": display,
                "bare": bare,
                "translit": translit,
                "meaning": meaning,
                "count": counts[bare],
                "surah": s,
                "ayah": a,
            })
        levels.append({
            "level": len(levels) + 1,
            "coverage_pct": round(cumulative / total_tokens * 100, 1),
            "words": words,
        })

    out = {
        "source": "quran_corpus.json.gz (Quran.com v4 word-by-word)",
        "total_tokens": total_tokens,
        "distinct_words": len(counts),
        "per_level": args.per_level,
        "levels": levels,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(f"{len(levels)} levels ({len(ranked)} words) -> {OUT} "
          f"({OUT.stat().st_size // 1024} KB); "
          f"final coverage {levels[-1]['coverage_pct']}% of all Quran words")


if __name__ == "__main__":
    main()
