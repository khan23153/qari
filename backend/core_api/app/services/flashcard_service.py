"""Flashcard service: auto-creation with daily cap, due card retrieval."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.corpus import Word
from app.models.user import Flashcard, User
from app.services import redis_service
from shared import FLASHCARD_DAILY_CAP, SM2_INITIAL_EASINESS, SM2_INITIAL_INTERVAL

logger = get_logger(__name__)


async def get_due_flashcards(
    db: AsyncSession,
    user_id,
    limit: int = 20,
) -> list[Flashcard]:
    """Retrieve due flashcards for a user, ordered by due_at.

    Only non-suspended cards with due_at <= now are returned.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        select(Flashcard)
        .where(
            and_(
                Flashcard.user_id == user_id,
                Flashcard.is_suspended == False,
                Flashcard.due_at <= now,
            )
        )
        .order_by(Flashcard.due_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_due_flashcards(db: AsyncSession, user_id) -> int:
    """Count due flashcards for a user."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(func.count(Flashcard.id))
        .where(
            and_(
                Flashcard.user_id == user_id,
                Flashcard.is_suspended == False,
                Flashcard.due_at <= now,
            )
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def auto_create_flashcard(
    db: AsyncSession,
    user: User,
    word_id: int,
    source: str = "quiz_miss",
) -> Optional[Flashcard]:
    """Auto-create a flashcard for a word, respecting the daily cap.

    If a flashcard already exists for (user, word), it is returned as-is
    (no duplicate created). If the daily cap is reached, returns ``None``.

    Parameters
    ----------
    word_id : int
        The word to create a card for.
    source : str
        One of 'quiz_miss', 'recitation_miss', 'manual'.
    """
    # Check for existing card
    existing = await db.execute(
        select(Flashcard).where(
            and_(Flashcard.user_id == user.id, Flashcard.word_id == word_id)
        )
    )
    existing_card = existing.scalar_one_or_none()
    if existing_card is not None:
        return existing_card

    # Get word data
    word_result = await db.execute(select(Word).where(Word.id == word_id))
    word = word_result.scalar_one_or_none()
    if word is None:
        logger.warning("flashcard.word_not_found", word_id=word_id)
        return None

    # Check daily cap via Redis
    today_str = datetime.now(timezone.utc).date().isoformat()
    today_count = await redis_service.get_flashcard_daily_count(str(user.id), today_str)
    if today_count >= FLASHCARD_DAILY_CAP:
        logger.info(
            "flashcard.daily_cap_reached",
            user_id=str(user.id),
            count=today_count,
            cap=FLASHCARD_DAILY_CAP,
        )
        return None

    # Create the card
    card = Flashcard(
        user_id=user.id,
        word_id=word_id,
        surah_number=word.surah_number,
        ayah_number=word.ayah_number,
        word_position=word.word_position,
        source=source,
        sm2_easiness=SM2_INITIAL_EASINESS,
        sm2_interval=SM2_INITIAL_INTERVAL,
        sm2_repetitions=0,
        due_at=datetime.now(timezone.utc),
        is_suspended=False,
    )
    db.add(card)
    await db.flush()

    # Increment daily counter
    await redis_service.increment_flashcard_daily_count(str(user.id), today_str)

    logger.info(
        "flashcard.created",
        user_id=str(user.id),
        word_id=word_id,
        source=source,
        card_id=card.id,
    )
    return card


async def auto_create_from_quiz_miss(
    db: AsyncSession,
    user: User,
    word_ids: list[int],
) -> list[Flashcard]:
    """Auto-create flashcards for words missed in a quiz.

    Respects the daily cap — only creates cards up to the remaining quota.
    """
    created = []
    for wid in word_ids:
        card = await auto_create_flashcard(db, user, wid, source="quiz_miss")
        if card is not None:
            created.append(card)
        else:
            # Cap reached or error — stop trying
            break
    return created


async def auto_create_from_recitation_miss(
    db: AsyncSession,
    user: User,
    word_ids: list[int],
) -> list[Flashcard]:
    """Auto-create flashcards for words mispronounced in a recitation session."""
    created = []
    for wid in word_ids:
        card = await auto_create_flashcard(db, user, wid, source="recitation_miss")
        if card is not None:
            created.append(card)
        else:
            break
    return created
