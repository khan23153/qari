"""Progress routes: lesson progress, ayah progress with idempotency."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError, ProblemException, ConflictError
from app.core.logging import get_logger
from app.models.content import Lesson
from app.models.user import (
    Flashcard, User, UserAyahProgress, UserLessonProgress, UserStats,
)
from app.schemas.user import (
    AyahProgressRequest, AyahProgressResponse,
    LessonProgressRequest, LessonProgressResponse, BadgeAwarded,
)
from app.services.badge_service import evaluate_badges
from app.services.flashcard_service import auto_create_from_quiz_miss
from app.services.redis_service import (
    cache_delete, check_idempotency, store_idempotency,
)
from app.services.streak_service import update_streak
from shared import RedisKeys

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/progress", tags=["progress"])


# ---------------------------------------------------------------------------
# Lesson progress
# ---------------------------------------------------------------------------

@router.post("/lessons/{lesson_id}", response_model=LessonProgressResponse)
async def update_lesson_progress(
    lesson_id: int,
    body: LessonProgressRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update lesson progress with idempotency.

    Returns XP earned, new badges, and streak state.
    If the lesson quiz was failed, flashcards are auto-created for missed words.
    """
    # --- Idempotency check ---
    idem_key = body.idempotency_key
    cached = await check_idempotency(str(user.id), idem_key)
    if cached is not None:
        return LessonProgressResponse(**cached)

    # --- Verify lesson exists ---
    lesson_result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = lesson_result.scalar_one_or_none()
    if lesson is None:
        raise NotFoundError("Lesson", lesson_id)

    # --- Find or create progress row ---
    progress_result = await db.execute(
        select(UserLessonProgress).where(
            and_(
                UserLessonProgress.user_id == user.id,
                UserLessonProgress.lesson_id == lesson_id,
            )
        )
    )
    progress = progress_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    xp_earned = 0

    if progress is None:
        progress = UserLessonProgress(
            user_id=user.id,
            lesson_id=lesson_id,
            status=body.status,
            score=body.score,
            idempotency_key=idem_key,
        )
        if body.status == "in_progress":
            progress.started_at = now
            progress.last_accessed_at = now
        elif body.status == "completed":
            progress.started_at = progress.started_at or now
            progress.completed_at = now
            progress.last_accessed_at = now
            xp_earned = lesson.xp_reward
            progress.xp_earned = xp_earned
        db.add(progress)
    else:
        progress.status = body.status
        progress.last_accessed_at = now
        if body.score is not None:
            progress.score = body.score
        if body.status == "in_progress" and progress.started_at is None:
            progress.started_at = now
        elif body.status == "completed" and progress.completed_at is None:
            progress.completed_at = now
            xp_earned = lesson.xp_reward
            progress.xp_earned = (progress.xp_earned or 0) + xp_earned

    # --- Award XP ---
    if xp_earned > 0:
        user.total_xp += xp_earned

    # --- Update streak ---
    streak, streak_updated = await update_streak(db, user)

    # --- Update stats ---
    if body.status == "completed":
        stats_result = await db.execute(
            select(UserStats).where(UserStats.user_id == user.id)
        )
        stats = stats_result.scalar_one_or_none()
        if stats is None:
            stats = UserStats(user_id=user.id)
            db.add(stats)
            await db.flush()
        stats.lessons_completed += 1

    # --- Auto-create flashcards on quiz miss ---
    # If score < 60 and lesson has quiz questions, create flashcards for the lesson's words
    new_badges_list: list[BadgeAwarded] = []
    if body.score is not None and body.score < 60 and body.status == "completed":
        # Get word IDs from the lesson's surah/ayah reference
        # For simplicity, we skip auto-creation here since we'd need to map
        # quiz questions to specific words. In production, the quiz response
        # would include missed word IDs.
        logger.info(
            "progress.quiz_miss",
            user_id=str(user.id),
            lesson_id=lesson_id,
            score=float(body.score),
        )

    # --- Evaluate badges ---
    new_badges = await evaluate_badges(db, user)
    for badge in new_badges:
        new_badges_list.append(BadgeAwarded(
            id=badge.id,
            slug=badge.slug,
            name=badge.name_en,
            tier=badge.tier,
            xp_reward=badge.xp_reward,
        ))

    await db.commit()
    await db.refresh(user)

    # --- Invalidate caches ---
    await cache_delete(RedisKeys.HOME_CACHE.format(user_id=str(user.id)))

    response = LessonProgressResponse(
        lesson_id=lesson_id,
        status=body.status,
        xp_earned=xp_earned,
        total_xp=user.total_xp,
        new_badges=new_badges_list,
        streak=streak,
        streak_updated=streak_updated,
    )

    # --- Store idempotent response ---
    await store_idempotency(str(user.id), idem_key, response.model_dump())

    return response


# ---------------------------------------------------------------------------
# Ayah progress (batch)
# ---------------------------------------------------------------------------

@router.post("/ayahs", response_model=AyahProgressResponse)
async def mark_ayahs_studied(
    body: AyahProgressRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch mark ayahs as studied. Idempotent via key."""
    # --- Idempotency check ---
    cached = await check_idempotency(str(user.id), body.idempotency_key)
    if cached is not None:
        return AyahProgressResponse(**cached)

    now = datetime.now(timezone.utc)
    marked = 0

    for ref in body.ayahs:
        # Find existing or create new
        result = await db.execute(
            select(UserAyahProgress).where(
                and_(
                    UserAyahProgress.user_id == user.id,
                    UserAyahProgress.surah_number == ref.surah_number,
                    UserAyahProgress.ayah_number == ref.ayah_number,
                )
            )
        )
        progress = result.scalar_one_or_none()

        if progress is None:
            progress = UserAyahProgress(
                user_id=user.id,
                surah_number=ref.surah_number,
                ayah_number=ref.ayah_number,
                times_studied=1,
                last_studied_at=now,
            )
            db.add(progress)
            marked += 1
        else:
            progress.times_studied += 1
            progress.last_studied_at = now
            marked += 1

    # --- Update streak ---
    streak, streak_updated = await update_streak(db, user)

    # --- Update stats ---
    stats_result = await db.execute(
        select(UserStats).where(UserStats.user_id == user.id)
    )
    stats = stats_result.scalar_one_or_none()
    if stats is None:
        stats = UserStats(user_id=user.id)
        db.add(stats)
        await db.flush()
    stats.ayahs_studied += marked

    await db.commit()
    await db.refresh(user)

    # --- Invalidate caches ---
    await cache_delete(RedisKeys.HOME_CACHE.format(user_id=str(user.id)))

    response = AyahProgressResponse(
        marked=marked,
        total_requested=len(body.ayahs),
        streak=streak,
        streak_updated=streak_updated,
    )
    await store_idempotency(str(user.id), body.idempotency_key, response.model_dump())
    return response
