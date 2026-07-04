"""Scholar Q&A routes: ask a scholar (multipart audio), list questions."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.exceptions import ProblemException
from app.core.logging import get_logger
from app.models.user import ScholarQuestion, User, UserStats
from app.schemas.user import ScholarQuestionOut
from app.services.redis_service import cache_delete
from shared import RedisKeys

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/scholar", tags=["scholar"])

# Max audio file size: 10 MB
MAX_AUDIO_SIZE = 10 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/webm", "audio/aac", "audio/m4a"}


@router.post("/questions", response_model=ScholarQuestionOut)
async def ask_scholar(
    question_text: Optional[str] = Form(None),
    surah_ref: Optional[str] = Form(None),
    ayah_ref: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a question to a scholar, optionally with audio attachment.

    Multipart form data:
    - question_text: optional text question
    - surah_ref: optional surah reference (e.g. "2:255")
    - ayah_ref: optional ayah reference
    - audio: optional audio file (max 10MB, WAV/MP3/OGG)
    """
    if question_text is None and audio is None:
        raise ProblemException(
            status=422,
            title="Validation Failed",
            detail="Either question_text or an audio file must be provided",
        )

    audio_url = None
    audio_duration = None

    if audio is not None:
        # Validate file size
        content = await audio.read()
        if len(content) > MAX_AUDIO_SIZE:
            raise ProblemException(
                status=413,
                title="Payload Too Large",
                detail=f"Audio file exceeds {MAX_AUDIO_SIZE // (1024 * 1024)}MB limit",
            )

        # Validate content type
        content_type = audio.content_type or ""
        if content_type not in ALLOWED_AUDIO_TYPES:
            raise ProblemException(
                status=415,
                title="Unsupported Media Type",
                detail=f"Audio type '{content_type}' not supported. Allowed: {ALLOWED_AUDIO_TYPES}",
            )

        # In production, upload to S3/GCS and get URL
        # For now, we store a placeholder path
        audio_url = f"scholar_audio/{user.id}/{__import__('uuid').uuid4()}.{content_type.split('/')[-1]}"
        # Duration would be computed by ffprobe in production
        logger.info("scholar.audio_uploaded", user_id=str(user.id), size=len(content), content_type=content_type)

    question = ScholarQuestion(
        user_id=user.id,
        question_text=question_text,
        audio_url=audio_url,
        audio_duration_sec=audio_duration,
        surah_ref=surah_ref,
        ayah_ref=ayah_ref,
        status="pending",
    )
    db.add(question)

    # Update stats
    stats_result = await db.execute(
        select(UserStats).where(UserStats.user_id == user.id)
    )
    stats = stats_result.scalar_one_or_none()
    if stats is None:
        stats = UserStats(user_id=user.id)
        db.add(stats)
        await db.flush()
    stats.questions_asked += 1

    await db.commit()
    await db.refresh(question)

    await cache_delete(RedisKeys.HOME_CACHE.format(user_id=str(user.id)))

    return ScholarQuestionOut(
        id=question.id,
        question_text=question.question_text,
        audio_url=question.audio_url,
        surah_ref=question.surah_ref,
        ayah_ref=question.ayah_ref,
        status=question.status,
        answer_text=question.answer_text,
        scholar_name=question.scholar_name,
        answered_at=question.answered_at,
        created_at=question.created_at,
    )


@router.get("/questions", response_model=list[ScholarQuestionOut])
async def list_scholar_questions(
    status: Optional[str] = Query(None, pattern="^(pending|answered|rejected)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's scholar questions, optionally filtered by status."""
    stmt = (
        select(ScholarQuestion)
        .where(ScholarQuestion.user_id == user.id)
        .order_by(ScholarQuestion.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        stmt = stmt.where(ScholarQuestion.status == status)

    result = await db.execute(stmt)
    questions = list(result.scalars().all())

    return [
        ScholarQuestionOut(
            id=q.id,
            question_text=q.question_text,
            audio_url=q.audio_url,
            surah_ref=q.surah_ref,
            ayah_ref=q.ayah_ref,
            status=q.status,
            answer_text=q.answer_text,
            scholar_name=q.scholar_name,
            answered_at=q.answered_at,
            created_at=q.created_at,
        )
        for q in questions
    ]
