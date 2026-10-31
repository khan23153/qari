"""On-demand fetching of hadith collections with a size-capped disk cache.

Only the starter seed ships with the app; everything else is pulled from the
public-domain dataset the first time someone opens it and kept in a bounded
LRU cache, so the VPS disk stays light.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Awaitable, Callable, Optional

import httpx

FetchJson = Callable[[str], Awaitable[dict]]


class RemoteFetchError(Exception):
    """The remote catalog could not be reached or returned bad data."""


class DiskJsonCache:
    """JSON files under [root], evicted least-recently-used beyond [max_bytes]."""

    def __init__(self, root: Path | str, max_bytes: int):
        self.root = Path(root).resolve()
        self.max_bytes = max_bytes
        self._clock = 0

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root not in path.parents:
            raise ValueError(f"cache key escapes cache root: {key!r}")
        return path

    def _touch(self, path: Path) -> None:
        # Strictly increasing mtimes keep LRU order exact even within one tick.
        self._clock = max(time.time_ns(), self._clock + 1)
        os.utime(path, ns=(self._clock, self._clock))

    def get(self, key: str) -> Optional[dict]:
        path = self._path(key)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        self._touch(path)
        return data

    def put(self, key: str, value: dict) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        self._touch(path)
        self._evict(keep=path)

    def _files(self) -> list[Path]:
        if not self.root.exists():
            return []
        return [p for p in self.root.rglob("*.json") if p.is_file()]

    def size_bytes(self) -> int:
        return sum(p.stat().st_size for p in self._files())

    def _evict(self, keep: Path) -> None:
        files = sorted(self._files(), key=lambda p: p.stat().st_mtime_ns)
        total = sum(p.stat().st_size for p in files)
        for path in files:
            if total <= self.max_bytes:
                break
            if path == keep:
                continue
            total -= path.stat().st_size
            path.unlink(missing_ok=True)


class RemoteHadithSource:
    """Reads `fawazahmed0/hadith-api`-shaped editions through [cache]."""

    def __init__(self, fetch_json: FetchJson, cache: DiskJsonCache, base_url: str):
        self._fetch = fetch_json
        self._cache = cache
        self._base = base_url.rstrip("/")

    async def _get(self, rel: str) -> dict:
        cached = self._cache.get(rel)
        if cached is not None:
            return cached
        data = await self._fetch(f"{self._base}/{rel}")
        if not isinstance(data, dict) or "hadiths" not in data:
            raise RemoteFetchError(rel)
        self._cache.put(rel, data)
        return data

    async def _optional(self, rel: str) -> Optional[dict]:
        try:
            return await self._get(rel)
        except RemoteFetchError:
            return None

    async def hadith(self, arabic_edition: str, translation_edition: str, number: int) -> tuple[dict, Optional[dict]]:
        """(Arabic edition record, translation record or None)."""
        ara = await self._get(f"editions/{arabic_edition}/{number}.json")
        eng = await self._optional(f"editions/{translation_edition}/{number}.json")
        return ara, eng

    async def edition(self, name: str) -> dict:
        """A whole edition (several MB), fetched without the disk cache: the
        forward-check index is built from it once and saved on its own."""
        rel = f"editions/{name}.min.json"
        data = await self._fetch(f"{self._base}/{rel}")
        if not isinstance(data, dict) or "hadiths" not in data:
            raise RemoteFetchError(rel)
        return data

    async def section(self, arabic_edition: str, translation_edition: str, book: int) -> tuple[dict, Optional[dict]]:
        ara = await self._get(f"editions/{arabic_edition}/sections/{book}.json")
        eng = await self._optional(f"editions/{translation_edition}/sections/{book}.json")
        return ara, eng


def httpx_fetcher(timeout_sec: float) -> FetchJson:
    """A [FetchJson] backed by httpx that maps every failure to RemoteFetchError."""

    async def fetch(url: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RemoteFetchError(url) from exc

    return fetch
