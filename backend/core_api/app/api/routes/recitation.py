"""Recitation routes: get recitation session results (word-verdict report)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.user import RecitationSession, RecitationWordResult, User
from app.schemas.user import RecitationSessionOut, RecitationWordResultOut

router = APIRouter(prefix="/v1/recitations", tags=["recitation"])


@router.get("/{session_id}", response_model=RecitationSessionOut)
async def get_recitation_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a full word-verdict report for a recitation session."""
    result = await db.execute(
        select(RecitationSession)
        .options(selectinload(RecitationSession.word_results))
        .where(RecitationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise NotFoundError("RecitationSession", session_id)

    if session.user_id != user.id:
        raise ForbiddenError("You do not have access to this recitation session")

    # Build response with language-appropriate error details
    lang = user.app_language
    word_results = sorted(session.word_results, key=lambda r: (r.surah_number, r.ayah_number, r.word_position))

    return RecitationSessionOut(
        id=session.id,
        surah_number=session.surah_number,
        ayah_from=session.ayah_from,
        ayah_to=session.ayah_to,
        status=session.status,
        audio_duration_sec=float(session.audio_duration_sec) if session.audio_duration_sec else None,
        total_words=session.total_words,
        correct_words=session.correct_words,
        accuracy_pct=float(session.accuracy_pct) if session.accuracy_pct else None,
        error_message=session.error_message,
        queued_at=session.queued_at,
        completed_at=session.completed_at,
        word_results=[
            RecitationWordResultOut(
                id=wr.id,
                surah_number=wr.surah_number,
                ayah_number=wr.ayah_number,
                word_position=wr.word_position,
                expected_text=wr.expected_text,
                detected_text=wr.detected_text,
                verdict=wr.verdict,
                confidence=float(wr.confidence) if wr.confidence else None,
                error_detail=getattr(wr, f"error_detail_{lang}", None) or wr.error_detail_en,
                audio_start_sec=float(wr.audio_start_sec) if wr.audio_start_sec else None,
                audio_end_sec=float(wr.audio_end_sec) if wr.audio_end_sec else None,
            )
            for wr in word_results
        ],
    )
