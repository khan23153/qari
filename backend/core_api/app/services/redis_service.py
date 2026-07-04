"""Redis cache service for content caching and session state."""
import json
from typing import Optional, Any
import redis.asyncio as redis

from app.core.config import settings

_pool: redis.ConnectionPool | None = None


def _get_pool() -> redis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL, decode_responses=True
        )
    return _pool


def _get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_get_pool())


async def cache_get(key: str) -> Optional[Any]:
    """Get a JSON-serialized value from cache."""
    r = _get_redis()
    raw = await r.get(key)
    if raw:
        return json.loads(raw)
    return None


async def cache_set(key: str, value: Any, ttl: int = 86400) -> None:
    """Set a JSON-serializable value in cache with TTL (default 24h)."""
    r = _get_redis()
    await r.setex(key, ttl, json.dumps(value, default=str))


async def cache_delete(key: str) -> None:
    r = _get_redis()
    await r.delete(key)


async def rate_limit(key: str, limit: int, window: int) -> bool:
    """Sliding window rate limiter. Returns True if allowed."""
    r = _get_redis()
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    results = await pipe.execute()
    return results[0] <= limit
