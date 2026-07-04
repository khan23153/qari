"""Badge evaluation — checks machine-evaluable criteria against user stats."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserStats, UserBadge
from app.models.content import Badge
from uuid import UUID


async def evaluate_badges(db: AsyncSession, user_id: UUID) -> list[str]:
    """Check all badges and award any newly earned ones. Returns badge_ids earned."""
    stats_result = await db.execute(
        select(UserStats).where(UserStats.user_id == user_id)
    )
    stats = stats_result.scalar_one_or_none()
    if not stats:
        return []

    badges_result = await db.execute(select(Badge))
    all_badges = badges_result.scalars().all()

    earned_result = await db.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
    )
    already_earned = {row[0] for row in earned_result}

    newly_earned = []
    for badge in all_badges:
        if badge.badge_id in already_earned:
            continue
        if _check_criteria(badge.criteria, stats):
            db.add(UserBadge(user_id=user_id, badge_id=badge.badge_id))
            newly_earned.append(badge.badge_id)

    if newly_earned:
        await db.flush()
    return newly_earned


def _check_criteria(criteria: dict, stats: UserStats) -> bool:
    """Evaluate machine-readable badge criteria."""
    crit_type = criteria.get("type")
    if crit_type == "streak":
        return stats.current_streak >= criteria.get("days", 0)
    elif crit_type == "xp":
        return stats.xp_total >= criteria.get("amount", 0)
    elif crit_type == "longest_streak":
        return stats.longest_streak >= criteria.get("days", 0)
    return False
