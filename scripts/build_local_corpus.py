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
import re
import time
from pathlib import Path

import httpx

BASE = "https://api.quran.com/api/v4"
OUT = Path(__file__).resolve().parent.parent / "mobile" / "assets" / "quran_corpus.json"

# ─── Tajweed ────────────────────────────────────────────────────────────────
# Quran.com v4 exposes `text_uthmani_tajweed`, which embeds <tajweed class=X>
# tags around the letters each rule applies to. We strip the markup, compute
# each rule's character range in the plain ayah text, then map those ranges to
# word-relative offsets so the mobile reader can colour the precise letters.
_TAJWEED_TAG_RE = re.compile(r"<tajweed class=([^>\s]+)>(.*?)</tajweed>", re.DOTALL)
_SPAN_END_RE = re.compile(r"<span[^>]*>.*?</span>", re.DOTALL)
_TAJWEED_MARKUP_RE = re.compile(r"</?tajweed[^>]*>")

# Friendly English names for the markup classes (used for the reader legend
# and the word detail sheet). Keys are the raw Quran.com class names.
TAJWEED_RULE_NAMES: dict[str, str] = {
    "ham_wasl": "Hamzat al-Wasl",
    "laam_shamsiyah": "Lam Shamsiyyah",
    "madda_normal": "Madd Tabii (Natural)",
    "madda_permissible": "Madd Ja'iz (Permissible)",
    "madda_obligatory": "Madd Wajib (Obligatory)",
    "madda_necessary": "Madd Lazim (Necessary)",
    "slnt": "Madd 'Arid (Silent)",
    "ghunnah": "Ghunnah (Nasalisation)",
    "ikhafa": "Ikhfa (Concealment)",
    "ikhafa_shafawi": "Ikhfa Shafawi",
    "qalaqah": "Qalqalah (Echoing)",
    "idgham_ghunnah": "Idgham bi Ghunnah",
    "idgham_wo_ghunnah": "Idgham bila Ghunnah",
    "idgham_shafawi": "Idgham Shafawi",
    "idgham_mutajanisayn": "Idgham Mutajanisayn",
    "iqlab": "Iqlab (Conversion)",
}


def _strip_tajweed_markup(text: str) -> str:
    """Remove tajweed markup + verse-end markers, leaving plain Uthmani text."""
    text = _SPAN_END_RE.sub("", text)
    text = _TAJWEED_MARKUP_RE.sub("", text)
    return text


def build_tajweed_spans(tajweed_text: str, words: list[dict]) -> list[list[dict] | None]:
    """Return a list parallel to `words`; each item is a list of tajweed span
    dicts (with offsets relative to that word's own `text`) or None.

    Each span dict: {start, end, rule, rule_name, rule_description}.
    """
    if not tajweed_text:
        return [None for _ in words]

    # Word boundaries in the plain (markup-stripped) ayah text. Words are joined
    # by single spaces, matching how Quran.com renders the ayah.
    boundaries: list[tuple[int, int]] = []
    pos = 0
    for w in words:
        form = w.get("text") or ""
        start = pos
        end = pos + len(form)
        boundaries.append((start, end))
        pos = end + 1  # +1 for the space separator

    spans_per_word: list[list[dict]] = [[] for _ in words]

    for match in _TAJWEED_TAG_RE.finditer(tajweed_text):
        rule = match.group(1)
        fragment = match.group(2)

        # Character offset of this fragment in the plain ayah text.
        tagged_before = tajweed_text[: match.start()]
        plain_before = _strip_tajweed_markup(tagged_before)
        a_start = len(plain_before)
        a_end = a_start + len(fragment)

        for idx, (w_start, w_end) in enumerate(boundaries):
            ov_start = max(a_start, w_start)
            ov_end = min(a_end, w_end)
            if ov_start < ov_end:
                spans_per_word[idx].append({
                    "start": ov_start - w_start,
                    "end": ov_end - w_start,
                    "rule": rule,
                    "rule_name": TAJWEED_RULE_NAMES.get(rule, rule),
                    "rule_description": "",
                })

    return [spans or None for spans in spans_per_word]

# Verified Quran.com translation resource IDs.
EN_RES = 84   # English (Saheeh International-style)
# Urdu: Fateh Muhammad Jalandhari (resource 234 / slug ur-fatah-muhammad-jalandhari).
# This MUST match the Urdu tarjuma AUDIO the app plays (everyayah.com
# urdu_shamshad_ali_khan_46kbps), which is a recitation of Jalandhari's
# translation — alquran.cloud edition "ur.jalandhry.text". Using any other
# Urdu translator (e.g. Maududi, resource 97) makes the read text disagree
# with the heard audio. Do not change without re-checking the audio source.
UR_RES = 234  # Urdu — Fateh Muhammad Jalandhari
PER_PAGE = 300
RATE_DELAY = 0.25

# Optional base URL for per-ayah Urdu translation audio. When set, everyayah-
# style "{base}/{surah:03d}{ayah:03d}.mp3" URLs are written into the offline
# corpus so the reader can queue Urdu tarjuma audio without a network call.
# Leave unset (empty) to omit Urdu audio URLs from the bundle (the app also
# constructs them from AppConstants.urduTranslationCdnUrl at runtime).
import os
URDU_AUDIO_BASE_URL = os.environ.get("URDU_AUDIO_BASE_URL", "").rstrip("/")


async def fetch_surah(client: httpx.AsyncClient, surah: int) -> dict:
    params = {
        "fields": "text_uthmani,text_imlaei,text_uthmani_tajweed",
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

        # Tajweed markup for this ayah (may be absent if the API omits it).
        tajweed_text = (v.get("text_uthmani_tajweed") or "").strip()

        # First pass: collect raw word dicts so we can compute tajweed spans
        # (which need word boundaries across the whole ayah).
        raw_words = []
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
            raw_words.append({
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

        # Second pass: attach per-word tajweed spans (word-relative offsets).
        tajweed_spans = build_tajweed_spans(tajweed_text, raw_words)
        words = []
        for raw, spans in zip(raw_words, tajweed_spans):
            raw["tajweed_spans"] = spans
            words.append(raw)

        transliteration = " ".join(p for p in word_translit_parts if p) or None

        audio_url_ur = None
        if URDU_AUDIO_BASE_URL:
            audio_url_ur = (
                f"{URDU_AUDIO_BASE_URL}/{surah:03d}{ayah_number:03d}.mp3"
            )

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
            "audio_url_ur": audio_url_ur,
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
