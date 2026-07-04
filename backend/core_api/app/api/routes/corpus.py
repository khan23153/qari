"""Corpus routes: surahs, ayahs, words, roots — all cached in Redis."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_optional_user
from app.core.exceptions import NotFoundError
from app.models.corpus import Ayah, Qari, Root, Surah, TajweedAnnotation, Word
from app.schemas.corpus import (
    AyahOut, QariBrief, RootDetail, RootBrief,
    SurahBrief, SurahDetail, TajweedAnnotationOut,
    WordBrief, WordDetail, WordOccurrence,
)
from app.services.redis_service import cache_get, cache_set
from shared import AppLanguage, MAX_AYAHS_PER_REQUEST, RedisKeys

router = APIRouter(prefix="/v1", tags=["corpus"])


def _lang_suffix(lang: AppLanguage) -> str:
    return lang.value


def _surah_name_translation(surah: Surah, lang: str) -> Optional[str]:
    return getattr(surah, f"name_translation_{lang}", None)


def _ayah_translation(ayah: Ayah, lang: str) -> Optional[str]:
    return getattr(ayah, f"text_translation_{lang}", None)


def _word_translation(word: Word, lang: str) -> Optional[str]:
    return getattr(word, f"translation_{lang}", None)


def _surah_context_story(surah: Surah, lang: str) -> Optional[str]:
    return getattr(surah, f"context_story_{lang}", None)


def _tajweed_description(taj: TajweedAnnotation, lang: str) -> Optional[str]:
    return getattr(taj, f"description_{lang}", None)


# ---------------------------------------------------------------------------
# Surahs
# ---------------------------------------------------------------------------

@router.get("/surahs", response_model=list[SurahBrief])
async def list_surahs(
    lang: AppLanguage = Query(AppLanguage.en),
    db: AsyncSession = Depends(get_db),
):
    """List all 114 surahs (cached)."""
    cache_key = f"qari:cache:surahs:{lang.value}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    result = await db.execute(select(Surah).order_by(Surah.surah_number))
    surahs = list(result.scalars().all())

    out = [
        SurahBrief(
            surah_number=s.surah_number,
            name_arabic=s.name_arabic,
            name_transliteration=s.name_transliteration,
            name_translation=_surah_name_translation(s, lang.value),
            revelation_place=s.revelation_place,
            revelation_order=s.revelation_order,
            ayah_count=s.ayah_count,
        )
        for s in surahs
    ]
    await cache_set(cache_key, [m.model_dump() for m in out], ttl=RedisKeys.TTL_AYAH)
    return out


@router.get("/surahs/{surah_number}", response_model=SurahDetail)
async def get_surah(
    surah_number: int,
    lang: AppLanguage = Query(AppLanguage.en),
    db: AsyncSession = Depends(get_db),
):
    """Get surah metadata with context story (cached)."""
    if not 1 <= surah_number <= 114:
        raise NotFoundError("Surah", surah_number)

    cache_key = RedisKeys.SURAH_CACHE.format(surah_id=surah_number) + f":{lang.value}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return SurahDetail(**cached)

    result = await db.execute(
        select(Surah).where(Surah.surah_number == surah_number)
    )
    surah = result.scalar_one_or_none()
    if surah is None:
        raise NotFoundError("Surah", surah_number)

    out = SurahDetail(
        surah_number=surah.surah_number,
        name_arabic=surah.name_arabic,
        name_transliteration=surah.name_transliteration,
        name_translation=_surah_name_translation(surah, lang.value),
        revelation_place=surah.revelation_place,
        revelation_order=surah.revelation_order,
        ayah_count=surah.ayah_count,
        page_start=surah.page_start,
        juz_list=surah.juz_list,
        context_story=_surah_context_story(surah, lang.value),
    )
    await cache_set(cache_key, out.model_dump(), ttl=RedisKeys.TTL_AYAH)
    return out


# ---------------------------------------------------------------------------
# Ayahs
# ---------------------------------------------------------------------------

@router.get("/surahs/{surah_number}/ayahs", response_model=list[AyahOut])
async def get_surah_ayahs(
    surah_number: int,
    from_: int = Query(1, alias="from", ge=1),
    to: Optional[int] = Query(None, ge=1),
    lang: AppLanguage = Query(AppLanguage.en),
    qari: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get ayahs for a surah with embedded word array (max 20 per request, cached)."""
    if not 1 <= surah_number <= 114:
        raise NotFoundError("Surah", surah_number)

    # Enforce max 20 ayahs per request
    if to is None:
        to = from_ + MAX_AYAHS_PER_REQUEST - 1
    else:
        if to - from_ + 1 > MAX_AYAHS_PER_REQUEST:
            to = from_ + MAX_AYAHS_PER_REQUEST - 1

    cache_key = RedisKeys.AYAH_RANGE_CACHE.format(
        surah=surah_number, from_=from_, to=to, lang=lang.value, qari=qari or "default"
    )
    cached = await cache_get(cache_key)
    if cached is not None:
        return [AyahOut(**a) for a in cached]

    result = await db.execute(
        select(Ayah)
        .options(selectinload(Ayah.words))
        .where(
            and_(
                Ayah.surah_number == surah_number,
                Ayah.ayah_number >= from_,
                Ayah.ayah_number <= to,
            )
        )
        .order_by(Ayah.ayah_number)
    )
    ayahs = list(result.scalars().all())

    out = [
        AyahOut(
            id=a.id,
            surah_number=a.surah_number,
            ayah_number=a.ayah_number,
            text_arabic=a.text_arabic,
            text_translation=_ayah_translation(a, lang.value),
            text_transliteration=a.text_transliteration,
            juz=a.juz,
            page=a.page,
            sajda=a.sajda,
            audio_url=a.audio_url,
            words=[
                WordBrief(
                    id=w.id,
                    word_position=w.word_position,
                    text_arabic=w.text_arabic,
                    text_transliteration=w.text_transliteration,
                    translation=_word_translation(w, lang.value),
                    pos_group=w.pos_group,
                    audio_url=w.audio_url,
                )
                for w in sorted(a.words, key=lambda x: x.word_position)
            ],
        )
        for a in ayahs
    ]
    await cache_set(cache_key, [a.model_dump() for a in out], ttl=RedisKeys.TTL_AYAH)
    return out


