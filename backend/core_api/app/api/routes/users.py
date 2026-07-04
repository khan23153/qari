"""User onboarding and home aggregation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.core.deps import get_db, get_current_user
from app.core.security import create_backend_jwt
from app.models.user import User, UserStats
from app.models.content import Lesson
from app.models.corpus import Surah
from app.schemas.user import OnboardingRequest, UserSchema, HomeResponse
from app.services.redis_service import cache_get, cache_set, cache_delete
from app.services.streak_service import update_streak

router = APIRouter()


@router.post("/users/onboarding", response_model=UserSchema)
async def onboarding(
    req: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
):
    """The ONLY onboarding write. Creates user from Firebase UID."""
    # Check if user already exists
    existing = await db.execute(
        select(User).where(User.auth_provider_id == req.firebase_uid)
    )
    user = existing.scalar_one_or_none()
    if user:
        raise HTTPException(status_code=409, detail="User already onboarded")

    user = User(
        user_id=uuid4(),
        auth_provider_id=req.firebase_uid,
        app_language=req.app_language,
        starting_path=req.starting_path,
        display_name=req.display_name,
    )
    db.add(user)

    # Initialize stats
    stats = UserStats(user_id=user.user_id)
    db.add(stats)
    await db.commit()

    # Invalidate home cache
    await cache_delete(f"home:{user.user_id}")

    return UserSchema.model_validate(user)


@router.post("/users/auth/exchange")
async def exchange_token(
    firebase_uid: str,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Firebase UID for a backend JWT (after Firebase verification)."""
    jwt_token = create_backend_jwt(firebase_uid)
    return {"access_token": jwt_token, "token_type": "bearer"}


@router.get("/me/home", response_model=HomeResponse)
async def get_home(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Single aggregated call for the home screen."""
    cache_key = f"home:{user.user_id}"
    cached = await cache_get(cache_key)
    if cached:
        return HomeResponse(**cached)

    # Get stats
    stats_result = await db.execute(
        select(UserStats).where(UserStats.user_id == user.user_id)
    )
    stats = stats_result.scalar_one_or_none()

    # Get next lesson based on starting_path
    next_lesson = None
    if user.starting_path == "foundation":
        lesson_result = await db.execute(
            select(Lesson)
            .where(Lesson.review_status == "published", Lesson.module == 1)
            .order_by(Lesson.unit_number, Lesson.sequence)
            .limit(1)
        )
        lesson = lesson_result.scalar_one_or_none()
        if lesson:
            next_lesson = {
                "lesson_id": str(lesson.lesson_id),
                "title": lesson.title,
                "module": lesson.module,
            }

    # Get due flashcard count
    from app.services.flashcard_service import get_due_flashcards
    due_cards = await get_due_flashcards(db, user.user_id, limit=20)

    # Update streak
    streak_info = await update_streak(db, user.user_id, stats.timezone if stats else "Asia/Kolkata")

    data = HomeResponse(
        streak=streak_info["streak"],
        xp_total=stats.xp_total if stats else 0,
        next_lesson=next_lesson,
        due_flashcard_count=len(due_cards),
        continue_reading=None,
        daily_goal_progress=0.0,
    )
    await cache_set(cache_key, data.model_dump(), ttl=60)
    return data
