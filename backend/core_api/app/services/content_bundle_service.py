"""Content bundle service: offline bundle manifest generation.

Generates a manifest of all content needed for offline access within a
given scope (e.g. juz30, a specific surah range, or a lesson module).
"""

from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.corpus import Ayah, Word, Surah
from app.models.content import Lesson, QuizQuestion
from shared import AppLanguage

logger = get_logger(__name__)


# Supported bundle scopes
VALID_SCOPES = {"juz30", "juz1", "juz15", "last_2_surahs", "all"}

# Scope → (surah range, ayah range filter)
SCOPE_FILTERS = {
    "juz30": lambda q: q.where(Ayah.juz == 30),
    "juz1": lambda q: q.where(Ayah.juz == 1),
    "juz15": lambda q: q.where(Ayah.juz == 15),
    "last_2_surahs": lambda q: q.where(Ayah.surah_number.in_([113, 114])),
    "all": lambda q: q,
}


async def generate_bundle_manifest(
    db: AsyncSession,
    scope: str,
    lang: AppLanguage = AppLanguage.en,
) -> dict:
    """Generate an offline content bundle manifest for the given scope.

    The manifest includes:
    - List of surahs with metadata
    - List of ayahs with text and audio URLs
    - List of words with translations
    - List of published lessons referencing the scope
    - Total download size estimate

    Parameters
    ----------
    scope : str
        One of 'juz30', 'juz1', 'juz15', 'last_2_surahs', 'all'.
    lang : AppLanguage
        Language for translations.
    """
    if scope not in VALID_SCOPES:
        raise ValueError(f"Invalid scope '{scope}'. Valid scopes: {VALID_SCOPES}")

    lang_suffix = lang.value

    # --- Ayahs ---
    ayah_query = select(Ayah).order_by(Ayah.surah_number, Ayah.ayah_number)
    ayah_query = SCOPE_FILTERS[scope](ayah_query)
    ayah_result = await db.execute(ayah_query)
    ayahs = list(ayah_result.scalars().all())

    # --- Surahs in scope ---
    surah_numbers = sorted({a.surah_number for a in ayahs})
    surah_result = await db.execute(
        select(Surah).where(Surah.surah_number.in_(surah_numbers)).order_by(Surah.surah_number)
    )
    surahs = list(surah_result.scalars().all())

    # --- Words for ayahs in scope ---
    ayah_ids = [a.id for a in ayahs]
    words: list[Word] = []
    if ayah_ids:
        # Fetch in batches to avoid huge IN clauses
        batch_size = 500
        for i in range(0, len(ayah_ids), batch_size):
            batch = ayah_ids[i:i + batch_size]
            w_result = await db.execute(
                select(Word)
                .where(Word.ayah_id.in_(batch))
                .order_by(Word.surah_number, Word.ayah_number, Word.word_position)
            )
            words.extend(w_result.scalars().all())

    # --- Lessons referencing surahs in scope ---
    surah_ref_strs = [str(s) for s in surah_numbers]
    lesson_result = await db.execute(
        select(Lesson)
        .where(
            and_(
                Lesson.review_status == "published",
                Lesson.surah_ref.in_(surah_ref_strs + [f"{s}" for s in surah_numbers]),
            )
        )
        .order_by(Lesson.module, Lesson.lesson_order)
    )
    lessons = list(lesson_result.scalars().all())

    # --- Build manifest ---
    def _lang_field(obj, field_base: str) -> Optional[str]:
        """Get the language-specific field from an ORM object."""
        attr = f"{field_base}_{lang_suffix}"
        return getattr(obj, attr, None)

    manifest = {
        "scope": scope,
        "lang": lang_suffix,
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "surahs": [
            {
                "surah_number": s.surah_number,
                "name_arabic": s.name_arabic,
                "name_transliteration": s.name_transliteration,
                "name_translation": _lang_field(s, "name_translation"),
                "revelation_place": s.revelation_place,
                "ayah_count": s.ayah_count,
            }
            for s in surahs
        ],
        "ayahs": [
            {
                "surah_number": a.surah_number,
                "ayah_number": a.ayah_number,
                "text_arabic": a.text_arabic,
                "text_translation": _lang_field(a, "text_translation"),
                "text_transliteration": a.text_transliteration,
                "juz": a.juz,
                "page": a.page,
                "sajda": a.sajda,
                "audio_url": a.audio_url,
            }
            for a in ayahs
        ],
        "words": [
            {
                "surah_number": w.surah_number,
                "ayah_number": w.ayah_number,
                "word_position": w.word_position,
                "text_arabic": w.text_arabic,
                "text_transliteration": w.text_transliteration,
                "translation": _lang_field(w, "translation"),
                "pos_group": w.pos_group,
                "audio_url": w.audio_url,
            }
            for w in words
        ],
        "lessons": [
            {
                "id": l.id,
                "slug": l.slug,
                "module": l.module,
                "title": _lang_field(l, "title"),
                "summary": _lang_field(l, "summary"),
                "xp_reward": l.xp_reward,
                "estimated_minutes": l.estimated_minutes,
            }
            for l in lessons
        ],
        "counts": {
            "surahs": len(surahs),
            "ayahs": len(ayahs),
            "words": len(words),
            "lessons": len(lessons),
        },
        "estimated_size_mb": round(
            len(ayahs) * 0.002 + len(words) * 0.001 + len(lessons) * 0.05, 2
        ),
    }

    logger.info(
        "bundle.generated",
        scope=scope,
        lang=lang_suffix,
        ayahs=len(ayahs),
        words=len(words),
        lessons=len(lessons),
    )
    return manifest
