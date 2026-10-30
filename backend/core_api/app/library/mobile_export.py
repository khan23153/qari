"""Export the bundled library in API response shape for the mobile app.

The app serves this snapshot whenever `/v1/library` is unreachable or not yet
deployed, so every record is validated through the same response schemas the
API uses.
"""

from app.library.arabic import normalize_arabic
from app.library.service import LibraryService
from app.schemas.library import (
    BookOut,
    CategoryOut,
    CollectionBrief,
    HadithDetail,
    HadithSummary,
    NarratorOut,
)

MOBILE_SEED_VERSION = 1
_ALL = 1_000_000


def _dump(model, data: dict) -> dict:
    return model.model_validate(data).model_dump(mode="json")


async def build_mobile_seed(service: LibraryService) -> dict:
    collections = []
    for c in service.list_collections(None, 1, _ALL)["items"]:
        brief = _dump(CollectionBrief, c)
        brief["books"] = [_dump(BookOut, b) for b in service.list_books(c["slug"], 1, _ALL)["items"]]
        collections.append(brief)

    hadiths = {}
    for hadith_id in service.seed_hadith_ids():
        hadiths[hadith_id] = _dump(HadithDetail, await service.get_hadith(hadith_id))

    gharib = []
    for g in service.gharib_entries():
        gharib.append({
            "id": g["id"],
            "word_ar": g["word_ar"],
            "forms": sorted({normalize_arabic(f) for f in g["forms"]}),
            "root_ar": g["root_ar"],
            "transliteration": g["transliteration"],
            "gloss_en": g["gloss_en"],
            "definition_ar": g.get("definition_ar"),
            "source_book": g["source_book"],
            "review_status": g["review_status"],
        })

    return {
        "version": MOBILE_SEED_VERSION,
        "categories": [_dump(CategoryOut, c) for c in service.categories()],
        "collections": collections,
        "hadiths": hadiths,
        "hadith_summaries": [_dump(HadithSummary, s) for s in service.list_hadiths("all", 1, _ALL)["items"]],
        "narrators": {nid: _dump(NarratorOut, service.get_narrator(nid)) for nid in service.narrator_ids()},
        "gharib": gharib,
    }
