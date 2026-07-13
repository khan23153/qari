"""Generate a self-contained local Quran corpus asset for the mobile app.

The backend corpus DB is frequently empty/unreliable, which left the reader
showing a blank screen. This script pulls the full Quran (Uthmani text,
simple text, English + Urdu verse translations, and word-by-word
transliteration + English word translation) from the Quran.com API v4 and
writes it as a single JSON file shaped to match the mobile app's
``AyahModel`` / ``WordModel`` ``fromJson`` keys, so the Flutter code can load
it directly with no mapping layer.

Output: mobile/assets/quran_corpus.json
Run:    python3 scripts/build_local_corpus.py
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import httpx

BASE = "https://api.quran.com/api/v4"
OUT = Path(__file__).resolve().parent.parent / "mobile" / "assets" / "quran_corpus.json"

# Verified Quran.com translation resource IDs.
EN_RES = 84   # English (Saheeh International-style)
UR_RES = 97   # Urdu
PER_PAGE = 300
RATE_DELAY = 0.25


async def fetch_surah(client: httpx.AsyncClient, surah: int) -> dict:
    params = {
        "fields": "text_uthmani,text_imlaei",
        "translations": f"{EN_RES},{UR_RES}",
        "words": "true",
        "word_fields": "text_uthmani,transliteration,text_imlaei",
        "word_translation_language": "en",
        "per_page": PER_PAGE,
        "page": 1,
    }
    r = await client.get(f"/verses/by_chapter/{surah}", params=params)
    r.raise_for_status()
    payload = r.json()
    verses = payload.get("verses", [])
    paging = payload.get("pagination", {})
    total_pages = paging.get("total_pages", 1)
    page = 1
    while page < total_pages:
        page += 1
        params["page"] = page
        r2 = await client.get(f"/verses/by_chapter/{surah}", params=params)
        r2.raise_for_status()
        verses.extend(r2.json().get("verses", []))
    return build_surah(surah, verses)


def _pick_translation(translations: list[dict], resource_id: int) -> str | None:
    for t in translations:
        if t.get("resource_id") == resource_id:
            text = t.get("text")
            if text:
                # Strip inline foot-note markup like <sup foot_note="...">n</sup>
                import re
                text = re.sub(r"<[^>]+>", "", text)
                return text.strip()
    return None


def build_surah(surah: int, verses: list[dict]) -> dict:
    ayahs = []
    for v in verses:
        ayah_number = v.get("verse_number")
        ayah_text = (v.get("text_uthmani") or "").strip()
        ayah_text_simple = (v.get("text_imlaei") or "").strip()
        translations = v.get("translations", []) or []
        translation_en = _pick_translation(translations, EN_RES)
        translation_ur = _pick_translation(translations, UR_RES)
        sajda = v.get("sajdah_number") is not None
        page_number = v.get("page_number")
        juz_number = v.get("juz_number")

        words = []
        word_translit_parts = []
        for w in v.get("words", []):
            word_number = w.get("position")
            text = (w.get("text_uthmani") or "").strip()
            if not text:
                continue
            translit = None
            tr = w.get("transliteration")
            if isinstance(tr, dict):
                translit = (tr.get("text") or "").strip() or None
            word_translit_parts.append(translit or "")
            wt = w.get("translation")
            word_translation_en = None
            if isinstance(wt, dict):
                word_translation_en = (wt.get("text") or "").strip() or None
            words.append({
                "word_id": surah * 1_000_000 + ayah_number * 1000 + (word_number or 0),
                "surah_number": surah,
                "ayah_number": ayah_number,
                "word_number": word_number,
                "text": text,
                "text_clean": (w.get("text_imlaei") or "").strip() or None,
                "transliteration": translit,
                "translation_en": word_translation_en,
                "translation_ur": None,
                "translation_hi": None,
                "pos_group": None,
                "pos_arabic": None,
                "root_arabic": None,
                "root_id": None,
                "morphology": None,
                "lemma": None,
                "audio_url": None,
                "tajweed_spans": None,
            })

        transliteration = " ".join(p for p in word_translit_parts if p) or None

        ayahs.append({
            "ayah_id": surah * 1000 + ayah_number,
            "surah_number": surah,
            "ayah_number": ayah_number,
            "ayah_text": ayah_text,
            "ayah_text_simple": ayah_text_simple or None,
            "translation_en": translation_en,
            "translation_ur": translation_ur,
            "translation_hi": None,
            "transliteration": transliteration,
            "audio_url": None,
            "page_number": page_number,
            "juz_number": juz_number,
            "is_bismillah": surah == 1 and ayah_number == 1,
            "words": words,
            "sajda": sajda,
            "context_story": None,
        })
    return {"surah_number": surah, "ayahs": ayahs}


async def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    headers = {"Accept": "application/json", "User-Agent": "QariCorpusBuilder/1.0"}
    async with httpx.AsyncClient(base_url=BASE, headers=headers, timeout=30.0,
                                 follow_redirects=True) as client:
        surahs = []
        for s in range(1, 115):
            for attempt in range(4):
                try:
                    data = await fetch_surah(client, s)
                    surahs.append(data)
                    print(f"  surah {s}: {len(data['ayahs'])} ayahs", flush=True)
                    break
                except Exception as e:  # noqa: BLE001
                    print(f"  surah {s} attempt {attempt+1} failed: {e}", flush=True)
                    await asyncio.sleep(1.5 * (attempt + 1))
            await asyncio.sleep(RATE_DELAY)

    total_ayahs = sum(len(s["ayahs"]) for s in surahs)
    total_words = sum(len(a["words"]) for s in surahs for a in s["ayahs"])
    out = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "https://api.quran.com/api/v4",
        "surah_count": len(surahs),
        "ayah_count": total_ayahs,
        "word_count": total_words,
        "surahs": surahs,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    size_mb = OUT.stat().st_size / 1_000_000
    print(f"\nWrote {OUT} ({size_mb:.1f} MB): {len(surahs)} surahs, "
          f"{total_ayahs} ayahs, {total_words} words")


if __name__ == "__main__":
    asyncio.run(main())
