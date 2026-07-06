"""
Async client for the Quran.com API v4.

Documentation: https://api.quran.com/api/v4

The client wraps every endpoint the ETL pipeline needs:

* ``GET /chapters``                         – all 114 surah metadata
* ``GET /quran/verses/uthmani``             – Uthmani text
* ``GET /quran/verses/imlaei``              – Imlaei (simple) text
* ``GET /quran/verses/uthmani_tajweed``     – Uthmani + tajweed markup
* ``GET /quran/verses/translations``        – translation editions
* ``GET /verses/by_chapter/{n}``            – ayah list with word refs
* ``GET /quran/verses/{key}/by_word``       – word-by-word data
* ``GET /audio/reciters/{id}``              – reciter info
* ``GET /audio/reciters/{id}/by_chapter/{n}`` – per-surah audio files + segments

All requests are retried with exponential backoff.  Rate-limiting is
enforced via a small inter-request delay.
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any, Dict, List, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class QuranComError(Exception):
    """Base error for Quran.com API failures."""


class QuranComHTTPError(QuranComError):
    """Raised when the API returns a non-2xx status after all retries."""

    def __init__(self, status_code: int, url: str, body: str) -> None:
        super().__init__(f"HTTP {status_code} from {url}: {body[:200]}")
        self.status_code = status_code
        self.url = url
        self.body = body


class QuranComRateLimitError(QuranComError):
    """Raised when the API returns 429 Too Many Requests."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class QuranComClient:
    """Async httpx-based client for Quran.com API v4.

    Parameters
    ----------
    base_url:
        Root URL for the API (no trailing slash).
    api_token:
        Optional bearer token for authenticated requests.
    timeout:
        Request timeout in seconds.
    max_retries:
        Maximum number of retry attempts on transient failures.
    retry_backoff:
        Base delay (seconds) for exponential backoff.
    rate_limit_delay:
        Minimum delay between consecutive requests to be polite.
    """

    def __init__(
        self,
        base_url: str = "https://api.quran.com/api/v4",
        *,
        api_token: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        rate_limit_delay: float = 0.2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.rate_limit_delay = rate_limit_delay

        headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "QariETL/1.0 (+https://qari.app)",
        }
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers=headers,
            follow_redirects=True,
        )
        self._last_request_time: float = 0.0
        self._semaphore = asyncio.Semaphore(5)

    # ------------------------------------------------------------------
    # Low-level request with retry + rate limiting
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute an HTTP request with retries and rate limiting.

        Returns the parsed JSON body (the ``data`` key if present).
        Raises ``QuranComHTTPError`` on persistent failure.
        """
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            # Rate-limit: ensure minimum gap between requests
            now = asyncio.get_event_loop().time()
            wait = self.rate_limit_delay - (now - self._last_request_time)
            if wait > 0:
                await asyncio.sleep(wait)

            try:
                async with self._semaphore:
                    self._last_request_time = asyncio.get_event_loop().time()
                    resp = await self._client.request(method, path, params=params)

                if resp.status_code == 429:
                    raise QuranComRateLimitError(
                        f"Rate limited on {path} (attempt {attempt})"
                    )

                resp.raise_for_status()
                payload = resp.json()

                # Quran.com wraps results in {"data": ...} or {"chapters": ...}
                if isinstance(payload, dict) and "data" in payload:
                    return payload["data"]
                return payload

            except httpx.HTTPStatusError as exc:
                last_exc = QuranComHTTPError(
                    exc.response.status_code,
                    str(exc.request.url),
                    exc.response.text,
                )
                logger.warning(
                    "http_status_error",
                    path=path,
                    status=exc.response.status_code,
                    attempt=attempt,
                )
                if exc.response.status_code >= 400 and exc.response.status_code < 500:
                    if exc.response.status_code != 429:
                        raise last_exc  # non-retryable client error

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ReadError) as exc:
                last_exc = exc
                logger.warning(
                    "transport_error",
                    path=path,
                    error=str(exc),
                    attempt=attempt,
                )

            except QuranComRateLimitError as exc:
                last_exc = exc
                logger.warning(
                    "rate_limited",
                    path=path,
                    attempt=attempt,
                )

            # Exponential backoff before next attempt
            if attempt < self.max_retries:
                delay = self.retry_backoff * (2 ** (attempt - 1))
                logger.debug("retry_sleep", delay=delay, attempt=attempt)
                await asyncio.sleep(delay)

        # All retries exhausted
        raise QuranComHTTPError(
            0,
            path,
            f"Exhausted {self.max_retries} retries. Last error: {last_exc}",
        )

    async def _get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self._request("GET", path, params=params)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_surahs(self) -> List[Dict[str, Any]]:
        """Fetch all 114 surahs with metadata.

        Endpoint: ``GET /chapters?language=en``
        Returns a list of surah dicts with keys: id, name_arabic,
        name_simple, revelation_place, revelation_order, verses_count, etc.
        """
        logger.info("fetching_surahs")
        data = await self._get("/chapters", params={"language": "en"})
        # The API returns {"chapters": [...]} (no "data" wrapper)
        if isinstance(data, dict) and "chapters" in data:
            return data["chapters"]
        if isinstance(data, list):
            return data
        return []

    async def get_ayahs(
        self,
        surah_number: int,
        qari_id: int,
        translations: List[int],
    ) -> List[Dict[str, Any]]:
        """Fetch all ayahs for a surah with Uthmani, Imlaei text and translations.

        Endpoint: ``GET /verses/by_chapter/{surah_number}``
        Query params: fields=text_uthmani,text_imlaei,translations; translations=...

        Returns a list of ayah dicts each containing:
        verse_key, verse_number, text_uthmani, text_imlaei, translations, etc.
        """
        logger.info("fetching_ayahs", surah=surah_number, qari=qari_id)
        params: Dict[str, Any] = {
            "fields": "text_uthmani,text_imlaei,text_uthmani_tajweed",
            "translations": ",".join(str(t) for t in translations),
            "per_page": 300,  # max per page
            "page": 1,
        }
        all_verses: List[Dict[str, Any]] = []

        while True:
            data = await self._get(
                f"/verses/by_chapter/{surah_number}", params=params
            )
            if isinstance(data, dict):
                verses = data.get("verses", [])
            elif isinstance(data, list):
                verses = data
            else:
                verses = []

            all_verses.extend(verses)

            # Handle pagination
            paging = data.get("pagination", {}) if isinstance(data, dict) else {}
            total_pages = paging.get("total_pages", 1)
            if params["page"] >= total_pages:
                break
            params["page"] += 1

        logger.info(
            "fetched_ayahs",
            surah=surah_number,
            count=len(all_verses),
        )
        return all_verses

    async def get_word_translations(self, surah_number: int) -> List[Dict[str, Any]]:
        """Fetch word-by-word translations and transliterations for a surah.

        Endpoint: ``GET /verses/by_chapter/{surah_number}`` with ``words=true``.
        The quran.com v4 API has no dedicated ``/by_word`` sub-resource; word
        data is returned inline on each verse when ``words=true`` is set.
        Returns word dicts with: verse_key, word_number, translation,
        transliteration, arabic_text, etc.
        """
        logger.info("fetching_word_translations", surah=surah_number)
        params: Dict[str, Any] = {
            "words": "true",
            "word_fields": "text_uthmani,location,transliteration",
            "word_translation_language": "en",
            "per_page": 300,
            "page": 1,
        }
        all_words: List[Dict[str, Any]] = []

        while True:
            data = await self._get(
                f"/verses/by_chapter/{surah_number}",
                params=params,
            )
            if isinstance(data, dict):
                verses = data.get("verses", [])
            elif isinstance(data, list):
                verses = data
            else:
                verses = []

            # Words are nested on each verse; flatten them out and stamp
            # the parent verse_key onto each word for downstream joins.
            for verse in verses:
                verse_key = verse.get("verse_key", "")
                for word in verse.get("words", []):
                    word.setdefault("verse_key", verse_key)
                    all_words.append(word)

            paging = data.get("pagination", {}) if isinstance(data, dict) else {}
            total_pages = paging.get("total_pages", 1)
            if params["page"] >= total_pages:
                break
            params["page"] += 1

        logger.info(
            "fetched_word_translations",
            surah=surah_number,
            count=len(all_words),
        )
        return all_words

    async def get_audio_segments(
        self,
        surah_number: int,
        qari_id: int,
    ) -> List[Dict[str, Any]]:
        """Fetch ayah audio URLs and segment timestamps for a surah/reciter.

        Endpoint: ``GET /audio/reciters/{qari_id}/by_chapter/{surah_number}``
        Returns audio file dicts with: verse_number, audio_url, segments,
        duration, etc.
        """
        logger.info(
            "fetching_audio_segments",
            surah=surah_number,
            qari=qari_id,
        )
        data = await self._get(
            f"/audio/reciters/{qari_id}/by_chapter/{surah_number}",
            params={"segments": "true"},
        )

        if isinstance(data, dict):
            audio_files = data.get("audio_files", [])
        elif isinstance(data, list):
            audio_files = data
        else:
            audio_files = []

        logger.info(
            "fetched_audio_segments",
            surah=surah_number,
            qari=qari_id,
            count=len(audio_files),
        )
        return audio_files

    async def get_tajweed_text(self, surah_number: int) -> List[Dict[str, Any]]:
        """Fetch the Uthmani tajweed-markup text variant for a surah.

        Endpoint: ``GET /verses/by_chapter/{surah_number}``
        with ``fields=text_uthmani_tajweed``.

        Returns a list of verse dicts with verse_key and text_uthmani_tajweed.
        """
        logger.info("fetching_tajweed_text", surah=surah_number)
        params: Dict[str, Any] = {
            "fields": "text_uthmani_tajweed",
            "per_page": 300,
            "page": 1,
        }
        all_verses: List[Dict[str, Any]] = []

        while True:
            data = await self._get(
                f"/verses/by_chapter/{surah_number}", params=params
            )
            if isinstance(data, dict):
                verses = data.get("verses", [])
            elif isinstance(data, list):
                verses = data
            else:
                verses = []

            all_verses.extend(verses)

            paging = data.get("pagination", {}) if isinstance(data, dict) else {}
            total_pages = paging.get("total_pages", 1)
            if params["page"] >= total_pages:
                break
            params["page"] += 1

        logger.info(
            "fetched_tajweed_text",
            surah=surah_number,
            count=len(all_verses),
        )
        return all_verses

    async def get_qaris(self) -> List[Dict[str, Any]]:
        """Fetch the list of available reciters (qaris).

        Endpoint: ``GET /audio/reciters``
        """
        logger.info("fetching_qaris")
        data = await self._get("/audio/reciters")
        if isinstance(data, dict):
            return data.get("reciters", [])
        if isinstance(data, list):
            return data
        return []

    async def get_word_audio(self, surah_number: int) -> List[Dict[str, Any]]:
        """Fetch per-word audio URLs for a surah.

        Endpoint: ``GET /verses/by_chapter/{surah_number}`` with ``words=true``.
        Per-word audio URLs are returned inline on each word.
        """
        logger.info("fetching_word_audio", surah=surah_number)
        data = await self._get(
            f"/verses/by_chapter/{surah_number}",
            params={"words": "true", "word_fields": "audio_url,location", "per_page": 300},
        )
        if isinstance(data, dict):
            return data.get("verses", [])
        if isinstance(data, list):
            return data
        return []

    # ------------------------------------------------------------------
    # Checksum helper
    # ------------------------------------------------------------------

    @staticmethod
    def checksum_text(text: str) -> str:
        """Compute SHA-256 checksum of a Quranic text block."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()
        logger.info("client_closed")
