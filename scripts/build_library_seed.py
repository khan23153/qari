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

Narrator rulings and defects that cite Taqrib al-Tahdhib carry a
``taqrib_no``. They are checked letter-for-letter against the verbatim
entries in ``taqrib_excerpts.json``; a match is marked
``verified_from_source`` and the full entry is attached. Refresh the
excerpts from a full Taqrib text (one JSON list of numbered entries, e.g.
parsed from the Islamic_Library_Dataset Drive export) with
``--taqrib-entries PATH``.
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


_ARABIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
TAQRIB_SOURCE = "Taqrib al-Tahdhib (Ibn Hajar, d. 852 AH), entry text from the Islamic_Library_Dataset export"


def taqrib_excerpts(curated: dict, entries_path: Path | None) -> dict[str, str]:
    """Verbatim Taqrib entries for every taqrib_no the curated data cites."""
    excerpts_file = DATA_DIR / "taqrib_excerpts.json"
    wanted = sorted({
        r["taqrib_no"] for n in curated["narrators"] for r in n["rulings"] if r.get("taqrib_no")
    } | {
        d["taqrib_no"] for h in curated["hadiths"] for d in h.get("defects", []) if d.get("taqrib_no")
    })
    if entries_path is not None:
        entries = json.loads(entries_path.read_text(encoding="utf-8"))
        by_no = {}
        for e in entries:
            head = e.split("-", 1)[0].strip()
            by_no[head] = e.strip()
        excerpts = {}
        for no in wanted:
            key = str(no).translate(_ARABIC_DIGITS)
            if key not in by_no:
                raise ValueError(f"Taqrib entry {no} not found in {entries_path}")
            excerpts[str(no)] = by_no[key]
        excerpts_file.write_text(json.dumps(excerpts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not excerpts_file.exists():
        return {}
    return json.loads(excerpts_file.read_text(encoding="utf-8"))


def verify_taqrib(record: dict, text_field: str, excerpts: dict[str, str]) -> dict:
    """Mark a Taqrib-cited record verified if its wording is in the entry."""
    no = record.get("taqrib_no")
    entry = excerpts.get(str(no)) if no else None
    if entry is None:
        return record
    quoted = verbatim([entry], record[text_field])  # raises if not present
    return {
        **record,
        text_field: quoted,
        "source_book": f"Taqrib al-Tahdhib, no. {no}",
        "source_text_ar": entry,
        "review_status": "verified_from_source",
    }


def build(cache_dir: Path, taqrib_entries: Path | None = None) -> None:
    curated = json.loads((DATA_DIR / "curated.json").read_text(encoding="utf-8"))
    excerpts = taqrib_excerpts(curated, taqrib_entries)
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
                verify_taqrib(
                    {**d, "quote_ar": verbatim([a["text"]], d["quote_ar"])} if d.get("quote_verified") else d,
                    "quote_ar",
                    excerpts,
                )
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
            verify_taqrib(r, "ruling_ar", excerpts) if r.get("taqrib_no")
            else {**r, "ruling_ar": verbatim(sources, r["ruling_ar"])} if r["review_status"] == "verified_from_source"
            else r
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
    parser.add_argument("--taqrib-entries", type=Path, default=None)
    args = parser.parse_args()
    build(args.cache_dir, args.taqrib_entries)
