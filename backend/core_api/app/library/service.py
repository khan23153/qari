"""Library read model over the bundled catalog/seed plus the on-demand remote source."""

from __future__ import annotations

import asyncio
import json
import logging
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.core.exceptions import NotFoundError, ProblemException
from app.library.arabic import normalize_arabic, strip_clitics
from app.library.forward_check import ForwardIndex, detect_language, editions_for
from app.library.grading import DEFECT_CAUSES, dataset_grade, inclusion_grade
from app.library.remote import RemoteFetchError, RemoteHadithSource

DATA_DIR = Path(__file__).resolve().parent / "data"
SEARCH_LIMIT = 20

# How long a forward check waits for the first-time index build before
# answering "preparing" (the build keeps running in the background).
FORWARD_WAIT_SEC = 8.0

log = logging.getLogger(__name__)


class LibraryUnavailableError(ProblemException):
    def __init__(self, detail: str):
        super().__init__(status=503, title="Service Unavailable", detail=detail)


def page_of(items: list, page: int, page_size: int) -> dict:
    start = (page - 1) * page_size
    return {
        "items": items[start:start + page_size],
        "total": len(items),
        "page": page,
        "page_size": page_size,
        "has_next": start + page_size < len(items),
    }


@lru_cache(maxsize=1)
def _bundled() -> tuple[dict, dict]:
    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    seed = json.loads((DATA_DIR / "seed.json").read_text(encoding="utf-8"))
    return catalog, seed


