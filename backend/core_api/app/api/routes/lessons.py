"""Lesson routes: list published lessons, get full lesson detail."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.content import Lesson, QuizQuestion
from app.schemas.content import LessonBrief, LessonDetail, QuizQuestionOut
from app.services.redis_service import cache_get, cache_set
from shared import AppLanguage, LessonReviewStatus, RedisKeys

router = APIRouter(prefix="/v1/lessons", tags=["lessons"])


def _lang_field(obj, field_base: str, lang: str) -> Optional[str]:
    return getattr(obj, f"{field_base}_{lang}", None)


@router.get("", response_model=list[LessonBrief])
async def list_lessons(
    module: Optional[str] = Query(None),
    lang: AppLanguage = Query(AppLanguage.en),
    db: AsyncSession = Depends(get_db),
):
    """List published lessons, optionally filtered by module (cached)."""
    cache_key = RedisKeys.LESSON_LIST_CACHE.format(module=module or "all", lang=lang.value)
    cached = await cache_get(cache_key)
    if cached is not None:
        return [LessonBrief(**l) for l in cached]

    stmt = (
        select(Lesson)
        .where(Lesson.review_status == LessonReviewStatus.published.value)
        .order_by(Lesson.module, Lesson.lesson_order)
    )
    if module:
        stmt = stmt.where(Lesson.module == module)

    result = await db.execute(stmt)
    lessons = list(result.scalars().all())

    out = [
        LessonBrief(
            id=l.id,
            slug=l.slug,
            module=l.module,
            title=_lang_field(l, "title", lang.value) or l.title_en,
            summary=_lang_field(l, "summary", lang.value),
            lesson_order=l.lesson_order,
            estimated_minutes=l.estimated_minutes,
            xp_reward=l.xp_reward,
            surah_ref=l.surah_ref,
            ayah_range=l.ayah_range,
            tags=l.tags,
        )
        for l in lessons
    ]
    await cache_set(cache_key, [l.model_dump() for l in out], ttl=RedisKeys.TTL_LESSON)
    return out


@router.get("/{lesson_id}", response_model=LessonDetail)
async def get_lesson(
    lesson_id: int,
    lang: AppLanguage = Query(AppLanguage.en),
    db: AsyncSession = Depends(get_db),
):
    """Get full lesson payload with quiz questions (cached, published only)."""
    cache_key = RedisKeys.LESSON_CACHE.format(lesson_id=lesson_id, lang=lang.value)
    cached = await cache_get(cache_key)
    if cached is not None:
        return LessonDetail(**cached)

    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.quiz_questions))
        .where(
            and_(
                Lesson.id == lesson_id,
                Lesson.review_status == LessonReviewStatus.published.value,
            )
        )
    )
    lesson = result.scalar_one_or_none()
    if lesson is None:
        raise NotFoundError("Lesson", lesson_id)

    out = LessonDetail(
        id=lesson.id,
        slug=lesson.slug,
        module=lesson.module,
        title=_lang_field(lesson, "title", lang.value) or lesson.title_en,
        summary=_lang_field(lesson, "summary", lang.value),
        content=_lang_field(lesson, "content", lang.value) or lesson.content_en,
        lesson_order=lesson.lesson_order,
        estimated_minutes=lesson.estimated_minutes,
        xp_reward=lesson.xp_reward,
        surah_ref=lesson.surah_ref,
        ayah_range=lesson.ayah_range,
        tags=lesson.tags,
        quiz_questions=[
            QuizQuestionOut(
                id=q.id,
                question=_lang_field(q, "question", lang.value) or q.question_en,
                question_type=q.question_type,
                options=_lang_field(q, "options", lang.value) or q.options_en,
                explanation=_lang_field(q, "explanation", lang.value),
                points=q.points,
                order_index=q.order_index,
            )
            for q in sorted(lesson.quiz_questions, key=lambda x: x.order_index)
        ],
    )
    await cache_set(cache_key, out.model_dump(), ttl=RedisKeys.TTL_LESSON)
    return out
