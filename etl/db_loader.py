"""
Async database loader for the Qari ETL pipeline.

Uses SQLAlchemy 2.0 async ORM with asyncpg to upsert data into Postgres.
All operations are idempotent (ON CONFLICT DO UPDATE) so the pipeline can
be re-run safely.

Tables (in the ``quran`` schema):

    quran.surahs
    quran.ayahs
    quran.words
    quran.roots
    quran.tajweed_annotations
    quran.qaris
    quran.etl_checksums  – stores per-load checksums for diff validation
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Table definitions (metadata-only, no ORM classes for speed)
# ---------------------------------------------------------------------------

metadata = sa.MetaData()

surahs_table = sa.Table(
    "surahs", metadata,
    sa.Column("id", sa.Integer, primary_key=True),  # equals surah number 1-114
    sa.Column("surah_number", sa.SmallInteger, nullable=False),
    sa.Column("name_arabic", sa.String(100), nullable=False),
    sa.Column("name_transliteration", sa.String(200), nullable=False),
    sa.Column("name_translation_en", sa.String(200), nullable=True),
    sa.Column("name_translation_ur", sa.String(200), nullable=True),
    sa.Column("name_translation_hi_latn", sa.String(200), nullable=True),
    sa.Column("revelation_place", sa.String(20), nullable=False),
    sa.Column("revelation_order", sa.SmallInteger, nullable=False),
    sa.Column("ayah_count", sa.SmallInteger, nullable=False),
    sa.Column("page_start", sa.SmallInteger, nullable=True),
    sa.Column("juz_list", sa.JSON, nullable=True),
    sa.Column("context_story_en", sa.Text, nullable=True),
    sa.Column("context_story_ur", sa.Text, nullable=True),
    sa.Column("context_story_hi_latn", sa.Text, nullable=True),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
              server_default=sa.func.now()),
    sa.UniqueConstraint("surah_number", name="uq_surahs_surah_number"),
    schema="public",
)

ayahs_table = sa.Table(
    "ayahs", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("surah_id", sa.Integer, sa.ForeignKey("public.surahs.id", ondelete="CASCADE"), nullable=False),
    sa.Column("surah_number", sa.SmallInteger, nullable=False),
    sa.Column("ayah_number", sa.SmallInteger, nullable=False),
    sa.Column("text_arabic", sa.Text, nullable=False),
    sa.Column("text_translation_en", sa.Text, nullable=True),
    sa.Column("text_translation_ur", sa.Text, nullable=True),
    sa.Column("text_translation_hi_latn", sa.Text, nullable=True),
    sa.Column("text_transliteration", sa.Text, nullable=True),
    sa.Column("juz", sa.SmallInteger, nullable=True),
    sa.Column("page", sa.SmallInteger, nullable=True),
    sa.Column("ruku", sa.SmallInteger, nullable=True),
    sa.Column("hizb_quarter", sa.SmallInteger, nullable=True),
    sa.Column("sajda", sa.Boolean, nullable=True),
    sa.Column("audio_url", sa.String(500), nullable=True),
    sa.Column("qari_id", sa.Integer, sa.ForeignKey("public.qaris.id", ondelete="SET NULL"), nullable=True),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("surah_number", "ayah_number", name="uq_ayahs_surah_ayah"),
    schema="public",
)

words_table = sa.Table(
    "words", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("ayah_id", sa.Integer, sa.ForeignKey("public.ayahs.id", ondelete="CASCADE"), nullable=False),
    sa.Column("surah_number", sa.SmallInteger, nullable=False),
    sa.Column("ayah_number", sa.SmallInteger, nullable=False),
    sa.Column("word_position", sa.SmallInteger, nullable=False),
    sa.Column("text_arabic", sa.String(200), nullable=False),
    sa.Column("text_transliteration", sa.String(200), nullable=True),
    sa.Column("translation_en", sa.String(500), nullable=True),
    sa.Column("translation_ur", sa.String(500), nullable=True),
    sa.Column("translation_hi_latn", sa.String(500), nullable=True),
    sa.Column("root_id", sa.Integer, sa.ForeignKey("public.roots.id", ondelete="SET NULL"), nullable=True),
    sa.Column("pos_group", sa.String(30), nullable=True),
    sa.Column("pos_detail", sa.String(100), nullable=True),
    sa.Column("morphology_features", sa.JSON, nullable=True),
    sa.Column("audio_url", sa.String(500), nullable=True),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("surah_number", "ayah_number", "word_position", name="uq_words_surah_ayah_pos"),
    schema="public",
)

roots_table = sa.Table(
    "roots", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("root_arabic", sa.Text, nullable=False),
    sa.Column("root_transliteration", sa.String(100), nullable=False),
    sa.Column("meaning_en", sa.Text, nullable=True),
    sa.Column("meaning_ur", sa.Text, nullable=True),
    sa.Column("meaning_hi_latn", sa.Text, nullable=True),
    sa.Column("occurrence_count", sa.Integer, nullable=False, server_default=sa.text("0")),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("root_arabic", name="uq_roots_root_arabic"),
    schema="public",
)

tajweed_table = sa.Table(
    "tajweed_annotations", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("word_id", sa.Integer, sa.ForeignKey("public.words.id", ondelete="CASCADE"), nullable=False),
    sa.Column("ayah_id", sa.Integer, sa.ForeignKey("public.ayahs.id", ondelete="CASCADE"), nullable=False),
    sa.Column("rule_category", sa.String(50), nullable=False),
    sa.Column("rule_name", sa.String(100), nullable=False),
    sa.Column("rule_name_arabic", sa.String(100), nullable=True),
    sa.Column("description_en", sa.Text, nullable=True),
    sa.Column("description_ur", sa.Text, nullable=True),
    sa.Column("description_hi_latn", sa.Text, nullable=True),
    sa.Column("char_start", sa.SmallInteger, nullable=True),
    sa.Column("char_end", sa.SmallInteger, nullable=True),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    schema="public",
)

qaris_table = sa.Table(
    "qaris", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("name", sa.String(200), nullable=False),
    sa.Column("arabic_name", sa.String(200), nullable=True),
    sa.Column("style", sa.String(50), nullable=True),
    sa.Column("audio_base_url", sa.String(500), nullable=True),
    sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("name", name="uq_qaris_name"),
    schema="public",
)

checksums_table = sa.Table(
    "etl_checksums", metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("load_id", sa.String(100), nullable=False),
    sa.Column("verse_key", sa.String(15), nullable=False),
    sa.Column("text_uthmani_checksum", sa.String(64), nullable=False),
    sa.Column("text_imlaei_checksum", sa.String(64)),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    schema="public",
)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

class DatabaseLoader:
    """Async database loader using SQLAlchemy + asyncpg.

    All methods perform upserts (INSERT ... ON CONFLICT DO UPDATE) so the
    pipeline is idempotent and safe to re-run.

    Parameters
    ----------
    database_url:
        SQLAlchemy async URL, e.g.
        ``postgresql+asyncpg://user:pass@host:5432/db``
    schema:
        Target Postgres schema (default ``quran``).
    """

    def __init__(self, database_url: str, schema: str = "quran") -> None:
        self.database_url = database_url
        self.schema = schema
        self._engine = create_async_engine(database_url, echo=False, pool_size=10)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    async def create_schema(self) -> None:
        """Create the target schema and all tables if they don't exist."""
        async with self._engine.begin() as conn:
            await conn.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {self.schema}"))
            await conn.run_sync(metadata.create_all)
        logger.info("schema_created", schema=self.schema)

    # ------------------------------------------------------------------
    # Surahs
    # ------------------------------------------------------------------

    async def load_surahs(
        self,
        db: AsyncSession,
        surahs: List[Dict[str, Any]],
    ) -> int:
        """Upsert surah metadata.

        Parameters
        ----------
        db:
            Async session.
        surahs:
            List of surah dicts from ``QuranComClient.get_surahs()``.

        Returns
        -------
        Number of rows upserted.
        """
        if not surahs:
            return 0

        rows: List[Dict[str, Any]] = []
        # quran.com returns the *city* of revelation (makkah/madinah);
        # core-api's check constraint expects the *type* (meccan/medinan).
        place_map = {
            "makkah": "meccan",
            "mecca": "meccan",
            "madinah": "medinan",
            "medina": "medinan",
        }
        for s in surahs:
            surah_num = s.get("id") or s.get("chapter_number")
            translated = s.get("translated_name") or {}
            if isinstance(translated, dict):
                name_en = translated.get("name", "")
            else:
                name_en = s.get("name_english", "")
            raw_place = (s.get("revelation_place") or "").lower()
            revelation_place = place_map.get(raw_place, "meccan")
            rows.append({
                "id": surah_num,
                "surah_number": surah_num,
                "name_arabic": s.get("name_arabic", ""),
                "name_transliteration": s.get("name_simple", s.get("name_complex", "")),
                "name_translation_en": name_en,
                "name_translation_ur": None,
                "name_translation_hi_latn": None,
                "revelation_place": revelation_place,
                "revelation_order": s.get("revelation_order"),
                "ayah_count": s.get("verses_count", 0),
                "page_start": None,
                "juz_list": None,
                "context_story_en": None,
                "context_story_ur": None,
                "context_story_hi_latn": None,
            })

        stmt = pg_insert(surahs_table).values(rows)
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in surahs_table.columns
            if c.name not in ("id",)
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"], set_=update_cols
        )
        result = await db.execute(stmt)
        await db.commit()
        logger.info("loaded_surahs", count=len(rows))
        return len(rows)

    # ------------------------------------------------------------------
    # Ayahs
    # ------------------------------------------------------------------

    async def load_ayahs(
        self,
        db: AsyncSession,
        ayahs: List[Dict[str, Any]],
    ) -> int:
        """Upsert ayahs (verses) with Arabic text, translations and metadata.

        Parameters
        ----------
        db:
            Async session.
        ayahs:
            List of ayah dicts from ``QuranComClient.get_ayahs()``.
            Each dict has: verse_key, verse_number, text_uthmani,
            text_imlaei, translations (list of {resource_id, text}),
            juz, page, ruku, hizbQuarter, sajda, audio, etc.
        """
        if not ayahs:
            return 0

        # Translation resource IDs → language column.
        EN_IDS = {131, 20, 149}
        UR_IDS = {85}

        def _to_int(v: Any) -> Optional[int]:
            try:
                return int(v)
            except (TypeError, ValueError):
                return None

        rows: List[Dict[str, Any]] = []
        for a in ayahs:
            verse_key = a.get("verse_key", "")
            parts = verse_key.split(":")
            surah_num = int(parts[0]) if len(parts) == 2 else a.get("surah_id", 0)
            ayah_num = int(parts[1]) if len(parts) == 2 else _to_int(a.get("verse_number")) or 0

            translations: Dict[str, str] = {}
            raw = a.get("translations", [])
            if isinstance(raw, list):
                for t in raw:
                    if isinstance(t, dict):
                        rid = t.get("resource_id", t.get("id"))
                        text = t.get("text", "")
                        if rid is not None and text:
                            translations[str(rid)] = text
            elif isinstance(raw, dict):
                translations = {str(k): v for k, v in raw.items() if v}

            en = next((translations[str(i)] for i in EN_IDS if str(i) in translations), None)
            ur = next((translations[str(i)] for i in UR_IDS if str(i) in translations), None)

            audio_url = None
            audio = a.get("audio")
            if isinstance(audio, dict):
                audio_url = audio.get("url")

            sajda = a.get("sajda")
            if not isinstance(sajda, bool):
                sajda = False

            rows.append({
                "surah_id": surah_num,
                "surah_number": surah_num,
                "ayah_number": ayah_num,
                "text_arabic": a.get("text_uthmani", "") or a.get("text_imlaei", ""),
                "text_translation_en": en,
                "text_translation_ur": ur,
                "text_translation_hi_latn": None,
                "text_transliteration": None,
                "juz": _to_int(a.get("juz")),
                "page": _to_int(a.get("page")),
                "ruku": _to_int(a.get("ruku")),
                "hizb_quarter": _to_int(a.get("hizbQuarter")),
                "sajda": sajda,
                "audio_url": audio_url,
                "qari_id": _to_int(a.get("qari_id")),
            })

        chunk_size = 200
        update_cols = [
            c.name for c in ayahs_table.columns
            if c.name not in ("id", "created_at")
        ]
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = pg_insert(ayahs_table).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["surah_number", "ayah_number"],
                set_={c: stmt.excluded[c] for c in update_cols},
            )
            await db.execute(stmt)
            total += len(chunk)

        await db.commit()
        logger.info("loaded_ayahs", count=total)
        return total

    # ------------------------------------------------------------------
    # Words
    # ------------------------------------------------------------------

    async def load_words(
        self,
        db: AsyncSession,
        words: List[Dict[str, Any]],
    ) -> int:
        """Upsert words with morphology, POS, and root linkage.

        Resolves ``ayah_id`` (FK → ayahs) and ``root_id`` (FK → roots)
        from the database before inserting.
        """
        if not words:
            return 0

        ayah_res = await db.execute(
            sa.text(f"SELECT id, surah_number, ayah_number FROM {self.schema}.ayahs")
        )
        ayah_map: Dict[tuple, int] = {}
        for row in ayah_res.fetchall():
            ayah_map[(row[1], row[2])] = row[0]

        root_res = await db.execute(
            sa.text(f"SELECT id, root_arabic FROM {self.schema}.roots")
        )
        root_map: Dict[str, int] = {}
        for row in root_res.fetchall():
            root_map[row[1]] = row[0]

        def _to_int(v: Any) -> int:
            try:
                return int(v)
            except (TypeError, ValueError):
                return 0

        rows: List[Dict[str, Any]] = []
        skipped = 0
        for w in words:
            verse_key = w.get("verse_key", "")
            parts = verse_key.split(":")
            surah_num = int(parts[0]) if len(parts) == 2 else w.get("surah", 0)
            ayah_num = int(parts[1]) if len(parts) == 2 else w.get("ayah", 0)

            ayah_id = ayah_map.get((surah_num, ayah_num))
            if ayah_id is None:
                skipped += 1
                continue

            loc = w.get("location")
            if isinstance(loc, dict):
                word_position = loc.get("word", loc.get("position"))
            else:
                word_position = None
            if word_position is None:
                word_position = w.get("word_number", w.get("position", 0))

            translation = w.get("translation")
            if isinstance(translation, dict):
                translation_en = translation.get("text")
            else:
                translation_en = translation

            transliteration = w.get("transliteration")
            if isinstance(transliteration, dict):
                transliteration = transliteration.get("text")

            root_id = None
            root = w.get("root")
            if root:
                root_id = root_map.get(root)

            features = w.get("features")
            if not isinstance(features, dict):
                features = None

            rows.append({
                "ayah_id": ayah_id,
                "surah_number": surah_num,
                "ayah_number": ayah_num,
                "word_position": _to_int(word_position),
                "text_arabic": w.get("text_uthmani") or w.get("text") or w.get("form") or "",
                "text_transliteration": transliteration,
                "translation_en": translation_en,
                "translation_ur": None,
                "translation_hi_latn": None,
                "root_id": root_id,
                "pos_group": w.get("pos_group"),
                "pos_detail": w.get("pos_tag"),
                "morphology_features": features,
                "audio_url": w.get("audio_url"),
            })

        chunk_size = 500
        update_cols = [
            c.name for c in words_table.columns
            if c.name not in ("id", "created_at")
        ]
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = pg_insert(words_table).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["surah_number", "ayah_number", "word_position"],
                set_={c: stmt.excluded[c] for c in update_cols},
            )
            await db.execute(stmt)
            total += len(chunk)

        await db.commit()
        logger.info("loaded_words", count=total, skipped_ayahs=skipped)
        return total

    # ------------------------------------------------------------------
    # Roots
    # ------------------------------------------------------------------

    async def load_roots(
        self,
        db: AsyncSession,
        roots: List[Dict[str, Any]],
    ) -> int:
        """Upsert root entries (Arabic root + transliteration + counts)."""
        if not roots:
            return 0

        rows: List[Dict[str, Any]] = []
        for r in roots:
            rows.append({
                "root_arabic": r.get("root", ""),
                "root_transliteration": r.get("transliteration", ""),
                "meaning_en": None,
                "meaning_ur": None,
                "meaning_hi_latn": None,
                "occurrence_count": r.get("occurrence_count", 0),
            })

        chunk_size = 500
        update_cols = [
            c.name for c in roots_table.columns
            if c.name not in ("id", "created_at")
        ]
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = pg_insert(roots_table).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["root_arabic"],
                set_={c: stmt.excluded[c] for c in update_cols},
            )
            await db.execute(stmt)
            total += len(chunk)

        await db.commit()
        logger.info("loaded_roots", count=total)
        return total

    # ------------------------------------------------------------------
    # Tajweed annotations
    # ------------------------------------------------------------------

    async def load_tajweed(
        self,
        db: AsyncSession,
        annotations: List[Dict[str, Any]],
    ) -> int:
        """Upsert tajweed annotations, resolving word_id and ayah_id FKs.

        Parameters
        ----------
        db:
            Async session.
        annotations:
            List of parsed-ayah dicts from ``TajweedParser.parse_ayah()``,
            each with keys: surah, ayah, annotations (list of rule dicts
            with rule_id, rule_name, description, char_start, char_end,
            word_indices).
        """
        if not annotations:
            return 0

        ayah_res = await db.execute(
            sa.text(f"SELECT id, surah_number, ayah_number FROM {self.schema}.ayahs")
        )
        ayah_map: Dict[tuple, int] = {}
        for row in ayah_res.fetchall():
            ayah_map[(row[1], row[2])] = row[0]

        word_res = await db.execute(
            sa.text(
                f"SELECT id, surah_number, ayah_number, word_position, text_arabic "
                f"FROM {self.schema}.words "
                f"ORDER BY surah_number, ayah_number, word_position"
            )
        )
        words_by_ayah: Dict[tuple, List[tuple]] = {}
        for row in word_res.fetchall():
            words_by_ayah.setdefault((row[1], row[2]), []).append(
                (row[3], row[0], row[4] or "")
            )

        rows: List[Dict[str, Any]] = []
        skipped = 0
        for parsed in annotations:
            surah = parsed.get("surah", 0)
            ayah = parsed.get("ayah", 0)
            ayah_id = ayah_map.get((surah, ayah))
            if ayah_id is None:
                skipped += 1
                continue
            ayah_words = words_by_ayah.get((surah, ayah), [])
            for ann in parsed.get("annotations", []):
                word_id = self._resolve_tajweed_word(ann, ayah_words)
                if word_id is None:
                    word_id = ayah_words[0][1] if ayah_words else None
                if word_id is None:
                    continue
                rule_name = ann.get("rule_name", "")
                rows.append({
                    "word_id": word_id,
                    "ayah_id": ayah_id,
                    "rule_category": ann.get("rule_category") or rule_name,
                    "rule_name": rule_name,
                    "rule_name_arabic": ann.get("rule_name_arabic"),
                    "description_en": ann.get("description_en")
                    or ann.get("description", ""),
                    "description_ur": ann.get("description_ur"),
                    "description_hi_latn": ann.get("description_hi_latn"),
                    "char_start": ann.get("char_start"),
                    "char_end": ann.get("char_end"),
                })

        # Idempotent reload: clear existing annotations before re-inserting.
        await db.execute(sa.text(f"DELETE FROM {self.schema}.tajweed_annotations"))

        chunk_size = 500
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = pg_insert(tajweed_table).values(chunk)
            await db.execute(stmt)
            total += len(chunk)

        await db.commit()
        logger.info("loaded_tajweed", count=total, skipped_ayahs=skipped)
        return total

    @staticmethod
    def _resolve_tajweed_word(
        ann: Dict[str, Any], ayah_words: List[tuple]
    ) -> Optional[int]:
        """Find the word id a tajweed annotation's char range falls in."""
        if not ayah_words:
            return None
        indices = ann.get("word_indices")
        if indices:
            idx = int(indices[0])
            if 0 <= idx < len(ayah_words):
                return ayah_words[idx][1]
        char_start = ann.get("char_start")
        if char_start is None:
            return None
        pos = 0
        for _wpos, wid, wtext in ayah_words:
            start = pos
            end = pos + len(wtext)
            if start <= char_start < end:
                return wid
            pos = end + 1
        return None

    # ------------------------------------------------------------------
    # Qaris
    # ------------------------------------------------------------------

    async def load_qaris(
        self,
        db: AsyncSession,
        qaris: List[Dict[str, Any]],
    ) -> int:
        """Upsert reciter (qari) metadata.

        Parameters
        ----------
        db:
            Async session.
        qaris:
            List of qari dicts from ``QuranComClient.get_qaris()``.

        Returns
        -------
        Number of rows upserted.
        """
        if not qaris:
            return 0

        rows: List[Dict[str, Any]] = []
        for q in qaris:
            qid = q.get("id")
            if qid is None:
                continue
            rows.append({
                "id": qid,
                "name": q.get("name", q.get("reciter_name", "")),
                "arabic_name": q.get("arabic_name", ""),
                "style": q.get("style"),
                "audio_base_url": q.get("audio_url") or q.get("relative_path", ""),
                "is_active": True,
            })

        stmt = pg_insert(qaris_table).values(rows)
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in qaris_table.columns
            if c.name not in ("id",)
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"], set_=update_cols
        )
        await db.execute(stmt)
        await db.commit()
        logger.info("loaded_qaris", count=len(rows))
        return len(rows)

    # ------------------------------------------------------------------
    # Checksums
    # ------------------------------------------------------------------

    async def load_checksums(
        self,
        db: AsyncSession,
        load_id: str,
        checksums: Dict[str, Dict[str, str]],
    ) -> int:
        """Store per-ayah text checksums for diff validation.

        Parameters
        ----------
        db:
            Async session.
        load_id:
            Unique identifier for this ETL run (e.g. timestamp-based).
        checksums:
            Dict mapping verse_key → {"uthmani": sha256, "imlaei": sha256}.

        Returns
        -------
        Number of rows inserted.
        """
        if not checksums:
            return 0

        rows: List[Dict[str, Any]] = []
        for verse_key, sums in checksums.items():
            rows.append({
                "load_id": load_id,
                "verse_key": verse_key,
                "text_uthmani_checksum": sums.get("uthmani", ""),
                "text_imlaei_checksum": sums.get("imlaei", ""),
            })

        chunk_size = 500
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = pg_insert(checksums_table).values(chunk)
            await db.execute(stmt)
            total += len(chunk)

        await db.commit()
        logger.info("loaded_checksums", count=total, load_id=load_id)
        return total

    # ------------------------------------------------------------------
    # Previous checksum retrieval (for diff)
    # ------------------------------------------------------------------

    async def get_previous_checksums(
        self,
        db: AsyncSession,
    ) -> Dict[str, Dict[str, str]]:
        """Retrieve the most recent load's checksums for diff comparison.

        Returns
        -------
        Dict mapping verse_key → {"uthmani": checksum, "imlaei": checksum}.
        """
        # Get the most recent load_id
        result = await db.execute(
            sa.text(f"""
                SELECT DISTINCT load_id
                FROM {self.schema}.etl_checksums
                ORDER BY load_id DESC
                LIMIT 1
            """)
        )
        row = result.fetchone()
        if not row:
            return {}

        prev_load_id = row[0]
        result = await db.execute(
            sa.text(f"""
                SELECT verse_key, text_uthmani_checksum, text_imlaei_checksum
                FROM {self.schema}.etl_checksums
                WHERE load_id = :load_id
            """),
            {"load_id": prev_load_id},
        )

        checksums: Dict[str, Dict[str, str]] = {}
        for row in result.fetchall():
            checksums[row[0]] = {
                "uthmani": row[1] or "",
                "imlaei": row[2] or "",
            }

        logger.info("retrieved_previous_checksums", load_id=prev_load_id, count=len(checksums))
        return checksums

    # ------------------------------------------------------------------
    # Session helper
    # ------------------------------------------------------------------

    def session(self) -> AsyncSession:
        """Return a new async session."""
        return self._session_factory()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Dispose of the engine connection pool."""
        await self._engine.dispose()
        logger.info("db_loader_closed")
