"""Streak service: idempotent streak updates with freeze grace.

Rules from spec:
- Streak update is idempotent per user-timezone-day (Redis lock)
- 1-day freeze grace per 30 days
- If a day is missed and user has freeze credits, the streak is preserved
- Freeze credits are granted once per 30-day window
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.user import User
from app.services import redis_service
from shared import STREAK_FREEZE_GRACE_WINDOW_DAYS, STREAK_FREEZE_GRANT, RedisKeys

logger = get_logger(__name__)


def _user_today(user: User) -> date:
    """Get today's date in the user's timezone."""
    # In production, use zoneinfo for proper tz math. For simplicity here,
    # we use UTC date as a reasonable proxy. The user.timezone field is
    # available for more precise computation.
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(user.timezone)
        return datetime.now(tz).date()
    except Exception:
        return datetime.now(timezone.utc).date()


def _days_between(d1: date, d2: date) -> int:
    """Absolute day difference between two dates."""
    return abs((d2 - d1).days)


async def update_streak(
    db: AsyncSession,
    user: User,
    today: Optional[date] = None,
) -> tuple[int, bool]:
    """Update the user's streak idempotently.

    Returns ``(current_streak, streak_updated)``.

    Logic:
    1. Acquire a Redis lock for (user, today) — if already held, no-op.
    2. If last_streak_date is None → first ever activity: streak = 1.
    3. If last_streak_date == today → already counted (shouldn't happen with lock).
    4. If last_streak_date == yesterday → streak += 1.
    5. If gap == 1 day and freeze_credits > 0 → use freeze, streak += 1, credits -= 1.
    6. If gap > 1 → streak = 1 (reset).
    7. Check freeze credit grant eligibility (1 per 30 days).
    8. Update longest_streak if current exceeds it.
    """
    today = today or _user_today(user)
    date_str = today.isoformat()

    # --- Idempotency: Redis lock per user-timezone-day ---
    lock_acquired = await redis_service.acquire_streak_lock(str(user.id), date_str)
    if not lock_acquired:
        # Already processed today
        return user.current_streak, False

    last = user.last_streak_date

    if last is None:
        # First ever activity
        new_streak = 1
        streak_updated = True
    elif last == today:
        # Already counted (lock race or replay)
        return user.current_streak, False
    elif last == today - timedelta(days=1):
        # Consecutive day
        new_streak = user.current_streak + 1
        streak_updated = True
    else:
        gap_days = _days_between(last, today)
        if gap_days == 2 and user.freeze_credits > 0:
            # Use a freeze credit to bridge a 1-day gap
            new_streak = user.current_streak + 1
            user.freeze_credits -= 1
            streak_updated = True
            logger.info(
                "streak.freeze_used",
                user_id=str(user.id),
                remaining_credits=user.freeze_credits,
            )
        else:
            # Gap too large — reset streak
            new_streak = 1
            streak_updated = True
            logger.info(
                "streak.reset",
                user_id=str(user.id),
                gap_days=gap_days,
                previous_streak=user.current_streak,
            )

    # --- Freeze credit grant: 1 per 30 days ---
    _maybe_grant_freeze(user, today)

    # --- Apply updates ---
    user.current_streak = new_streak
    user.last_streak_date = today
    if new_streak > user.longest_streak:
        user.longest_streak = new_streak

    await db.flush()
    logger.info(
        "streak.updated",
        user_id=str(user.id),
        new_streak=new_streak,
        updated=streak_updated,
    )
    return new_streak, streak_updated


def _maybe_grant_freeze(user: User, today: date) -> None:
    """Grant a freeze credit if 30+ days have passed since the last grant."""
    if user.last_freeze_grant_date is None:
        user.last_freeze_grant_date = today
        user.freeze_credits += STREAK_FREEZE_GRANT
        logger.info("streak.freeze_granted", user_id=str(user.id), credits=user.freeze_credits)
        return

    days_since_grant = _days_between(user.last_freeze_grant_date, today)
    if days_since_grant >= STREAK_FREEZE_GRACE_WINDOW_DAYS:
        user.last_freeze_grant_date = today
        user.freeze_credits += STREAK_FREEZE_GRANT
        logger.info(
            "streak.freeze_granted",
            user_id=str(user.id),
            credits=user.freeze_credits,
            days_since_last=days_since_grant,
        )
