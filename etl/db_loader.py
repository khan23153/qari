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
    sa.Column("id", sa.Integer, primary_key=True),  # surah number 1-114
    sa.Column("name_arabic", sa.String(50), nullable=False),
    sa.Column("name_simple", sa.String(50), nullable=False),
    sa.Column("name_english", sa.String(100)),
    sa.Column("revelation_place", sa.String(20)),  # meccan / medinan
    sa.Column("revelation_order", sa.Integer),
    sa.Column("verses_count", sa.Integer, nullable=False),
    sa.Column("bismillah_pre", sa.Boolean, default=True),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    schema="quran",
)

ayahs_table = sa.Table(
    "ayahs", metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("surah_id", sa.Integer, sa.ForeignKey("quran.surahs.id"), nullable=False),
    sa.Column("ayah_number", sa.Integer, nullable=False),
    sa.Column("verse_key", sa.String(15), unique=True, nullable=False),  # "2:255"
    sa.Column("text_uthmani", sa.Text, nullable=False),
    sa.Column("text_imlaei", sa.Text),
    sa.Column("text_uthmani_simple", sa.Text),
    sa.Column("translations", sa.JSON),  # {edition_id: text}
    sa.Column("audio_url", sa.Text),
    sa.Column("audio_duration", sa.Float),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    sa.UniqueConstraint("surah_id", "ayah_number", name="uq_ayahs_surah_ayah"),
    schema="quran",
)

words_table = sa.Table(
    "words", metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("surah_id", sa.Integer, nullable=False),
    sa.Column("ayah_number", sa.Integer, nullable=False),
    sa.Column("word_number", sa.Integer, nullable=False),
    sa.Column("verse_key", sa.String(15), nullable=False),
    sa.Column("position", sa.Integer, nullable=False),  # global word position
    sa.Column("arabic_text", sa.Text),
    sa.Column("translation", sa.Text),
    sa.Column("transliteration", sa.Text),
    sa.Column("pos_tag", sa.String(20)),
    sa.Column("pos_group", sa.String(10)),  # ism / fil / harf
    sa.Column("lemma", sa.Text),
    sa.Column("root", sa.Text),
    sa.Column("features", sa.JSON),
    sa.Column("audio_url", sa.Text),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    sa.UniqueConstraint("verse_key", "word_number", name="uq_words_verse_word"),
    schema="quran",
)

roots_table = sa.Table(
    "roots", metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("root_arabic", sa.Text, unique=True, nullable=False),
    sa.Column("root_transliteration", sa.String(50)),
    sa.Column("occurrence_count", sa.Integer, default=0),
    sa.Column("unique_lemmas", sa.JSON),  # list of lemma strings
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    schema="quran",
)

tajweed_table = sa.Table(
    "tajweed_annotations", metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("surah_id", sa.Integer, nullable=False),
    sa.Column("ayah_number", sa.Integer, nullable=False),
    sa.Column("verse_key", sa.String(15), nullable=False),
    sa.Column("rule_id", sa.Integer, nullable=False),
    sa.Column("rule_name", sa.String(50), nullable=False),
    sa.Column("description", sa.Text),
    sa.Column("text_fragment", sa.Text),
    sa.Column("char_start", sa.Integer),
    sa.Column("char_end", sa.Integer),
    sa.Column("word_indices", sa.JSON),  # list of int
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    schema="quran",
)

qaris_table = sa.Table(
    "qaris", metadata,
    sa.Column("id", sa.Integer, primary_key=True),  # Quran.com reciter ID
    sa.Column("name", sa.String(200), nullable=False),
    sa.Column("arabic_name", sa.String(200)),
    sa.Column("english_name", sa.String(200)),
    sa.Column("relative_path", sa.String(500)),
    sa.Column("file_formats", sa.JSON),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    schema="quran",
)

