"""Flashcard routes: due cards, review with SM-2."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError, ProblemException
from app.core.logging import get_logger
from app.models.corpus import Word, Root
from app.models.user import Flashcard, FlashcardReview, User, UserStats
from app.schemas.user import DueFlashcardOut, FlashcardReviewRequest, FlashcardReviewResponse
from app.services.redis_service import cache_delete
from app.services.srs_service import calculate_sm2
from shared import DEFAULT_FLASHCARD_LIMIT, RedisKeys

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/flashcards", tags=["flashcards"])


@router.get("/due", response_model=list[DueFlashcardOut])
async def get_due_flashcards(
    limit: int = Query(DEFAULT_FLASHCARD_LIMIT, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get due flashcards with embedded word data."""
    now = datetime.now(timezone.utc)
    lang = user.app_language

    result = await db.execute(
        select(Flashcard)
        .options(
            selectinload(Flashcard.word).selectinload(Word.root),
        )
        .where(
            and_(
                Flashcard.user_id == user.id,
                Flashcard.is_suspended == False,
                Flashcard.due_at <= now,
            )
        )
        .order_by(Flashcard.due_at.asc())
        .limit(limit)
    )

    cards = []
    for card in result.scalars().all():
        word = card.word
        root_text = word.root.root_arabic if word and word.root else None
        cards.append(DueFlashcardOut(
            id=card.id,
            word_id=card.word_id,
            surah_number=card.surah_number,
            ayah_number=card.ayah_number,
            word_position=card.word_position,
            text_arabic=word.text_arabic if word else "",
            text_transliteration=word.text_transliteration if word else None,
            translation=getattr(word, f"translation_{lang}", None) if word else None,
            pos_group=word.pos_group if word else None,
            root_text=root_text,
            audio_url=word.audio_url if word else None,
            due_at=card.due_at,
            sm2_repetitions=card.sm2_repetitions,
        ))
    return cards


@router.post("/{card_id}/review", response_model=FlashcardReviewResponse)
async def review_flashcard(
    card_id: int,
    body: FlashcardReviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Review a flashcard with a grade (0-5). Applies SM-2 update."""
    result = await db.execute(
        select(Flashcard)
        .where(
            and_(Flashcard.id == card_id, Flashcard.user_id == user.id)
        )
    )
    card = result.scalar_one_or_none()
    if card is None:
        raise NotFoundError("Flashcard", card_id)

    # --- Run SM-2 ---
    sm2_result = calculate_sm2(
        grade=body.grade,
        easiness=float(card.sm2_easiness),
        repetitions=card.sm2_repetitions,
        interval=card.sm2_interval,
    )

    # --- Record review audit trail ---
    review = FlashcardReview(
        flashcard_id=card.id,
        user_id=user.id,
        grade=body.grade,
        prev_easiness=float(card.sm2_easiness),
        new_easiness=sm2_result.new_easiness,
        prev_interval=card.sm2_interval,
        new_interval=sm2_result.new_interval,
    )
    db.add(review)

    # --- Update card ---
    prev_easiness = float(card.sm2_easiness)
    prev_interval = card.sm2_interval

    card.sm2_easiness = sm2_result.new_easiness
    card.sm2_interval = sm2_result.new_interval
    card.sm2_repetitions = sm2_result.new_repetitions
    card.due_at = sm2_result.next_due_at
    card.last_reviewed_at = datetime.now(timezone.utc)
    card.is_suspended = sm2_result.is_suspended

    # --- Update stats ---
    stats_result = await db.execute(
        select(UserStats).where(UserStats.user_id == user.id)
    )
    stats = stats_result.scalar_one_or_none()
    if stats is None:
        stats = UserStats(user_id=user.id)
        db.add(stats)
        await db.flush()
    stats.flashcards_reviewed += 1

    await db.commit()
    await db.refresh(card)

    # --- Invalidate home cache ---
    await cache_delete(RedisKeys.HOME_CACHE.format(user_id=str(user.id)))

    return FlashcardReviewResponse(
        flashcard_id=card.id,
        new_easiness=sm2_result.new_easiness,
        new_interval=sm2_result.new_interval,
        new_repetitions=sm2_result.new_repetitions,
        next_due_at=sm2_result.next_due_at,
        is_suspended=sm2_result.is_suspended,
    )
