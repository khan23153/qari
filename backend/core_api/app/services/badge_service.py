"""Badge service: evaluate and award badges based on user activity."""

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.content import Badge
from app.models.user import User, UserBadge, UserStats, UserLessonProgress, FlashcardReview, RecitationSession

logger = get_logger(__name__)


async def evaluate_badges(
    db: AsyncSession,
    user: User,
) -> list[Badge]:
    """Check all badge criteria and award any newly-earned badges.

    Returns a list of newly awarded Badge objects.
    """
    # Fetch all badges
    badges_result = await db.execute(select(Badge))
    all_badges = list(badges_result.scalars().all())

    # Fetch already-awarded badge IDs
    awarded_result = await db.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == user.id)
    )
    awarded_ids = {row[0] for row in awarded_result}

    # Gather user stats
    stats = await _get_user_stats(db, user.id)
    lessons_completed = await _count_completed_lessons(db, user.id)
    flashcards_reviewed = await _count_flashcard_reviews(db, user.id)
    recitation_sessions = await _count_recitation_sessions(db, user.id)
    streak = user.current_streak
    total_xp = user.total_xp

    newly_awarded: list[Badge] = []

    for badge in all_badges:
        if badge.id in awarded_ids:
            continue

        if _check_criteria(badge, {
            "lessons_completed": lessons_completed,
            "flashcards_reviewed": flashcards_reviewed,
            "recitation_sessions": recitation_sessions,
            "streak": streak,
            "total_xp": total_xp,
            "stats": stats,
        }):
            # Award the badge
            user_badge = UserBadge(user_id=user.id, badge_id=badge.id)
            db.add(user_badge)
            # Award XP from badge
            user.total_xp += badge.xp_reward
            newly_awarded.append(badge)
            logger.info(
                "badge.awarded",
                user_id=str(user.id),
                badge_slug=badge.slug,
                xp_reward=badge.xp_reward,
            )

    if newly_awarded:
        await db.flush()

    return newly_awarded


async def _get_user_stats(db: AsyncSession, user_id) -> Optional[UserStats]:
    result = await db.execute(
        select(UserStats).where(UserStats.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _count_completed_lessons(db: AsyncSession, user_id) -> int:
    result = await db.execute(
        select(func.count(UserLessonProgress.id)).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.status == "completed",
        )
    )
    return result.scalar() or 0


async def _count_flashcard_reviews(db: AsyncSession, user_id) -> int:
    result = await db.execute(
        select(func.count(FlashcardReview.id)).where(FlashcardReview.user_id == user_id)
    )
    return result.scalar() or 0


async def _count_recitation_sessions(db: AsyncSession, user_id) -> int:
    result = await db.execute(
        select(func.count(RecitationSession.id)).where(
            RecitationSession.user_id == user_id,
            RecitationSession.status == "completed",
        )
    )
    return result.scalar() or 0


def _check_criteria(badge: Badge, ctx: dict) -> bool:
    """Evaluate badge criteria from criteria_json.

    Supported criteria keys (all optional, AND-ed together):
    - min_lessons_completed
    - min_flashcards_reviewed
    - min_recitation_sessions
    - min_streak
    - min_xp
    """
    criteria = badge.criteria_json or {}
    if not criteria:
        return False

    if "min_lessons_completed" in criteria:
        if ctx["lessons_completed"] < criteria["min_lessons_completed"]:
            return False
    if "min_flashcards_reviewed" in criteria:
        if ctx["flashcards_reviewed"] < criteria["min_flashcards_reviewed"]:
            return False
    if "min_recitation_sessions" in criteria:
        if ctx["recitation_sessions"] < criteria["min_recitation_sessions"]:
            return False
    if "min_streak" in criteria:
        if ctx["streak"] < criteria["min_streak"]:
            return False
    if "min_xp" in criteria:
        if ctx["total_xp"] < criteria["min_xp"]:
            return False

    return True
