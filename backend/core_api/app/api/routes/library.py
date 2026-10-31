"""Islamic Library routes: collections, hadith with scholar grades, isnad, rijal, gharib."""

from functools import lru_cache
from pathlib import Path as FsPath
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Path, Query

from app.core.config import settings
from app.library.remote import DiskJsonCache, RemoteHadithSource, httpx_fetcher
from app.library.service import LibraryService
from app.schemas.library import (
    BookPage,
    Category,
    CategoryOut,
    CollectionDetail,
    CollectionPage,
    ForwardCheckIn,
    ForwardCheckOut,
    GharibOut,
    HadithDetail,
    HadithPage,
    NarratorOut,
    SearchOut,
)

router = APIRouter(prefix="/v1/library", tags=["library"])

HADITH_ID = r"^[a-z0-9-]+:\d+$"


@lru_cache(maxsize=1)
def get_library_service() -> LibraryService:
    """Process-wide service; tests replace it via dependency_overrides."""
    remote = None
    if settings.library_remote_enabled:
        base_url = LibraryService.from_bundled_data().remote_base_url()
        if base_url:
            remote = RemoteHadithSource(
                fetch_json=httpx_fetcher(settings.library_remote_timeout_sec),
                cache=DiskJsonCache(settings.library_cache_dir, max_bytes=settings.library_cache_max_mb * 1024 * 1024),
                base_url=base_url,
            )
    return LibraryService.from_bundled_data(
        remote=remote,
        forward_cache=FsPath(settings.library_cache_dir) / "forward-index.pickle",
    )


def _page(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> tuple[int, int]:
    return page, page_size


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(service: LibraryService = Depends(get_library_service)):
    """The five library shelves with how many collections each holds."""
    return service.categories()


@router.get("/collections", response_model=CollectionPage)
async def list_collections(
    category: Optional[Category] = Query(None),
    paging: tuple[int, int] = Depends(_page),
    service: LibraryService = Depends(get_library_service),
):
    return service.list_collections(category, *paging)


@router.get("/collections/{slug}", response_model=CollectionDetail)
async def get_collection(slug: str, service: LibraryService = Depends(get_library_service)):
    return service.get_collection(slug)


@router.get("/collections/{slug}/books", response_model=BookPage)
async def list_books(
    slug: str,
    paging: tuple[int, int] = Depends(_page),
    service: LibraryService = Depends(get_library_service),
):
    return service.list_books(slug, *paging)


@router.get("/collections/{slug}/books/{book}/hadiths", response_model=HadithPage)
async def list_book_hadiths(
    slug: str,
    book: int = Path(..., ge=1),
    paging: tuple[int, int] = Depends(_page),
    service: LibraryService = Depends(get_library_service),
):
    """Hadith of one book; fetched on demand and cached when not in the seed."""
    return await service.list_book_hadiths(slug, book, *paging)


@router.get("/hadiths", response_model=HadithPage)
async def list_hadiths(
    graded: Literal["all", "weak", "fabricated"] = Query("all"),
    paging: tuple[int, int] = Depends(_page),
    service: LibraryService = Depends(get_library_service),
):
    """Indexed hadith. `weak`: at least one named scholar graded it da'if or
    mawdu'; `fabricated`: at least one graded it mawdu'."""
    return service.list_hadiths(graded, *paging)


@router.get("/hadiths/{hadith_id}", response_model=HadithDetail)
async def get_hadith(
    hadith_id: str = Path(..., pattern=HADITH_ID, examples=["bukhari:1"]),
    service: LibraryService = Depends(get_library_service),
):
    return await service.get_hadith(hadith_id)


@router.get("/narrators/{narrator_id}", response_model=NarratorOut)
async def get_narrator(narrator_id: str, service: LibraryService = Depends(get_library_service)):
    return service.get_narrator(narrator_id)


@router.get("/gharib/{word}", response_model=GharibOut)
async def lookup_gharib(word: str, service: LibraryService = Depends(get_library_service)):
    """Classical meaning of a difficult hadith word; tashkeel and clitics are ignored."""
    return service.lookup_gharib(word)


@router.get("/search", response_model=SearchOut)
async def search(
    q: str = Query(..., min_length=2, max_length=100),
    service: LibraryService = Depends(get_library_service),
):
    return service.search(q)


@router.post("/check", response_model=ForwardCheckOut)
async def check_forward(body: ForwardCheckIn, service: LibraryService = Depends(get_library_service)):
    """Find a forwarded "hadith" in the collections and show who graded it.

    Safha never grades: a match shows the scholars' grades, and no match is
    reported as not found in these collections, not as fabricated. The first
    call after a restart may answer 503 while the collections are prepared.
    """
    return await service.check_forward(body.text)
