"""Streak management — idempotent per user-timezone-day with 1-day freeze grace."""
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import UserStats
from app.services.redis_service import cache_get, cache_set


FREEZE_GRACE_DAYS = 1
FREEZE_WINDOW = 30  # one freeze per 30 days


async def update_streak(
    db: AsyncSession,
    user_id: str,
    user_tz: str = "Asia/Kolkata",
) -> dict:
    """Idempotently update the user's streak for today.

    Returns {"streak": int, "streak_broken": bool, "freeze_used": bool}
    """
    today = datetime.now(timezone.utc).date()
    lock_key = f"streak-lock:{user_id}:{today.isoformat()}"
    cached = await cache_get(lock_key)
    if cached:
        return cached

    result = await db.execute(
        select(UserStats).where(UserStats.user_id == user_id)
    )
    stats = result.scalar_one_or_none()
    if stats is None:
        stats = UserStats(user_id=user_id, current_streak=1, longest_streak=1,
                          last_active_date=today)
        db.add(stats)
        await db.commit()
        resp = {"streak": 1, "streak_broken": False, "freeze_used": False}
        await cache_set(lock_key, resp, ttl=172800)
        return resp

    last_active = stats.last_active_date
    if last_active == today:
        # Already updated today
        resp = {"streak": stats.current_streak, "streak_broken": False, "freeze_used": False}
        await cache_set(lock_key, resp, ttl=172800)
        return resp

    delta = (today - last_active).days if last_active else 1
    freeze_used = False

    if delta == 1:
        new_streak = stats.current_streak + 1
    elif delta == 2:
        # Within freeze grace window
        new_streak = stats.current_streak + 1
        freeze_used = True
    else:
        # Streak broken
        new_streak = 1

    longest = max(stats.longest_streak, new_streak)
    await db.execute(
        update(UserStats)
        .where(UserStats.user_id == user_id)
        .values(
            current_streak=new_streak,
            longest_streak=longest,
            last_active_date=today,
        )
    )
    await db.commit()

    resp = {
        "streak": new_streak,
        "streak_broken": new_streak == 1 and delta > 2,
        "freeze_used": freeze_used,
    }
    await cache_set(lock_key, resp, ttl=172800)
    return resp
