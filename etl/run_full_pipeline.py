"""ETL pipeline runner — orchestrates full Quran corpus mirror sync.

Steps:
1. Fetch surahs from Quran.com → surahs table
2. Fetch ayahs (Uthmani + Imlaei + translations + audio) → ayahs table
3. Parse Quranic Arabic Corpus morphology → words, roots tables
4. Parse tajweed annotations → tajweed_annotations table
5. Validate row counts and checksums
6. Diff against previous load (fail loudly on Quranic text changes)
"""
import asyncio
import hashlib
import json
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

from etl.config import settings
from etl.quran_com_client import QuranComClient
from etl.parsers.corpus_parser import CorpusParser
from etl.parsers.tajweed_parser import TajweedParser

log = structlog.get_logger()


async def run_full_pipeline():
    """Run the complete ETL pipeline."""
    log.info("Starting ETL pipeline", timestamp=datetime.now(timezone.utc).isoformat())

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    client = QuranComClient()
    corpus_parser = CorpusParser()
    tajweed_parser = TajweedParser()

    try:
        # Step 1: Surahs
        surahs = await client.get_surahs()
        assert len(surahs) == settings.EXPECTED_SURAH_COUNT, \
            f"Expected {settings.EXPECTED_SURAH_COUNT} surahs, got {len(surahs)}"

        async with session_factory() as db:
            for s in surahs:
                await db.execute(text("""
                    INSERT INTO surahs (surah_number, name_arabic, name_translit,
                        name_translated, revelation_place, ayah_count)
                    VALUES (:num, :ar, :tr, :trans, :rev, :count)
                    ON CONFLICT (surah_number) DO UPDATE SET
                        name_arabic = EXCLUDED.name_arabic,
                        name_translit = EXCLUDED.name_translit,
                        ayah_count = EXCLUDED.ayah_count
                """), {
                    "num": s["id"],
                    "ar": s["name_arabic"],
                    "tr": s["name_simple"],
                    "trans": json.dumps({"en": s["translated_name"]["name"]}),
                    "rev": "makkah" if s["revelation_place"] == "makkah" else "madinah",
                    "count": s["verses_count"],
                })
            await db.commit()
        log.info("Surahs loaded", count=len(surahs))

        # Step 2: Ayahs + words (for each surah)
        total_ayahs = 0
        total_words = 0
        for surah in surahs:
            surah_number = surah["id"]
            ayahs = await client.get_ayahs(surah_number)
            total_ayahs += len(ayahs)

            # TODO: Fetch word-by-word data and merge with corpus morphology
            # TODO: Insert ayahs and words into DB
            # TODO: Parse tajweed annotations

        log.info("Ayahs loaded", count=total_ayahs)

        # Step 3: Validate
        assert total_ayahs == settings.EXPECTED_AYAH_COUNT, \
            f"Expected {settings.EXPECTED_AYAH_COUNT} ayahs, got {total_ayahs}"

        # Step 4: Checksum validation
        # TODO: Compare Quranic text checksums against previous load
        # Any diff in Quranic text itself FAILS the pipeline loudly

        log.info("ETL pipeline completed successfully",
                 surahs=len(surahs), ayahs=total_ayahs)

    except Exception as e:
        log.error("ETL pipeline failed", error=str(e))
        raise
    finally:
        await client.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_full_pipeline())