class LibraryService:
    def __init__(
        self,
        catalog: dict,
        seed: dict,
        remote: Optional[RemoteHadithSource] = None,
        forward_cache: Optional[Path] = None,
        forward_wait_sec: float = FORWARD_WAIT_SEC,
    ):
        self._categories = catalog["categories"]
        self._collections = {c["slug"]: c for c in catalog["collections"]}
        self._source = catalog["source"]
        self._hadiths = {h["id"]: h for h in seed["hadiths"]}
        self._narrators = {n["id"]: n for n in seed["narrators"]}
        self._gharib = seed["gharib"]
        self._gharib_by_form = {
            normalize_arabic(form): g for g in self._gharib for form in g["forms"]
        }
        self._remote = remote
        self._forward_cache = forward_cache
        self._forward_wait = forward_wait_sec
        self._forward: Optional[ForwardIndex] = None
        self._forward_task: Optional[asyncio.Task] = None

    @classmethod
    def from_bundled_data(
        cls,
        remote: Optional[RemoteHadithSource] = None,
        forward_cache: Optional[Path] = None,
        forward_wait_sec: float = FORWARD_WAIT_SEC,
    ) -> "LibraryService":
        catalog, seed = _bundled()
        return cls(catalog, seed, remote, forward_cache, forward_wait_sec)

    def remote_base_url(self) -> Optional[str]:
        return self._source.get("base_url")

    def seed_hadith_ids(self) -> list[str]:
        return list(self._hadiths)

    def narrator_ids(self) -> list[str]:
        return list(self._narrators)

    def gharib_entries(self) -> list[dict]:
        return list(self._gharib)

    # --- catalog ----------------------------------------------------------

    def categories(self) -> list[dict]:
        return [
            {**c, "collection_count": sum(1 for x in self._collections.values() if x["category"] == c["slug"])}
            for c in self._categories
        ]

    def _collection(self, slug: str) -> dict:
        try:
            return self._collections[slug]
        except KeyError:
            raise NotFoundError("Collection", slug) from None

    @staticmethod
    def _brief(c: dict) -> dict:
        return {**c, "book_count": len(c.get("books", []))}

    def list_collections(self, category: Optional[str], page: int, page_size: int) -> dict:
        items = [self._brief(c) for c in self._collections.values() if category in (None, c["category"])]
        return page_of(items, page, page_size)

    def get_collection(self, slug: str) -> dict:
        return self._brief(self._collection(slug))

    def list_books(self, slug: str, page: int, page_size: int) -> dict:
        return page_of(self._collection(slug).get("books", []), page, page_size)

    # --- hadith -----------------------------------------------------------

    def _grades(self, collection: str, dataset_grades: list[dict]) -> list[dict]:
        grades = []
        included = inclusion_grade(collection)
        if included:
            grades.append(included)
        grades.extend(dataset_grade(g["scholar"], g["grade"], g.get("source_dataset")) for g in dataset_grades)
        return grades

    def _summary(self, h: dict) -> dict:
        return {
            "id": h["id"],
            "collection": h["collection"],
            "number": h["number"],
            "book_number": h["book"]["number"],
            "matn_ar": h.get("matn_ar") or h["text_ar"],
            "translation_text": (h.get("translation") or {}).get("text"),
            "grades": self._grades(h["collection"], h.get("dataset_grades", [])),
        }

    def _reliability(self, node: dict) -> str:
        role = node.get("role", "narrator")
        if role in ("prophet", "compiler"):
            return role
        narrator = self._narrators.get(node.get("narrator_id") or "")
        return narrator["reliability"] if narrator else "unknown"

    def _detail(self, h: dict) -> dict:
        c = self._collections[h["collection"]]
        chain = [
            {
                "position": i,
                "name_ar": node["name_ar"],
                "narrator_id": node.get("narrator_id"),
                "role": node.get("role", "narrator"),
                "term_ar": node.get("term_ar"),
                "identification": node["identification"],
                "candidates": node.get("candidates", []),
                "reliability": self._reliability(node),
            }
            for i, node in enumerate(h.get("chain", []))
        ]
        defects = []
        for d in h.get("defects", []):
            label_en, label_ar = DEFECT_CAUSES[d["cause"]]
            narrator = self._narrators.get(d.get("narrator_id") or "")
            defects.append({
                **d,
                "cause_label_en": label_en,
                "cause_label_ar": label_ar,
                "narrator_name_ar": narrator["name_ar"] if narrator else None,
                "quote_verified": bool(d.get("quote_verified", False)),
            })
        return {
            "id": h["id"],
            "collection": {"slug": c["slug"], "name_en": c["name_en"], "name_ar": c["name_ar"]},
            "number": h["number"],
            "arabic_number": h.get("arabic_number"),
            "book": h["book"],
            "text_ar": h["text_ar"],
            "isnad_ar": h.get("isnad_ar"),
            "matn_ar": h.get("matn_ar"),
            "compiler_note_ar": h.get("compiler_note_ar"),
            "translation": h.get("translation"),
            "grades": self._grades(h["collection"], h.get("dataset_grades", [])),
            "defects": defects,
            "chain": chain,
            "gharib_words": h.get("gharib_words", []),
            "source": h["source"],
            "review_status": h["review_status"],
        }

    def _remote_config(self, c: dict) -> Optional[dict]:
        if self._remote is None or c.get("availability") != "remote":
            return None
        return c.get("remote")

    def _from_dataset(self, c: dict, ara_record: dict, ara_meta: dict, eng_record: Optional[dict]) -> dict:
        """Normalise one dataset record into the seed shape (no curated chain)."""
        cfg = c["remote"]
        book = ara_record["reference"]["book"]
        translation = None
        if eng_record is not None:
            translation = {
                "language": "en",
                "text": eng_record["text"],
                "source": f"{cfg['provider']} ({cfg['translation_edition']})",
                "license_status": "unverified",
            }
        grades_from = eng_record if eng_record is not None else ara_record
        return {
            "id": f"{c['slug']}:{ara_record['hadithnumber']}",
            "collection": c["slug"],
            "number": int(ara_record["hadithnumber"]),
            "arabic_number": ara_record.get("arabicnumber"),
            "book": {"number": book, "name_en": ara_meta.get("section", {}).get(str(book))},
            "text_ar": ara_record["text"],
            "translation": translation,
            "dataset_grades": [
                {"scholar": g["name"], "grade": g["grade"], "source_dataset": f"{cfg['provider']} ({cfg['translation_edition']})"}
                for g in grades_from.get("grades", [])
            ],
            "source": {
                "dataset": cfg["provider"],
                "editions": [cfg["arabic_edition"], cfg["translation_edition"]],
                "license": cfg["license"],
            },
            "review_status": "verified_from_source",
        }

    async def get_hadith(self, hadith_id: str) -> dict:
        return self._detail(await self._hadith_record(hadith_id))

    async def _hadith_record(self, hadith_id: str) -> dict:
        """The curated seed record, else the dataset record from the remote."""
        if hadith_id in self._hadiths:
            return self._hadiths[hadith_id]
        slug, number = hadith_id.split(":")
        c = self._collections.get(slug)
        cfg = self._remote_config(c) if c else None
        if cfg is None:
            raise NotFoundError("Hadith", hadith_id)
        try:
            ara, eng = await self._remote.hadith(cfg["arabic_edition"], cfg["translation_edition"], int(number))
        except RemoteFetchError:
            raise LibraryUnavailableError(f"Hadith '{hadith_id}' could not be fetched from the remote catalog") from None
        if not ara.get("hadiths"):
            raise NotFoundError("Hadith", hadith_id)
        eng_record = eng["hadiths"][0] if eng and eng.get("hadiths") else None
        return self._from_dataset(c, ara["hadiths"][0], ara["metadata"], eng_record)

    async def list_book_hadiths(self, slug: str, book: int, page: int, page_size: int) -> dict:
        c = self._collection(slug)
        if not any(b["number"] == book for b in c.get("books", [])):
            raise NotFoundError("Book", f"{slug}/{book}")
        seeded = {h["number"]: h for h in self._hadiths.values() if h["collection"] == slug and h["book"]["number"] == book}
        items: dict[int, dict] = {}
        cfg = self._remote_config(c)
        if cfg is not None:
            try:
                ara, eng = await self._remote.section(cfg["arabic_edition"], cfg["translation_edition"], book)
            except RemoteFetchError:
                raise LibraryUnavailableError(f"Book '{slug}/{book}' could not be fetched from the remote catalog") from None
            eng_by_number = {r["hadithnumber"]: r for r in (eng or {}).get("hadiths", [])}
            for record in ara.get("hadiths", []):
                n = int(record["hadithnumber"])
                items[n] = self._from_dataset(c, record, ara["metadata"], eng_by_number.get(record["hadithnumber"]))
        items.update(seeded)
        ordered = [self._summary(items[n]) for n in sorted(items)]
        return page_of(ordered, page, page_size)

    def list_hadiths(self, graded: str, page: int, page_size: int) -> dict:
        wanted = {"weak": {"daif", "mawdu"}, "fabricated": {"mawdu"}}.get(graded)
        items = []
        for h in self._hadiths.values():
            summary = self._summary(h)
            if wanted is None or any(g["ruling_type"] in wanted for g in summary["grades"]):
                items.append(summary)
        return page_of(items, page, page_size)

    # --- rijal / gharib / search -------------------------------------------

    def _narrator_brief(self, n: dict) -> dict:
        return {"id": n["id"], "name_ar": n["name_ar"], "name_en": n["name_en"], "reliability": n["reliability"]}

    def get_narrator(self, narrator_id: str) -> dict:
        n = self._narrators.get(narrator_id)
        if n is None:
            raise NotFoundError("Narrator", narrator_id)
        return {
            **n,
            "teachers": [self._narrator_brief(self._narrators[t]) for t in n.get("teachers", [])],
            "students": [self._narrator_brief(self._narrators[s]) for s in n.get("students", [])],
        }

    def lookup_gharib(self, word: str) -> dict:
        normalized = normalize_arabic(word)
        for token in normalized.split() or [normalized]:
            for stem in strip_clitics(token):
                entry = self._gharib_by_form.get(stem)
                if entry is not None:
                    return {**entry, "matched_form": stem}
        raise NotFoundError("Gharib entry", word)

    # --- forward check ----------------------------------------------------

    async def check_forward(self, text: str) -> dict:
        """Closest hadith to a forwarded text, with the grades scholars gave.

        A miss is "not found in these collections", never a ruling.
        """
        index = await self._forward_index()
        matches = []
        for m in index.search(text):
            try:
                record = await self._hadith_record(m.hadith_id)
            except (NotFoundError, LibraryUnavailableError):
                continue
            matches.append({
                "band": m.band,
                "score": m.score,
                "language": m.language,
                "hadith": self._summary(record),
            })
        searched = [self._collections[s]["name_en"] for s in index.collections if s in self._collections]
        if matches:
            note = (
                "Compare the wording before sharing. Grades are those given by the "
                "named scholars; Safha does not grade hadith."
            )
        else:
            note = (
                "Not found in the collections Safha searches. That does not prove "
                "it is fabricated, but do not share it as a hadith until a scholar "
                "confirms its source."
            )
        return {
            "query_language": detect_language(text),
            "matches": matches,
            "searched_collections": searched,
            "note": note,
        }

    async def _forward_index(self) -> ForwardIndex:
        if self._forward is not None:
            return self._forward
        if self._remote is None:
            raise LibraryUnavailableError("Checking forwards needs the hadith collections, which are not enabled")
        if self._forward_task is None:
            self._forward_task = asyncio.create_task(self._build_forward())
        task = self._forward_task
        try:
            self._forward = await asyncio.wait_for(asyncio.shield(task), timeout=self._forward_wait)
        except asyncio.TimeoutError:
            raise LibraryUnavailableError(
                "Safha is preparing the hadith collections for the first time. Try again in a minute."
            ) from None
        except Exception:
            self._forward_task = None  # try again on the next request
            raise LibraryUnavailableError("The hadith collections could not be fetched for checking") from None
        return self._forward

    async def _build_forward(self) -> ForwardIndex:
        path = self._forward_cache
        if path is not None and path.exists():
            try:
                return await asyncio.to_thread(lambda: pickle.loads(path.read_bytes()))
            except Exception:  # a stale or broken file is rebuilt
                log.warning("forward index at %s unreadable; rebuilding", path)
        index = ForwardIndex()
        for c in self._collections.values():
            cfg = self._remote_config(c)
            if cfg is None:
                continue
            for lang, edition_name in editions_for(cfg).items():
                try:
                    edition = await self._remote.edition(edition_name)
                except RemoteFetchError:
                    continue
                await asyncio.to_thread(index.add_edition, c["slug"], lang, edition)
                del edition  # editions are large; keep only the index
        if not index.collections:
            raise RemoteFetchError("no hadith edition could be fetched")
        if path is not None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                data = await asyncio.to_thread(pickle.dumps, index)
                path.write_bytes(data)
            except OSError:
                log.warning("could not save forward index to %s", path)
        return index

    def search(self, query: str) -> dict:
        q_ar = normalize_arabic(query)
        q_en = query.strip().lower()

        def hit(*fields: Optional[str]) -> bool:
            for f in fields:
                if f and (q_ar and q_ar in normalize_arabic(f) or q_en in f.lower()):
                    return True
            return False

        hadiths = [
            self._summary(h) for h in self._hadiths.values()
            if hit(h.get("matn_ar") or h["text_ar"], (h.get("translation") or {}).get("text"))
        ]
        narrators = [
            self._narrator_brief(n) for n in self._narrators.values() if hit(n["name_ar"], n["name_en"])
        ]
        collections = [
            self._brief(c) for c in self._collections.values()
            if hit(c["name_en"], c["name_ar"], c["author_en"], c["author_ar"])
        ]
        return {
            "query": query,
            "hadiths": hadiths[:SEARCH_LIMIT],
            "narrators": narrators[:SEARCH_LIMIT],
            "collections": collections[:SEARCH_LIMIT],
        }