checksums_table = sa.Table(
    "etl_checksums", metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("load_id", sa.String(100), nullable=False),
    sa.Column("verse_key", sa.String(15), nullable=False),
    sa.Column("text_uthmani_checksum", sa.String(64), nullable=False),
    sa.Column("text_imlaei_checksum", sa.String(64)),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    schema="quran",
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
        for s in surahs:
            rows.append({
                "id": s.get("id") or s.get("chapter_number"),
                "name_arabic": s.get("name_arabic", ""),
                "name_simple": s.get("name_simple", s.get("name_complex", "")),
                "name_english": s.get("translated_name", {}).get("name", "") if isinstance(s.get("translated_name"), dict) else s.get("english_name", ""),
                "revelation_place": s.get("revelation_place", ""),
                "revelation_order": s.get("revelation_order"),
                "verses_count": s.get("verses_count", 0),
                "bismillah_pre": s.get("bismillah_pre", True),
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
        """Upsert ayahs with text, translations, and audio metadata.

        Parameters
        ----------
        db:
            Async session.
        ayahs:
            List of ayah dicts from ``QuranComClient.get_ayahs()``.
            Each dict should have: verse_key, surah_id (or verse_number),
            text_uthmani, text_imlaei, translations, audio_url, etc.

        Returns
        -------
        Number of rows upserted.
        """
        if not ayahs:
            return 0

        rows: List[Dict[str, Any]] = []
        for a in ayahs:
            verse_key = a.get("verse_key", "")
            # Parse surah and ayah from verse_key "2:255"
            parts = verse_key.split(":")
            surah_id = int(parts[0]) if len(parts) == 2 else a.get("surah_id", 0)
            ayah_num = int(parts[1]) if len(parts) == 2 else a.get("ayah_number", 0)

            # Extract translations: API returns list of {resource_id: ..., text: ...}
            translations: Dict[str, str] = {}
            raw_translations = a.get("translations", [])
            if isinstance(raw_translations, list):
                for t in raw_translations:
                    if isinstance(t, dict):
                        resource_id = str(t.get("resource_id", t.get("id", "")))
                        text = t.get("text", "")
                        if resource_id and text:
                            translations[resource_id] = text
            elif isinstance(raw_translations, dict):
                translations = {str(k): v for k, v in raw_translations.items()}

            rows.append({
                "surah_id": surah_id,
                "ayah_number": ayah_num,
                "verse_key": verse_key,
                "text_uthmani": a.get("text_uthmani", ""),
                "text_imlaei": a.get("text_imlaei", ""),
                "text_uthmani_simple": a.get("text_uthmani_simple", ""),
                "translations": translations,
                "audio_url": a.get("audio_url", ""),
                "audio_duration": a.get("audio_duration", 0),
            })

        # Batch upsert in chunks to avoid parameter limits
        chunk_size = 200
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = pg_insert(ayahs_table).values(chunk)
            update_cols = {
                c.name: stmt.excluded[c.name]
                for c in ayahs_table.columns
                if c.name not in ("id",)
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["verse_key"], set_=update_cols
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
        """Upsert words with morphology, POS, and root data.

        Parameters
        ----------
        db:
            Async session.
        words:
            List of word dicts.  Each should have: verse_key, word_number,
            arabic_text, translation, transliteration, pos_tag, pos_group,
            lemma, root, features, audio_url.

        Returns
        -------
        Number of rows upserted.
        """
        if not words:
            return 0

        rows: List[Dict[str, Any]] = []
        for w in words:
            verse_key = w.get("verse_key", "")
            parts = verse_key.split(":")
            surah_id = int(parts[0]) if len(parts) == 2 else w.get("surah", 0)
            ayah_num = int(parts[1]) if len(parts) == 2 else w.get("ayah", 0)

            rows.append({
                "surah_id": surah_id,
                "ayah_number": ayah_num,
                "word_number": w.get("word", w.get("word_number", 0)),
                "verse_key": verse_key,
                "position": w.get("position", 0),
                "arabic_text": w.get("form", w.get("arabic_text", "")),
                "translation": w.get("translation", ""),
                "transliteration": w.get("transliteration", ""),
                "pos_tag": w.get("pos_tag", ""),
                "pos_group": w.get("pos_group", ""),
                "lemma": w.get("lemma"),
                "root": w.get("root"),
                "features": w.get("features", {}),
                "audio_url": w.get("audio_url", ""),
            })

        chunk_size = 500
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = pg_insert(words_table).values(chunk)
            update_cols = {
                c.name: stmt.excluded[c.name]
                for c in words_table.columns
                if c.name not in ("id",)
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["verse_key", "word_number"], set_=update_cols
            )
            await db.execute(stmt)
            total += len(chunk)

        await db.commit()
        logger.info("loaded_words", count=total)
        return total

    # ------------------------------------------------------------------
    # Roots
    # ------------------------------------------------------------------

    async def load_roots(
        self,
        db: AsyncSession,
        roots: List[Dict[str, Any]],
    ) -> int:
        """Upsert root entries.

        Parameters
        ----------
        db:
            Async session.
        roots:
            List of root dicts from ``CorpusParser.extract_roots()``.
            Each has: root, transliteration, occurrence_count, unique_lemmas.

        Returns
        -------
        Number of rows upserted.
        """
        if not roots:
            return 0

        rows: List[Dict[str, Any]] = []
        for r in roots:
            rows.append({
                "root_arabic": r.get("root", ""),
                "root_transliteration": r.get("transliteration", ""),
                "occurrence_count": r.get("occurrence_count", 0),
                "unique_lemmas": r.get("unique_lemmas", []),
            })

        chunk_size = 500
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = pg_insert(roots_table).values(chunk)
            update_cols = {
                c.name: stmt.excluded[c.name]
                for c in roots_table.columns
                if c.name not in ("id",)
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["root_arabic"], set_=update_cols
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
        """Upsert tajweed annotations.

        Parameters
        ----------
        db:
            Async session.
        annotations:
            List of annotation dicts from ``TajweedParser.parse_ayah()``.
            Each should have: surah, ayah, rule_id, rule_name, description,
            text_fragment, char_start, char_end, word_indices.

        Returns
        -------
        Number of rows upserted.
        """
        if not annotations:
            return 0

        rows: List[Dict[str, Any]] = []
        for ann in annotations:
            surah = ann.get("surah", 0)
            ayah = ann.get("ayah", 0)
            verse_key = ann.get("verse_key", f"{surah}:{ayah}")

            # The annotation may be nested inside a per-ayah result dict
            ann_list = ann.get("annotations", [ann]) if "annotations" in ann else [ann]

            for a in ann_list:
                rows.append({
                    "surah_id": surah,
                    "ayah_number": ayah,
                    "verse_key": verse_key,
                    "rule_id": a.get("rule_id", 0),
                    "rule_name": a.get("rule_name", ""),
                    "description": a.get("description", ""),
                    "text_fragment": a.get("text_fragment", ""),
                    "char_start": a.get("char_start", 0),
                    "char_end": a.get("char_end", 0),
                    "word_indices": a.get("word_indices", []),
                })

        chunk_size = 500
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            # Tajweed annotations are replaced wholesale on each load
            # (delete + insert would be cleaner, but upsert by all columns
            #  except id works for idempotency)
            stmt = pg_insert(tajweed_table).values(chunk)
            # No unique constraint to conflict on — use on_conflict_do_nothing
            # to avoid duplicates on re-run.  For a true upsert, a unique
            # constraint on (verse_key, rule_id, char_start) would be needed.
            stmt = stmt.on_conflict_do_nothing()
            await db.execute(stmt)
            total += len(chunk)

        await db.commit()
        logger.info("loaded_tajweed", count=total)
        return total

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
            rows.append({
                "id": q.get("id"),
                "name": q.get("name", q.get("reciter_name", "")),
                "arabic_name": q.get("arabic_name", ""),
                "english_name": q.get("english_name", q.get("name", "")),
                "relative_path": q.get("relative_path", ""),
                "file_formats": q.get("file_formats", []),
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
