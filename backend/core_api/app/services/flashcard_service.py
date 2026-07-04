"""Flashcard auto-creation and due-card retrieval."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.user import Flashcard
from app.models.corpus import Word

DAILY_CAP = 20


async def auto_create_flashcard(
    db: AsyncSession,
    user_id: str,
    surah_number: int,
    ayah_number: int,
    word_position: int,
    source: str,
) -> Flashcard | None:
    """Upsert a flashcard for a missed word. Caps at DAILY_CAP new cards/day."""
    # Check if card already exists
    existing = await db.execute(
        select(Flashcard).where(
            and_(
                Flashcard.user_id == user_id,
                Flashcard.surah_number == surah_number,
                Flashcard.ayah_number == ayah_number,
                Flashcard.word_position == word_position,
            )
        )
    )
    card = existing.scalar_one_or_none()
    if card:
        # Reset due date for existing card
        card.due_at = datetime.now(timezone.utc)
        await db.flush()
        return card

    # Check daily cap
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count_result = await db.execute(
        select(func.count(Flashcard.card_id)).where(
            and_(
                Flashcard.user_id == user_id,
                Flashcard.due_at >= today_start,
                Flashcard.repetitions == 0,
            )
        )
    )
    today_count = count_result.scalar()
    if today_count and today_count >= DAILY_CAP:
        return None

    card = Flashcard(
        card_id=uuid4(),
        user_id=user_id,
        surah_number=surah_number,
        ayah_number=ayah_number,
        word_position=word_position,
        source=source,
        due_at=datetime.now(timezone.utc),
    )
    db.add(card)
    await db.flush()
    return card


async def get_due_flashcards(
    db: AsyncSession,
    user_id: str,
    limit: int = 20,
) -> list[Flashcard]:
    """Get due flashcards with embedded word data."""
    result = await db.execute(
        select(Flashcard)
        .where(
            and_(
                Flashcard.user_id == user_id,
                Flashcard.due_at <= datetime.now(timezone.utc),
                Flashcard.suspended == False,
            )
        )
        .order_by(Flashcard.due_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())