# ---------------------------------------------------------------------------
# Words
# ---------------------------------------------------------------------------

@router.get("/words/{surah}:{ayah}:{pos}", response_model=WordDetail)
async def get_word_detail(
    surah: int,
    ayah: int,
    pos: int,
    lang: AppLanguage = Query(AppLanguage.en),
    db: AsyncSession = Depends(get_db),
):
    """Get full word detail: morphology, root, tajweed, other occurrences (cached)."""
    cache_key = RedisKeys.WORD_CACHE.format(surah=surah, ayah=ayah, pos=pos, lang=lang.value)
    cached = await cache_get(cache_key)
    if cached is not None:
        return WordDetail(**cached)

    result = await db.execute(
        select(Word)
        .options(
            selectinload(Word.root),
            selectinload(Word.tajweed_annotations),
        )
        .where(
            and_(
                Word.surah_number == surah,
                Word.ayah_number == ayah,
                Word.word_position == pos,
            )
        )
    )
    word = result.scalar_one_or_none()
    if word is None:
        raise NotFoundError("Word", f"{surah}:{ayah}:{pos}")

    # Other occurrences of the same root
    other_occurrences: list[WordOccurrence] = []
    if word.root_id is not None:
        occ_result = await db.execute(
            select(Word)
            .where(and_(Word.root_id == word.root_id, Word.id != word.id))
            .order_by(Word.surah_number, Word.ayah_number, Word.word_position)
            .limit(50)
        )
        for w in occ_result.scalars().all():
            other_occurrences.append(
                WordOccurrence(
                    surah_number=w.surah_number,
                    ayah_number=w.ayah_number,
                    word_position=w.word_position,
                    text_arabic=w.text_arabic,
                )
            )

    root_brief = None
    if word.root is not None:
        root_brief = RootBrief(
            id=word.root.id,
            root_arabic=word.root.root_arabic,
            root_transliteration=word.root.root_transliteration,
            meaning=getattr(word.root, f"meaning_{lang.value}", None),
        )

    out = WordDetail(
        id=word.id,
        surah_number=word.surah_number,
        ayah_number=word.ayah_number,
        word_position=word.word_position,
        text_arabic=word.text_arabic,
        text_transliteration=word.text_transliteration,
        translation=_word_translation(word, lang.value),
        pos_group=word.pos_group,
        pos_detail=word.pos_detail,
        morphology_features=word.morphology_features,
        audio_url=word.audio_url,
        root=root_brief,
        tajweed_annotations=[
            TajweedAnnotationOut(
                id=t.id,
                rule_category=t.rule_category,
                rule_name=t.rule_name,
                rule_name_arabic=t.rule_name_arabic,
                description=_tajweed_description(t, lang.value),
                char_start=t.char_start,
                char_end=t.char_end,
            )
            for t in word.tajweed_annotations
        ],
        other_occurrences=other_occurrences,
    )
    await cache_set(cache_key, out.model_dump(), ttl=RedisKeys.TTL_WORD)
    return out


# ---------------------------------------------------------------------------
# Roots
# ---------------------------------------------------------------------------

@router.get("/roots/{root_id}", response_model=RootDetail)
async def get_root_detail(
    root_id: int,
    lang: AppLanguage = Query(AppLanguage.en),
    db: AsyncSession = Depends(get_db),
):
    """Get root meaning + occurrence list (cached)."""
    cache_key = RedisKeys.ROOT_CACHE.format(root_id=root_id, lang=lang.value)
    cached = await cache_get(cache_key)
    if cached is not None:
        return RootDetail(**cached)

    result = await db.execute(select(Root).where(Root.id == root_id))
    root = result.scalar_one_or_none()
    if root is None:
        raise NotFoundError("Root", root_id)

    # Occurrences
    occ_result = await db.execute(
        select(Word)
        .where(Word.root_id == root_id)
        .order_by(Word.surah_number, Word.ayah_number, Word.word_position)
        .limit(200)
    )
    occurrences = [
        WordOccurrence(
            surah_number=w.surah_number,
            ayah_number=w.ayah_number,
            word_position=w.word_position,
            text_arabic=w.text_arabic,
        )
        for w in occ_result.scalars().all()
    ]

    out = RootDetail(
        id=root.id,
        root_arabic=root.root_arabic,
        root_transliteration=root.root_transliteration,
        meaning=getattr(root, f"meaning_{lang.value}", None),
        occurrence_count=root.occurrence_count,
        occurrences=occurrences,
    )
    await cache_set(cache_key, out.model_dump(), ttl=RedisKeys.TTL_WORD)
    return out
