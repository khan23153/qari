"""Learning content endpoints — lesson manifests and detail."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.deps import get_db
from app.models.content import Lesson, QuizQuestion
from app.schemas.content import LessonSummary, LessonDetail
from app.services.redis_service import cache_get, cache_set

router = APIRouter()


@router.get("/lessons", response_model=list[LessonSummary])
async def list_lessons(
    module: Optional[int] = Query(None, ge=1, le=3),
    lang: str = Query("en", pattern="^(en|ur|hi_latn)$"),
    db: AsyncSession = Depends(get_db),
):
    """Published lesson manifest. API serves only review_status='published'."""
    cache_key = f"lessons:list:{module or 'all'}:{lang}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    query = (
        select(Lesson)
        .where(Lesson.review_status == "published")
        .order_by(Lesson.module, Lesson.unit_number, Lesson.sequence)
    )
    if module:
        query = query.where(Lesson.module == module)

    result = await db.execute(query)
    lessons = result.scalars().all()
    data = [LessonSummary.model_validate(l) for l in lessons]
    await cache_set(cache_key, [d.model_dump() for d in data], ttl=3600)
    return data


@router.get("/lessons/{lesson_id}", response_model=LessonDetail)
async def get_lesson(
    lesson_id: str,
    lang: str = Query("en", pattern="^(en|ur|hi_latn)$"),
    db: AsyncSession = Depends(get_db),
):
    """Full lesson payload including quiz questions."""
    cache_key = f"lesson:{lesson_id}:{lang}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(Lesson).where(
            Lesson.lesson_id == lesson_id,
            Lesson.review_status == "published",
        )
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found or not published")

    quiz_result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.lesson_id == lesson_id)
    )
    quiz_questions = [
        QuizQuestionSchema.model_validate(q)
        for q in quiz_result.scalars().all()
    ]

    data = LessonDetail(
        lesson_id=lesson.lesson_id,
        module=lesson.module,
        unit_number=lesson.unit_number,
        sequence=lesson.sequence,
        lesson_type=lesson.lesson_type,
        title=lesson.title,
        xp_reward=lesson.xp_reward,
        min_pass_pct=lesson.min_pass_pct,
        content=lesson.content,
        quiz_questions=quiz_questions,
    )
    await cache_set(cache_key, data.model_dump(), ttl=3600)
    return data


from app.schemas.content import QuizQuestionSchema
