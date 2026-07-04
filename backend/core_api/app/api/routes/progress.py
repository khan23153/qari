"""User progress endpoints — lessons and ayahs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from app.core.deps import get_db, get_current_user
from app.models.user import (
    User, UserLessonProgress, UserAyahProgress, UserStats,
)
from app.models.content import Lesson
from app.schemas.user import LessonProgressRequest, LessonProgressResponse, AyahProgressRequest
from app.services.streak_service import update_streak
from app.services.badge_service import evaluate_badges
from app.services.redis_service import cache_delete

router = APIRouter()


@router.post("/progress/lessons/{lesson_id}", response_model=LessonProgressResponse)
async def update_lesson_progress(
    lesson_id: str,
    req: LessonProgressRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record lesson completion. Returns XP awarded, new badges, streak state."""
    # Verify lesson exists
    lesson_result = await db.execute(
        select(Lesson).where(Lesson.lesson_id == lesson_id)
    )
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Upsert progress
    existing = await db.execute(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == user.user_id,
            UserLessonProgress.lesson_id == lesson_id,
        )
    )
    progress = existing.scalar_one_or_none()

    xp_awarded = 0
    if progress is None:
        progress = UserLessonProgress(
            user_id=user.user_id,
            lesson_id=lesson_id,
            status=req.status,
            best_score=req.score,
            attempts=1,
            completed_at=datetime.now(timezone.utc) if req.status == "completed" else None,
        )
        db.add(progress)
        if req.status == "completed":
            xp_awarded = lesson.xp_reward
    else:
        progress.attempts += 1
        if req.status == "completed":
            if progress.status != "completed":
                xp_awarded = lesson.xp_reward
            progress.status = "completed"
            progress.completed_at = datetime.now(timezone.utc)
            if req.score and (progress.best_score is None or req.score > progress.best_score):
                progress.best_score = req.score

    # Update XP
    if xp_awarded > 0:
        await db.execute(
            update(UserStats)
            .where(UserStats.user_id == user.user_id)
            .values(xp_total=UserStats.xp_total + xp_awarded)
        )

    # Update streak
    stats_result = await db.execute(
        select(UserStats).where(UserStats.user_id == user.user_id)
    )
    stats = stats_result.scalar_one_or_none()
    streak_info = await update_streak(db, user.user_id, stats.timezone if stats else "Asia/Kolkata")

    # Evaluate badges
    new_badges = await evaluate_badges(db, user.user_id)

    await db.commit()
    await cache_delete(f"home:{user.user_id}")

    return LessonProgressResponse(
        xp_awarded=xp_awarded,
        new_badges=new_badges,
        streak_state=streak_info,
    )


@router.post("/progress/ayahs")
async def mark_ayahs_studied(
    req: AyahProgressRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch mark ayahs as studied for Module 2 reading progress."""
    for ayah_num in req.ayah_numbers:
        existing = await db.execute(
            select(UserAyahProgress).where(
                UserAyahProgress.user_id == user.user_id,
                UserAyahProgress.surah_number == req.surah_number,
                UserAyahProgress.ayah_number == ayah_num,
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(UserAyahProgress(
                user_id=user.user_id,
                surah_number=req.surah_number,
                ayah_number=ayah_num,
            ))

    await db.commit()
    await cache_delete(f"home:{user.user_id}")
    return {"status": "ok", "marked": len(req.ayah_numbers)}
