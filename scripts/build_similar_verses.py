#!/usr/bin/env python3
"""Build mobile/assets/similar_verses.json: the mutashabihat index.

Two ayahs are "similar" when, compared word by word by letter skeleton,
at least MIN_SHARED words appear in both in the same order and they make up
at least MIN_RATIO of the shorter ayah, yet the texts are not identical, so
a reciter can start one and slide into the other (2:58 and 7:161, 2:35 and
7:19, ...). Only the ayahs that have a similar
partner are written, with their skeleton words, so the app can check what
it hears against both verses without loading the whole corpus.

    python scripts/build_similar_verses.py
"""

import collections
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "mobile" / "assets" / "quran_corpus.json.gz"
OUT = ROOT / "mobile" / "assets" / "similar_verses.json"

GRAM = 3
MIN_SHARED = 4
MIN_RATIO = 0.5

_MARKS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_LETTER = re.compile("[ء-يٱ]")


def skeleton(word: str) -> str:
    """Letters only, with the spelling differences between the Uthmani text,
    the simple text and speech recognisers removed. Must match
    `SimilarVerseIndex.skeleton` in the app."""
    w = _MARKS.sub("", word)
    for a in "آأإٱ":
        w = w.replace(a, "ا")
    w = w.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")
    w = w.replace("ا", "")  # alif is spelled differently in each script
    return "".join(ch for ch in w if _LETTER.match(ch))


def words(text: str) -> list[str]:
    out = []
    for token in text.split():
        if not _LETTER.search(token):
            continue  # waqf signs and other marks
        sk = skeleton(token)
        if sk:
            out.append(sk)
    return out


def shared_in_order(a: list[str], b: list[str]) -> int:
    """Longest common subsequence of words."""
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            cur[j] = prev[j - 1] + 1 if ai == b[j - 1] else max(prev[j], cur[j - 1])
        prev = cur
    return prev[len(b)]


def main() -> None:
    corpus = json.loads(gzip.open(CORPUS).read())
    ayahs = {}
    for s in corpus["surahs"]:
        for a in s["ayahs"]:
            ayahs[f"{a['surah_number']}:{a['ayah_number']}"] = words(a["ayah_text_simple"])

    grams = collections.defaultdict(set)
    for ref, ws in ayahs.items():
        for i in range(len(ws) - GRAM + 1):
            grams[tuple(ws[i:i + GRAM])].add(ref)

    candidates = set()
    for refs in grams.values():
        if 1 < len(refs) <= 60:  # a phrase in 60+ ayahs is a formula, not a trap
            rs = sorted(refs)
            for i in range(len(rs)):
                for j in range(i + 1, len(rs)):
                    candidates.add((rs[i], rs[j]))

    similar = collections.defaultdict(set)
    for a, b in candidates:
        if ayahs[a] == ayahs[b]:
            continue  # identical text: sliding between them changes nothing heard
        wa, wb = ayahs[a], ayahs[b]
        shared = shared_in_order(wa, wb)
        if shared >= MIN_SHARED and shared >= MIN_RATIO * min(len(wa), len(wb)):
            similar[a].add(b)
            similar[b].add(a)

    def key(ref):
        s, a = ref.split(":")
        return int(s), int(a)

    out = {
        "min_shared": MIN_SHARED,
        "min_ratio": MIN_RATIO,
        "similar": {r: sorted(similar[r], key=key) for r in sorted(similar, key=key)},
        "words": {r: ayahs[r] for r in sorted(similar, key=key)},
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    pairs = sum(len(v) for v in similar.values()) // 2
    print(f"{len(similar)} ayahs, {pairs} pairs, {OUT.stat().st_size // 1024} KB")
    for probe in ("2:58", "7:161", "2:35", "7:19"):
        print(probe, "->", sorted(similar.get(probe, []), key=key)[:6])


if __name__ == "__main__":
    main()
