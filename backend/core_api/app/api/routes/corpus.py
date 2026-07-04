"""Quran corpus content endpoints (public, cached)."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.deps import get_db
from app.models.corpus import Surah, Ayah, Word, Root, TajweedAnnotation
from app.schemas.corpus import SurahSummary, SurahDetail, AyahSchema, WordDetailSchema, RootSchema
from app.services.redis_service import cache_get, cache_set

router = APIRouter()


@router.get("/surahs", response_model=list[SurahSummary])
async def list_surahs(
    lang: str = Query("en", pattern="^(en|ur|hi_latn)$"),
    db: AsyncSession = Depends(get_db),
):
    """List all 114 surahs with names and metadata."""
    cache_key = f"surahs:list:{lang}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(Surah).order_by(Surah.surah_number))
    surahs = result.scalars().all()
    data = [
        SurahSummary(
            surah_number=s.surah_number,
            name_arabic=s.name_arabic,
            name_translit=s.name_translit,
            name_translated=s.name_translated,
            revelation_place=s.revelation_place,
            ayah_count=s.ayah_count,
            has_context_story=s.context_story is not None,
        )
        for s in surahs
    ]
    await cache_set(cache_key, [d.model_dump() for d in data], ttl=86400)
    return data


@router.get("/surahs/{surah_number}", response_model=SurahDetail)
async def get_surah(
    surah_number: int,
    lang: str = Query("en", pattern="^(en|ur|hi_latn)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get surah metadata + context story."""
    if not 1 <= surah_number <= 114:
        raise HTTPException(status_code=400, detail="Invalid surah number")

    cache_key = f"surahs:{surah_number}:{lang}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(Surah).where(Surah.surah_number == surah_number)
    )
    surah = result.scalar_one_or_none()
    if not surah:
        raise HTTPException(status_code=404, detail="Surah not found")

    data = SurahDetail(
        surah_number=surah.surah_number,
        name_arabic=surah.name_arabic,
        name_translit=surah.name_translit,
        name_translated=surah.name_translated,
        revelation_place=surah.revelation_place,
        ayah_count=surah.ayah_count,
        has_context_story=surah.context_story is not None,
        context_story=surah.context_story,
    )
    await cache_set(cache_key, data.model_dump(), ttl=86400)
    return data


