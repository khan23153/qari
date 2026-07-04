"""Recitation session retrieval (results stored by recitation-api)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.models.user import User, RecitationSession, RecitationWordResult
from app.schemas.user import RecitationResultResponse, RecitationResultWord

router = APIRouter()


@router.get("/recitations/{session_id}", response_model=RecitationResultResponse)
async def get_recitation_result(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full word-verdict report for a recitation session (history screen)."""
    result = await db.execute(
        select(RecitationSession).where(
            RecitationSession.session_id == session_id,
            RecitationSession.user_id == user.user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Recitation session not found")

    words_result = await db.execute(
        select(RecitationWordResult)
        .where(RecitationWordResult.session_id == session_id)
        .order_by(
            RecitationWordResult.ayah_number,
            RecitationWordResult.word_position,
        )
    )
    words = []
    for wr in words_result.scalars().all():
        words.append(RecitationResultWord(
            key=f"{wr.surah_number}:{wr.ayah_number}:{wr.word_position}",
            verdict=wr.verdict,
            error_detail=wr.error_detail,
            user_clip={
                "start_ms": wr.start_ms,
                "end_ms": wr.end_ms,
            } if wr.start_ms is not None else None,
        ))

    return RecitationResultResponse(
        session_id=session.session_id,
        overall_score=session.overall_score,
        fluency_score=session.fluency_score,
        tajweed_score=session.tajweed_score,
        words=words,
        model_version=session.model_version,
    )
