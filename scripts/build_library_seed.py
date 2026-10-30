#!/usr/bin/env python3
"""Build the Islamic Library starter catalog and seed from real sources.

Sourced fields (Arabic text with tashkeel, English text, chapter names,
hadith ranges and scholar grades) are copied verbatim from the public-domain
``fawazahmed0/hadith-api`` dataset (Unlicense). Hand-curated fields (isnad
identification, narrator rulings, defect reasons, gharib entries) come from
``backend/core_api/app/library/data/curated.json`` and keep their own
``review_status``.

Usage (needs network access to raw.githubusercontent.com):

    python scripts/build_library_seed.py [--cache-dir .library-cache]

Writes ``catalog.json`` and ``seed.json`` next to ``curated.json``.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

DATASET = "fawazahmed0/hadith-api"
DATASET_BASE = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1"
DATASET_LICENSE = "Unlicense (public domain)"

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "backend" / "core_api" / "app" / "library" / "data"


def fetch_json(rel: str, cache_dir: Path) -> dict:
    target = cache_dir / rel
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"{DATASET_BASE}/{rel}", timeout=120) as resp:
            target.write_bytes(resp.read())
    return json.loads(target.read_text(encoding="utf-8"))


def books_for(info: dict) -> list[dict]:
    sections = info["metadata"]["sections"]
    ranges: dict[int, list[int]] = {}
    for h in info["hadiths"]:
        book = h["reference"]["book"]
        ranges.setdefault(book, []).append(h["hadithnumber"])
    books = []
    for key, name in sections.items():
        number = int(key)
        numbers = ranges.get(number)
        if number == 0 or not name or not numbers:
            continue
        books.append({
            "number": number,
            "name_en": name,
            "hadith_first": int(min(numbers)),
            "hadith_last": int(max(numbers)),
            "hadith_count": len(numbers),
        })
    return sorted(books, key=lambda b: b["number"])


_MARKS = {chr(c) for c in range(0x064B, 0x0660)} | {"\u0670", "\u0640", "\u200f", "\u200e"}


def find_letters(text: str, needle: str, start: int = 0) -> int:
    """Index in [text] where [needle] starts, comparing letters only.

    Tashkeel order differs between sources (shadda+fatha vs fatha+shadda), so
    both strings are compared with harakat removed and the hit is mapped back
    to the original index.
    """
    positions = [i for i, ch in enumerate(text) if ch not in _MARKS and i >= start]
    bare = "".join(text[i] for i in positions)
    hit = bare.index("".join(ch for ch in needle if ch not in _MARKS))
    return positions[hit]


def exact_quote(text: str, needle: str) -> str:
    """The verbatim substring of [text] that matches [needle] letter-for-letter.

    Raises ValueError if the source does not contain it, so a quote can never
    be marked verified unless it really is in the cited text.
    """
    positions = [i for i, ch in enumerate(text) if ch not in _MARKS]
    bare = "".join(text[i] for i in positions)
    bare_needle = "".join(ch for ch in needle if ch not in _MARKS)
    hit = bare.index(bare_needle)
    start = positions[hit]
    end = positions[hit + len(bare_needle) - 1] + 1
    while end < len(text) and text[end] in _MARKS and text[end] not in "\u200f\u200e":
        end += 1
    return text[start:end]


def verbatim(texts: list[str], quote: str) -> str:
    """Resolve each «...»-separated segment of [quote] against the sources."""
    segments = []
    for segment in quote.split(" ... "):
        for text in texts:
            try:
                segments.append(exact_quote(text, segment))
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"verified quote not found in any source text: {segment!r}")
    return " ... ".join(segments)


def split_text(text: str, first_word: str, end_marker: str | None) -> tuple[str, str, str | None]:
    """Split a sourced narration into (isnad, matn, trailing compiler note).

    The matn starts at [first_word]; the isnad ends at the opening quote just
    before it. Invisible RTL marks in the source are dropped from the matn.
    """
    word_at = find_letters(text, first_word)
    quote_at = text.rfind('"', 0, word_at)
    isnad = text[: quote_at if quote_at != -1 else word_at]
    isnad = isnad.replace("\u200f", "").replace("\u200e", "").strip().rstrip(" :،").strip()
    rest = text[word_at:]
    note = None
    if end_marker:
        end = find_letters(rest, end_marker)
        note = rest[end:].strip()
        rest = rest[:end]
    matn = rest.replace("\u200f", "").replace("\u200e", "")
    matn = matn.strip().rstrip('". ').strip()
    return isnad, matn, note


def build(cache_dir: Path) -> None:
    curated = json.loads((DATA_DIR / "curated.json").read_text(encoding="utf-8"))
    info = fetch_json("info.json", cache_dir)

    collections = []
    for c in curated["collections"]:
        entry = {k: v for k, v in c.items() if k != "dataset_key"}
        key = c.get("dataset_key")
        if key:
            entry["availability"] = "remote"
            entry["hadith_count"] = len(info[key]["hadiths"])
            entry["books"] = books_for(info[key])
            entry["remote"] = {
                "provider": DATASET,
                "base_url": DATASET_BASE,
                "license": DATASET_LICENSE,
                "arabic_edition": f"ara-{key}",
                "translation_edition": f"eng-{key}",
            }
        else:
            entry.setdefault("availability", "planned")
            entry["hadith_count"] = None
            entry["books"] = []
        collections.append(entry)

    catalog = {
        "categories": curated["categories"],
        "collections": collections,
        "source": {"dataset": DATASET, "base_url": DATASET_BASE, "license": DATASET_LICENSE},
    }

    hadiths = []
    for h in curated["hadiths"]:
        slug, number = h["id"].split(":")
        number = int(number)
        ara = fetch_json(f"editions/ara-{slug}/{number}.json", cache_dir)
        eng = fetch_json(f"editions/eng-{slug}/{number}.json", cache_dir)
        a, e = ara["hadiths"][0], eng["hadiths"][0]
        isnad, matn, note = split_text(a["text"], h["matn_marker"], h.get("matn_end_marker"))
        book = a["reference"]["book"]
        hadiths.append({
            "id": h["id"],
            "collection": slug,
            "number": number,
            "arabic_number": a.get("arabicnumber"),
            "book": {"number": book, "name_en": ara["metadata"]["section"].get(str(book))},
            "text_ar": a["text"],
            "isnad_ar": isnad,
            "matn_ar": matn,
            "compiler_note_ar": note,
            "translation": {
                "language": "en",
                "text": e["text"],
                "source": f"{DATASET} (eng-{slug})",
                "license_status": "unverified",
            },
            "dataset_grades": [
                {"scholar": g["name"], "grade": g["grade"], "source_dataset": f"{DATASET} (eng-{slug})"}
                for g in e.get("grades", [])
            ],
            "chain": h["chain"],
            "gharib_words": h.get("gharib_words", []),
            "defects": [
                {**d, "quote_ar": verbatim([a["text"]], d["quote_ar"])} if d.get("quote_verified") else d
                for d in h.get("defects", [])
            ],
            "source": {"dataset": DATASET, "editions": [f"ara-{slug}", f"eng-{slug}"], "license": DATASET_LICENSE},
            "review_status": "verified_from_source",
        })

    # Teachers/students are derived only from the seeded chains (node i heard
    # from node i+1), never typed by hand.
    sources = [h["text_ar"] for h in hadiths]
    narrators = {}
    for n in curated["narrators"]:
        rulings = [
            {**r, "ruling_ar": verbatim(sources, r["ruling_ar"])} if r["review_status"] == "verified_from_source" else r
            for r in n["rulings"]
        ]
        narrators[n["id"]] = {**n, "rulings": rulings, "teachers": [], "students": []}
    for h in hadiths:
        ids = [node.get("narrator_id") for node in h["chain"]]
        for student, teacher in zip(ids, ids[1:]):
            if student in narrators and teacher in narrators:
                if teacher not in narrators[student]["teachers"]:
                    narrators[student]["teachers"].append(teacher)
                if student not in narrators[teacher]["students"]:
                    narrators[teacher]["students"].append(student)

    gharib = []
    for g in curated["gharib"]:
        g = dict(g)
        g["forms"] = sorted(set(g["forms"]))
        gharib.append(g)

    seed = {"hadiths": hadiths, "narrators": list(narrators.values()), "gharib": gharib}
    (DATA_DIR / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (DATA_DIR / "seed.json").write_text(json.dumps(seed, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"catalog: {len(collections)} collections; seed: {len(hadiths)} hadiths, {len(narrators)} narrators, {len(gharib)} gharib")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".library-cache")
    build(parser.parse_args().cache_dir)
