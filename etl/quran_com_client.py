"""Quran.com API v4 client — surahs, ayahs, translations, audio."""
import httpx
from typing import Any
import structlog

from etl.config import settings

log = structlog.get_logger()


class QuranComClient:
    """Async client for Quran.com API v4."""

    def __init__(self):
        self.base_url = settings.QURAN_COM_API_BASE
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={"Accept": "application/json"},
        )

    async def get_surahs(self) -> list[dict]:
        """Fetch all 114 surahs with metadata."""
        resp = await self.client.get("/chapters", params={"language": "en"})
        resp.raise_for_status()
        data = resp.json()
        surahs = data.get("chapters", [])
        log.info("Fetched surahs", count=len(surahs))
        return surahs

    async def get_ayahs(
        self,
        surah_number: int,
        qari_id: int = 1,
        translations: str = "131,97,136",
    ) -> list[dict]:
        """Fetch ayahs with Uthmani text, translations, and audio segments.

        Translation IDs:
          131 = Sahih International (EN)
          97  = approved Urdu edition
          136 = Hinglish (if available)
        """
        resp = await self.client.get(
            f"/quran/verses/uthmani",
            params={"chapter_number": surah_number},
        )
        resp.raise_for_status()
        uthmani_data = resp.json().get("verses", [])

        resp2 = await self.client.get(
            f"/quran/verses/translations",
            params={
                "chapter_number": surah_number,
                "translations": translations,
            },
        )
        resp2.raise_for_status()
        trans_data = resp2.json().get("verses", [])

        # Merge uthmani text with translations
        trans_by_key = {
            (v["verse_number"], v["verse_key"]): v
            for v in trans_data
        }

        ayahs = []
        for v in uthmani_data:
            key = (v["verse_number"], v["verse_key"])
            trans = trans_by_key.get(key, {})
            ayahs.append({
                "ayah_number": v["verse_number"],
                "text_uthmani": v["text_uthmani"],
                "text_imlaei": v.get("text_imlaei", v["text_uthmani"]),
                "page_number": v.get("page_number"),
                "juz_number": v.get("juz_number"),
                "translations": trans.get("translations", []),
            })

        log.info("Fetched ayahs", surah=surah_number, count=len(ayahs))
        return ayahs

    async def get_word_translations(self, surah_number: int) -> list[dict]:
        """Fetch word-by-word translations and transliterations."""
        resp = await self.client.get(
            f"/quran/verses/word_by_word",
            params={"chapter_number": surah_number},
        )
        resp.raise_for_status()
        return resp.json().get("verses", [])

    async def get_audio_segments(self, surah_number: int, qari_id: int = 1) -> dict:
        """Fetch ayah audio URLs + segment timestamps for a qari."""
        resp = await self.client.get(
            f"/audio/reciters/{qari_id}",
            params={"chapter_number": surah_number},
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