@router.get("/surahs/{surah_number}/ayahs", response_model=list[AyahSchema])
async def get_ayahs(
    surah_number: int,
    from_: int = Query(1, alias="from", ge=1),
    to: Optional[int] = Query(None, ge=1),
    lang: str = Query("en", pattern="^(en|ur|hi_latn)$"),
    qari: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get ayahs with embedded word array for the Quran Reader."""
    if not 1 <= surah_number <= 114:
        raise HTTPException(status_code=400, detail="Invalid surah number")

    # Page ≤ 20 ayahs
    if to is None:
        to = min(from_ + 19, 286)
    if to - from_ + 1 > 20:
        raise HTTPException(status_code=400, detail="Max 20 ayahs per request")

    cache_key = f"ayahs:{surah_number}:{from_}:{to}:{lang}:{qari or 'default'}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    # Fetch ayahs
    ayah_result = await db.execute(
        select(Ayah)
        .where(
            Ayah.surah_number == surah_number,
            Ayah.ayah_number >= from_,
            Ayah.ayah_number <= to,
        )
        .order_by(Ayah.ayah_number)
    )
    ayahs = ayah_result.scalars().all()
    if not ayahs:
        raise HTTPException(status_code=404, detail="No ayahs found in range")

    # Fetch words for these ayahs
    word_result = await db.execute(
        select(Word)
        .where(
            Word.surah_number == surah_number,
            Word.ayah_number >= from_,
            Word.ayah_number <= to,
        )
        .order_by(Word.ayah_number, Word.word_position)
    )
    words = word_result.scalars().all()

    # Fetch tajweed annotations
    tajweed_result = await db.execute(
        select(TajweedAnnotation)
        .where(
            TajweedAnnotation.surah_number == surah_number,
            TajweedAnnotation.ayah_number >= from_,
            TajweedAnnotation.ayah_number <= to,
        )
    )
    tajweed_by_word = {}
    for t in tajweed_result.scalars().all():
        key = (t.ayah_number, t.word_position)
        tajweed_by_word.setdefault(key, []).append({
            "char_start": t.char_start,
            "char_end": t.char_end,
            "rule": t.rule,
        })

    # Group words by ayah
    words_by_ayah = {}
    for w in words:
        words_by_ayah.setdefault(w.ayah_number, []).append(w)

    data = []
    for ayah in ayahs:
        ayah_words = []
        for w in words_by_ayah.get(ayah.ayah_number, []):
            ayah_words.append(
                WordSchema(
                    word_position=w.word_position,
                    text_uthmani=w.text_uthmani,
                    transliteration=w.transliteration,
                    translation=w.translation,
                    pos_tag=w.pos_tag,
                    pos_group=w.pos_group,
                    audio_url=w.audio_url,
                    tajweed_spans=tajweed_by_word.get(
                        (w.ayah_number, w.word_position), []
                    ),
                )
            )
        data.append(AyahSchema(
            surah_number=ayah.surah_number,
            ayah_number=ayah.ayah_number,
            text_uthmani=ayah.text_uthmani,
            text_imlaei=ayah.text_imlaei,
            page_number=ayah.page_number,
            juz_number=ayah.juz_number,
            words=ayah_words,
        ))

    await cache_set(cache_key, [d.model_dump() for d in data], ttl=86400)
    return data


@router.get("/words/{surah_number}:{ayah_number}:{word_position}", response_model=WordDetailSchema)
async def get_word_detail(
    surah_number: int,
    ayah_number: int,
    word_position: int,
    lang: str = Query("en", pattern="^(en|ur|hi_latn)$"),
    db: AsyncSession = Depends(get_db),
):
    """Full word detail: morphology, root, other occurrences."""
    cache_key = f"word:{surah_number}:{ayah_number}:{word_position}:{lang}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(Word).where(
            Word.surah_number == surah_number,
            Word.ayah_number == ayah_number,
            Word.word_position == word_position,
        )
    )
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    root_data = None
    if word.root_id:
        root_result = await db.execute(
            select(Root).where(Root.root_id == word.root_id)
        )
        root_data = root_result.scalar_one_or_none()

    # Top 5 other occurrences
    other_occurrences = []
    if word.root_id:
        occ_result = await db.execute(
            select(Word)
            .where(Word.root_id == word.root_id)
            .limit(5)
        )
        for occ in occ_result.scalars().all():
            other_occurrences.append({
                "surah": occ.surah_number,
                "ayah": occ.ayah_number,
                "word_position": occ.word_position,
                "text": occ.text_uthmani,
            })

    data = WordDetailSchema(
        surah_number=word.surah_number,
        ayah_number=word.ayah_number,
        word_position=word.word_position,
        text_uthmani=word.text_uthmani,
        transliteration=word.transliteration,
        translation=word.translation,
        pos_tag=word.pos_tag,
        pos_group=word.pos_group,
        morphology=word.morphology if isinstance(word.morphology, list) else [word.morphology],
        lemma=word.lemma,
        root_id=word.root_id,
        root_arabic=root_data.root_arabic if root_data else None,
        root_translit=root_data.root_translit if root_data else None,
        root_core_meaning=root_data.core_meaning if root_data else None,
        occurrence_count=root_data.occurrence_count if root_data else None,
        other_occurrences=other_occurrences,
    )
    await cache_set(cache_key, data.model_dump(), ttl=86400)
    return data


@router.get("/roots/{root_id}", response_model=RootSchema)
async def get_root(
    root_id: int,
    lang: str = Query("en", pattern="^(en|ur|hi_latn)$"),
    db: AsyncSession = Depends(get_db),
):
    """Root meaning + occurrence list — powers Root Pattern screen."""
    cache_key = f"root:{root_id}:{lang}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(Root).where(Root.root_id == root_id))
    root = result.scalar_one_or_none()
    if not root:
        raise HTTPException(status_code=404, detail="Root not found")

    occ_result = await db.execute(
        select(Word)
        .where(Word.root_id == root_id)
        .order_by(Word.surah_number, Word.ayah_number)
        .limit(50)
    )
    occurrences = [
        {
            "surah": w.surah_number,
            "ayah": w.ayah_number,
            "word_position": w.word_position,
            "text": w.text_uthmani,
            "translation": w.translation,
        }
        for w in occ_result.scalars().all()
    ]

    data = RootSchema(
        root_id=root.root_id,
        root_arabic=root.root_arabic,
        root_translit=root.root_translit,
        core_meaning=root.core_meaning,
        occurrence_count=root.occurrence_count,
        occurrences=occurrences,
    )
    await cache_set(cache_key, data.model_dump(), ttl=86400)
    return data


from app.schemas.corpus import WordSchema
