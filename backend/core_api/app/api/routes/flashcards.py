"""Flashcard SRS endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.models.user import User, Flashcard, FlashcardReview
from app.models.corpus import Word
from app.schemas.user import FlashcardSchema, FlashcardReviewRequest, FlashcardReviewResponse
from app.services.srs_service import sm2_update
from app.services.flashcard_service import get_due_flashcards
from app.services.redis_service import cache_delete

router = APIRouter()


@router.get("/flashcards/due", response_model=list[FlashcardSchema])
async def list_due_flashcards(
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get due flashcards with embedded word data."""
    cards = await get_due_flashcards(db, user.user_id, limit)
    result = []
    for card in cards:
        word_result = await db.execute(
            select(Word).where(
                Word.surah_number == card.surah_number,
                Word.ayah_number == card.ayah_number,
                Word.word_position == card.word_position,
            )
        )
        word = word_result.scalar_one_or_none()
        result.append(FlashcardSchema(
            card_id=card.card_id,
            surah_number=card.surah_number,
            ayah_number=card.ayah_number,
            word_position=card.word_position,
            text_uthmani=word.text_uthmani if word else "",
            transliteration=word.transliteration if word else "",
            translation=word.translation if word else {},
            audio_url=word.audio_url if word else None,
        ))
    return result


@router.post("/flashcards/{card_id}/review", response_model=FlashcardReviewResponse)
async def review_flashcard(
    card_id: UUID,
    req: FlashcardReviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a flashcard review grade. Runs SM-2 update server-side."""
    result = await db.execute(
        select(Flashcard).where(
            Flashcard.card_id == card_id,
            Flashcard.user_id == user.user_id,
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Flashcard not found")

    new_ef, new_interval, new_reps, next_due = sm2_update(
        card.ease_factor, card.interval_days, card.repetitions, req.grade
    )

    card.ease_factor = new_ef
    card.interval_days = new_interval
    card.repetitions = new_reps
    card.due_at = next_due

    # Log review
    db.add(FlashcardReview(card_id=card_id, grade=req.grade))

    await db.commit()
    await cache_delete(f"home:{user.user_id}")

    return FlashcardReviewResponse(
        next_due=next_due,
        ease_factor=new_ef,
        interval_days=new_interval,
        repetitions=new_reps,
    )
