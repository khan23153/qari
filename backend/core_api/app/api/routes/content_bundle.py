"""Content bundle route: offline bundle manifest."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.exceptions import ProblemException
from app.services.content_bundle_service import generate_bundle_manifest
from app.services.redis_service import cache_get, cache_set
from shared import AppLanguage, RedisKeys

router = APIRouter(prefix="/v1/content", tags=["content-bundle"])


@router.get("/bundle")
async def get_content_bundle(
    scope: str = Query(..., description="Bundle scope: juz30, juz1, juz15, last_2_surahs, all"),
    lang: AppLanguage = Query(AppLanguage.en),
    db: AsyncSession = Depends(get_db),
):
    """Get an offline content bundle manifest for the given scope."""
    cache_key = RedisKeys.CONTENT_BUNDLE_CACHE.format(scope=scope, lang=lang.value)
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        manifest = await generate_bundle_manifest(db, scope, lang)
    except ValueError as exc:
        raise ProblemException(
            status=400,
            title="Bad Request",
            detail=str(exc),
        )

    await cache_set(cache_key, manifest, ttl=RedisKeys.TTL_BUNDLE)
    return manifest
