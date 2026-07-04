"""Redis service: caching, rate limiting, idempotency, and stream helpers."""

import json
import time
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger
from shared import RedisKeys

logger = get_logger(__name__)

_pool: Optional[redis.ConnectionPool] = None
_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """Initialise the async Redis connection pool."""
    global _pool, _client
    _pool = redis.ConnectionPool.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        decode_responses=True,
    )
    _client = redis.Redis(connection_pool=_pool)
    try:
        await _client.ping()
        logger.info("redis.connected", url=settings.redis_url)
    except Exception as exc:
        logger.error("redis.connection_failed", error=str(exc))
        _client = None


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _pool, _client
    if _client:
        await _client.aclose()
    if _pool:
        await _pool.aclose()
    _client = None
    _pool = None
    logger.info("redis.closed")


def get_redis() -> redis.Redis:
    """Return the Redis client. Raises if not initialised."""
    if _client is None:
        raise RuntimeError("Redis not initialised — call init_redis() first")
    return _client


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

async def cache_get(key: str) -> Optional[Any]:
    """Get a cached JSON value, or ``None`` if missing."""
    try:
        raw = await get_redis().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("redis.cache_get_failed", key=key, error=str(exc))
        return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    """Set a cached JSON value with TTL."""
    try:
        await get_redis().setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("redis.cache_set_failed", key=key, error=str(exc))


async def cache_delete(key: str) -> None:
    """Delete a cached key."""
    try:
        await get_redis().delete(key)
    except Exception as exc:
        logger.warning("redis.cache_delete_failed", key=key, error=str(exc))


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern."""
    try:
        keys = []
        async for key in get_redis().scan_iter(match=pattern, count=200):
            keys.append(key)
        if keys:
            await get_redis().delete(*keys)
    except Exception as exc:
        logger.warning("redis.cache_delete_pattern_failed", pattern=pattern, error=str(exc))


# ---------------------------------------------------------------------------
# Rate limiting — sliding window
# ---------------------------------------------------------------------------

async def check_rate_limit(
    user_id: str,
    endpoint: str,
    max_requests: Optional[int] = None,
    window_sec: Optional[int] = None,
) -> bool:
    """Sliding-window rate limiter.

    Returns ``True`` if the request is allowed, ``False`` if rate-limited.
    Uses a sorted set with timestamps for precise sliding window semantics.
    """
    if not settings.rate_limit_enabled:
        return True

    max_req = max_requests or settings.rate_limit_requests
    window = window_sec or settings.rate_limit_window_sec
    key = RedisKeys.RATE_LIMIT.format(user_id=user_id, endpoint=endpoint)
    now = time.time()
    window_start = now - window

    try:
        r = get_redis()
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)       # remove expired
        pipe.zadd(key, {str(now): now})                    # add current request
        pipe.zcard(key)                                     # count in window
        pipe.expire(key, window + 1)                        # auto-expire
        results = await pipe.execute()
        count = results[2]
        if count > max_req:
            logger.warning("rate_limit.exceeded", user_id=user_id, endpoint=endpoint, count=count)
            return False
        return True
    except Exception as exc:
        logger.error("rate_limit.check_failed", error=str(exc))
        # Fail open — allow the request if Redis is down
        return True


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

async def check_idempotency(user_id: str, key: str) -> Optional[dict]:
    """Check if an idempotency key has been seen. Return cached response if so."""
    redis_key = RedisKeys.IDEMPOTENCY.format(user_id=user_id, key=key)
    try:
        raw = await get_redis().get(redis_key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


async def store_idempotency(user_id: str, key: str, response: dict, ttl: int = 86400) -> None:
    """Store an idempotent response so a replay returns the same result."""
    redis_key = RedisKeys.IDEMPOTENCY.format(user_id=user_id, key=key)
    try:
        await get_redis().setex(redis_key, ttl, json.dumps(response, default=str))
    except Exception as exc:
        logger.warning("idempotency.store_failed", error=str(exc))


# ---------------------------------------------------------------------------
# Streak lock
# ---------------------------------------------------------------------------

async def acquire_streak_lock(user_id: str, date_str: str) -> bool:
    """Acquire a streak lock for a user-timezone-day.

    Returns ``True`` if this is the first call for this day (lock acquired),
    ``False`` if already processed.
    """
    key = RedisKeys.STREAK_LOCK.format(user_id=user_id, date=date_str)
    try:
        result = await get_redis().set(key, "1", nx=True, ex=RedisKeys.TTL_STREAK_LOCK)
        return result is not None
    except Exception:
        # If Redis is down, allow the update (fail open)
        return True


# ---------------------------------------------------------------------------
# Flashcard daily cap
# ---------------------------------------------------------------------------

async def get_flashcard_daily_count(user_id: str, date_str: str) -> int:
    """Get the number of new flashcards created today for a user."""
    key = RedisKeys.FLASHCARD_DAILY_CAP.format(user_id=user_id, date=date_str)
    try:
        raw = await get_redis().get(key)
        return int(raw) if raw else 0
    except Exception:
        return 0


async def increment_flashcard_daily_count(user_id: str, date_str: str, amount: int = 1) -> int:
    """Increment the daily flashcard creation counter. Returns the new count."""
    key = RedisKeys.FLASHCARD_DAILY_CAP.format(user_id=user_id, date=date_str)
    try:
        new_count = await get_redis().incrby(key, amount)
        await get_redis().expire(key, 86400)
        return new_count
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Redis Streams (for recitation jobs)
# ---------------------------------------------------------------------------

async def enqueue_recitation_job(session_id: str, payload: dict) -> str:
    """Enqueue a recitation job onto the Redis Stream.

    Returns the stream entry ID.
    """
    try:
        entry_id = await get_redis().xadd(
            RedisKeys.RECITATION_STREAM,
            {"session_id": session_id, **{k: json.dumps(v) for k, v in payload.items()}},
            maxlen=10000,
            approximate=True,
        )
        logger.info("recitation.enqueued", session_id=session_id, entry_id=entry_id)
        return entry_id
    except Exception as exc:
        logger.error("recitation.enqueue_failed", session_id=session_id, error=str(exc))
        raise


async def publish_recitation_result(session_id: str, result: dict) -> None:
    """Publish a recitation result to a per-session Redis channel for WebSocket delivery."""
    key = RedisKeys.RECITATION_RESULTS.format(session_id=session_id)
    try:
        await get_redis().publish(key, json.dumps(result, default=str))
    except Exception as exc:
        logger.warning("recitation.publish_failed", session_id=session_id, error=str(exc))
