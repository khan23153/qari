#!/usr/bin/env python3
"""Build website/public/data/pages.json from the app's own Quran assets.

Uses the same files the Flutter app ships (mobile/assets/quran_corpus.json.gz
for the Uthmani text and tajweed spans, mobile/assets/mushaf_layout.json.gz
for the printed line of every word), so the site shows Madinah Mushaf pages
exactly as the app lays them out.

    python website/tools/build_site_data.py
"""

import collections
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "mobile" / "assets"
OUT = ROOT / "website" / "public" / "data" / "pages.json"

PAGES = (1, 2, 293, 604)
DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
SURAH_AR = {1: "الفاتحة", 2: "البقرة", 17: "الإسراء", 18: "الكهف", 112: "الإخلاص", 113: "الفلق", 114: "الناس"}
SURAH_EN = {1: "Al-Fatihah", 2: "Al-Baqarah", 17: "Al-Isra", 18: "Al-Kahf", 112: "Al-Ikhlas", 113: "Al-Falaq", 114: "An-Nas"}
BASMALA = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"


def ref_key(ref: str) -> tuple[int, int]:
    s, a = ref.split(":")
    return int(s), int(a)


def main() -> None:
    corpus = json.loads(gzip.open(ASSETS / "quran_corpus.json.gz").read())
    layout = json.loads(gzip.open(ASSETS / "mushaf_layout.json.gz").read())["verses"]
    ayahs = {f"{a['surah_number']}:{a['ayah_number']}": a for s in corpus["surahs"] for a in s["ayahs"]}

    pages = {}
    for page in PAGES:
        refs = sorted((r for r, locs in layout.items() if any(p == page for p, _ in locs)), key=ref_key)
        lines: dict[int, list] = collections.defaultdict(list)
        for ref in refs:
            locs = layout[ref]
            words = ayahs[ref]["words"][: len(locs) - 1]
            for word, (p, line) in zip(words, locs[:-1]):
                if p != page:
                    continue
                spans = [[sp["start"], sp["end"], sp["rule"]] for sp in (word.get("tajweed_spans") or [])]
                lines[line].append({"w": word["text"], "s": spans})
            p, line = locs[-1]
            if p == page:
                lines[line].append({"m": ref.split(":")[1].translate(DIGITS), "ref": ref})

        opening = page <= 2
        line_count = 8 if opening else 15
        first_line = 1
        out_lines = []
        # Empty printed lines hold the surah banner and, after it, the basmala
        # (al-Fatihah's basmala is its first ayah; at-Tawbah has none).
        for n in range(first_line, line_count + 1):
            if n in lines:
                out_lines.append({"n": n, "type": "text", "items": lines[n]})
                continue
            nxt = next((m for m in range(n + 1, line_count + 1) if m in lines), None)
            if nxt is None:
                continue  # blank tail of an opening page
            ref = next(r for r in refs if any(x[0] == page and x[1] == nxt for x in layout[r]))
            surah, ayah = ref_key(ref)
            if ayah != 1:
                continue
            block_start = n
            while block_start - 1 >= first_line and block_start - 1 not in lines:
                block_start -= 1
            has_basmala = surah not in (1, 9) and nxt - block_start >= 2
            if has_basmala and n == nxt - 1:
                out_lines.append({"n": n, "type": "basmala", "text": BASMALA})
            else:
                out_lines.append({"n": n, "type": "header", "surah": surah, "name": SURAH_AR[surah]})
        first_ref = ref_key(refs[0])
        pages[str(page)] = {
            "page": page,
            "lineCount": line_count,
            "opening": opening,
            "surah": SURAH_EN[first_ref[0]],
            "juz": ayahs[refs[0]]["juz_number"],
            "lines": out_lines,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"pages": pages}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for p in PAGES:
        kinds = [(l["n"], l["type"]) for l in pages[str(p)]["lines"] if l["type"] != "text"]
        print(p, pages[str(p)]["surah"], "lines", len(pages[str(p)]["lines"]), "banners", kinds)


if __name__ == "__main__":
    main()
