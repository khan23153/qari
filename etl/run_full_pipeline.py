"""
Full ETL pipeline orchestrator.

Runs the complete extraction → transform → load → validate cycle:

1. Fetch all 114 surahs from Quran.com → validate count
2. For each surah, fetch ayahs (Uthmani, Imlaei, translations, audio)
3. Fetch word-by-word translations and transliterations
4. Fetch tajweed-markup text and parse into annotations
5. Parse Quranic Arabic Corpus morphology → extract roots
6. Load everything into Postgres via DatabaseLoader
7. Compute checksums and diff against previous load
8. Log a comprehensive summary

Usage::

    python -m etl.run_full_pipeline

Or programmatically::

    import asyncio
    from etl.run_full_pipeline import run_full_pipeline
    asyncio.run(run_full_pipeline())
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from .config import ETLSettings
from .quran_com_client import QuranComClient, QuranComError
from .parsers.corpus_parser import CorpusParser
from .parsers.tajweed_parser import TajweedParser
from .parsers.audio_segment_parser import AudioSegmentParser
from .db_loader import DatabaseLoader
from .validators import ETLValidator, ValidationResult

logger = structlog.get_logger(__name__)

# Configure structlog for console output
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
    cache_logger_on_first_use=True,
)


# ---------------------------------------------------------------------------
# Pipeline result
# ---------------------------------------------------------------------------

class PipelineResult:
    """Aggregated result of the full ETL run."""

    def __init__(self) -> None:
        self.load_id: str = ""
        self.started_at: Optional[datetime] = None
        self.finished_at: Optional[datetime] = None
        self.duration_sec: float = 0.0

        # Counts
        self.surahs_fetched: int = 0
        self.ayahs_fetched: int = 0
        self.words_fetched: int = 0
        self.roots_extracted: int = 0
        self.tajweed_annotations: int = 0
        self.audio_files_fetched: int = 0

        # Validation
        self.validation: Optional[ValidationResult] = None
        self.diff_identical: bool = True

        # Errors
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def success(self) -> bool:
        """True if the pipeline completed without errors and validation passed."""
        return (
            len(self.errors) == 0
            and self.validation is not None
            and self.validation.passed
            and self.diff_identical
        )

    def summary(self) -> Dict[str, Any]:
        """Return a JSON-serialisable summary."""
        return {
            "load_id": self.load_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_sec": round(self.duration_sec, 2),
            "success": self.success,
            "surahs_fetched": self.surahs_fetched,
            "ayahs_fetched": self.ayahs_fetched,
            "words_fetched": self.words_fetched,
            "roots_extracted": self.roots_extracted,
            "tajweed_annotations": self.tajweed_annotations,
            "audio_files_fetched": self.audio_files_fetched,
            "validation_passed": self.validation.passed if self.validation else False,
            "validation_errors": self.validation.errors if self.validation else [],
            "diff_identical": self.diff_identical,
            "errors": self.errors,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def run_full_pipeline(
    settings: Optional[ETLSettings] = None,
    corpus_file_path: Optional[str] = None,
) -> PipelineResult:
    """Run the complete ETL pipeline.

    Parameters
    ----------
    settings:
        ETL configuration.  If None, defaults are loaded from env vars.
    corpus_file_path:
        Path to the Quranic Arabic Corpus morphology TSV file.
        If None, looks for ``QURANIC_CORPUS_FILE`` env var or
        ``./quranic-corpus-morphology.txt``.

    Returns
    -------
    ``PipelineResult`` with full run statistics.
    """
    settings = settings or ETLSettings()
    result = PipelineResult()
    result.load_id = f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    result.started_at = datetime.now().astimezone()

    start_time = time.monotonic()

    logger.info("pipeline_start", load_id=result.load_id, config=settings.summary())

    # Initialise components
    client = QuranComClient(
        base_url=settings.quran_com_base_url,
        timeout=settings.http_timeout,
        max_retries=settings.max_retries,
        retry_backoff=settings.retry_backoff,
        rate_limit_delay=settings.rate_limit_delay,
    )
    loader = DatabaseLoader(settings.database_url, schema=settings.db_schema)
    validator = ETLValidator(
        expected_surahs=settings.expected_surahs,
        expected_ayahs=settings.expected_ayahs,
        expected_words=settings.expected_words,
    )
    tajweed_parser = TajweedParser()
    audio_parser = AudioSegmentParser()
    corpus_parser = CorpusParser()

    try:
        # ------------------------------------------------------------------
        # Step 1: Fetch surahs
        # ------------------------------------------------------------------
        logger.info("step_1_fetch_surahs")
        try:
            surahs = await client.get_surahs()
            result.surahs_fetched = len(surahs)

            if len(surahs) != settings.expected_surahs:
                result.errors.append(
                    f"Surah count mismatch: expected {settings.expected_surahs}, "
                    f"got {len(surahs)}"
                )
                logger.error("surah_count_mismatch", expected=settings.expected_surahs, actual=len(surahs))
                # Continue anyway — we still want to load what we have

        except QuranComError as exc:
            result.errors.append(f"Failed to fetch surahs: {exc}")
            logger.error("fetch_surahs_failed", error=str(exc))
            raise

        # ------------------------------------------------------------------
        # Step 2: Fetch ayahs, word translations, tajweed, and audio per surah
        # ------------------------------------------------------------------
        logger.info("step_2_fetch_ayahs")
        all_ayahs: List[Dict[str, Any]] = []
        all_words: List[Dict[str, Any]] = []
        all_tajweed: List[Dict[str, Any]] = []
        all_audio: List[Dict[str, Any]] = []
        uthmani_texts: Dict[str, str] = {}
        imlaei_texts: Dict[str, str] = {}

        # Use a semaphore to limit concurrency
        sem = asyncio.Semaphore(settings.max_concurrent_surahs)

        async def process_surah(surah: Dict[str, Any]) -> None:
            surah_num = surah.get("id") or surah.get("chapter_number", 0)
            async with sem:
                logger.info("processing_surah", surah=surah_num)

                # Ayahs with text and translations
                try:
                    ayahs = await client.get_ayahs(
                        surah_num,
                        qari_id=settings.qari_ids[0] if settings.qari_ids else 1,
                        translations=settings.translation_ids,
                    )
                except QuranComError as exc:
                    result.warnings.append(f"Failed to fetch ayahs for surah {surah_num}: {exc}")
                    return

                for a in ayahs:
                    verse_key = a.get("verse_key", f"{surah_num}:{a.get('verse_number', 0)}")
                    a["surah_id"] = surah_num
                    a["verse_key"] = verse_key

                    uthmani = a.get("text_uthmani", "")
                    imlaei = a.get("text_imlaei", "")
                    if uthmani:
                        uthmani_texts[verse_key] = uthmani
                    if imlaei:
                        imlaei_texts[verse_key] = imlaei

                all_ayahs.extend(ayahs)

                # Word-by-word translations
                try:
                    word_data = await client.get_word_translations(surah_num)
                    for w in word_data:
                        # Word data comes as per-verse with nested words
                        verse_key = w.get("verse_key", "")
                        for word in w.get("words", []):
                            word["verse_key"] = verse_key
                            all_words.append(word)
                except QuranComError as exc:
                    result.warnings.append(
                        f"Failed to fetch word translations for surah {surah_num}: {exc}"
                    )

                # Tajweed text
                if settings.load_tajweed:
                    try:
                        tajweed_verses = await client.get_tajweed_text(surah_num)
                        for tv in tajweed_verses:
                            ayah_num = tv.get("verse_number", 0)
                            tajweed_text = tv.get("text_uthmani_tajweed", "")
                            verse_key = tv.get("verse_key", f"{surah_num}:{ayah_num}")
                            parsed = tajweed_parser.parse_ayah(
                                surah_num, ayah_num, tajweed_text
                            )
                            parsed["verse_key"] = verse_key
                            all_tajweed.append(parsed)
                    except QuranComError as exc:
                        result.warnings.append(
                            f"Failed to fetch tajweed text for surah {surah_num}: {exc}"
                        )

                # Audio segments
                if settings.load_audio and settings.qari_ids:
                    for qari_id in settings.qari_ids[:2]:  # Limit to first 2 qaris for ETL
                        try:
                            audio_files = await client.get_audio_segments(
                                surah_num, qari_id
                            )
                            for af in audio_files:
                                parsed_audio = audio_parser.parse_ayah_audio(
                                    surah_num,
                                    af.get("verse_number", 0),
                                    af,
                                )
                                parsed_audio["qari_id"] = qari_id
                                all_audio.append(parsed_audio)
                                result.audio_files_fetched += 1
                        except QuranComError as exc:
                            result.warnings.append(
                                f"Failed to fetch audio for surah {surah_num}, "
                                f"qari {qari_id}: {exc}"
                            )

        # Process all surahs concurrently (bounded by semaphore)
        await asyncio.gather(*(process_surah(s) for s in surahs))

        result.ayahs_fetched = len(all_ayahs)
        result.words_fetched = len(all_words)
        result.tajweed_annotations = sum(
            len(a.get("annotations", [])) for a in all_tajweed
        )

        logger.info(
            "fetch_complete",
            surahs=result.surahs_fetched,
            ayahs=result.ayahs_fetched,
            words=result.words_fetched,
            tajweed_annotations=result.tajweed_annotations,
            audio_files=result.audio_files_fetched,
        )

        # ------------------------------------------------------------------
        # Step 3: Parse corpus morphology
        # ------------------------------------------------------------------
        if settings.load_corpus and corpus_file_path:
            logger.info("step_3_parse_corpus", file=corpus_file_path)
            try:
                corpus_words = corpus_parser.parse_morphology_file(corpus_file_path)
                roots = corpus_parser.extract_roots(corpus_words)
                result.roots_extracted = len(roots)

                # Merge corpus morphology into word data
                # Build a lookup: (surah, ayah, word) → corpus word dict
                corpus_lookup: Dict[str, Dict[str, Any]] = {}
                for cw in corpus_words:
                    key = f"{cw['surah']}:{cw['ayah']}:{cw['word']}"
                    corpus_lookup[key] = cw

                for word in all_words:
                    verse_key = word.get("verse_key", "")
                    word_num = word.get("word_number", word.get("position", 0))
                    lookup_key = f"{verse_key}:{word_num}"
                    cw = corpus_lookup.get(lookup_key)
                    if cw:
                        word["pos_tag"] = cw.get("pos_tag", "")
                        word["pos_group"] = cw.get("pos_group", "")
                        word["lemma"] = cw.get("lemma")
                        word["root"] = cw.get("root")
                        word["features"] = cw.get("features", {})

                logger.info(
                    "corpus_parsed",
                    corpus_words=len(corpus_words),
                    roots=len(roots),
                )
            except FileNotFoundError:
                result.warnings.append(
                    f"Corpus file not found: {corpus_file_path}"
                )
                logger.warning("corpus_file_not_found", path=corpus_file_path)
        else:
            logger.info("step_3_parse_corpus_skipped")

        # ------------------------------------------------------------------
        # Step 4: Load into database
        # ------------------------------------------------------------------
        logger.info("step_4_load_database")
        try:
            await loader.create_schema()

            async with loader.session() as db:
                # Load surahs
                await loader.load_surahs(db, surahs)

                # Load ayahs
                await loader.load_ayahs(db, all_ayahs)

                # Load words
                await loader.load_words(db, all_words)

                # Load roots
                if settings.load_corpus and corpus_file_path:
                    await loader.load_roots(db, roots)

                # Load tajweed
                if settings.load_tajweed:
                    await loader.load_tajweed(db, all_tajweed)

                # Load qaris
                try:
                    qaris = await client.get_qaris()
                    await loader.load_qaris(db, qaris)
                except QuranComError as exc:
                    result.warnings.append(f"Failed to fetch/load qaris: {exc}")

                # ------------------------------------------------------------------
                # Step 5: Validate checksums and diff
                # ------------------------------------------------------------------
                logger.info("step_5_validate")

                # Compute checksums
                uthmani_checksums = validator.validate_checksums(uthmani_texts)
                imlaei_checksums = validator.validate_checksums(imlaei_texts)

                # Get previous checksums for diff
                previous_checksums = await loader.get_previous_checksums(db)

                # Diff Uthmani text
                diff_identical = True
                if previous_checksums:
                    prev_uthmani = {
                        k: v.get("uthmani", "") for k, v in previous_checksums.items()
                    }
                    diff = validator.diff_against_previous(uthmani_checksums, prev_uthmani)
                    if not diff.identical:
                        diff_identical = False
                        result.errors.append(
                            f"QURANIC TEXT DIFF DETECTED: {len(diff.changed)} verses "
                            f"have changed Uthmani text. "
                            f"Sample: {diff.changed[:3]}"
                        )
                        logger.error(
                            "quranic_text_diff",
                            changed_verses=[c[0] for c in diff.changed],
                            count=len(diff.changed),
                        )

                result.diff_identical = diff_identical

                # Validate row counts
                result.validation = validator.validate_row_counts(
                    surahs=result.surahs_fetched,
                    ayahs=result.ayahs_fetched,
                    words=result.words_fetched,
                )

                # Store new checksums
                combined_checksums: Dict[str, Dict[str, str]] = {}
                for vk, checksum in uthmani_checksums.items():
                    combined_checksums[vk] = {
                        "uthmani": checksum,
                        "imlaei": imlaei_checksums.get(vk, ""),
                    }
                await loader.load_checksums(db, result.load_id, combined_checksums)

        except Exception as exc:
            result.errors.append(f"Database error: {exc}")
            logger.error("database_error", error=str(exc), exc_info=True)

    except Exception as exc:
        result.errors.append(f"Pipeline error: {exc}")
        logger.error("pipeline_error", error=str(exc), exc_info=True)

    finally:
        # ------------------------------------------------------------------
        # Cleanup
        # ------------------------------------------------------------------
        await client.close()
        await loader.close()

        result.finished_at = datetime.now().astimezone()
        result.duration_sec = time.monotonic() - start_time

    # ------------------------------------------------------------------
    # Step 6: Log summary
    # ------------------------------------------------------------------
    logger.info("pipeline_complete", **result.summary())

    if not result.success:
        logger.error(
            "pipeline_failed",
            errors=result.errors,
            validation_errors=result.validation.errors if result.validation else [],
        )
        # In production, this would trigger an alert
        # Exit with non-zero status for CI/CD
        if not result.diff_identical:
            logger.critical(
                "QURANIC_TEXT_INTEGRITY_FAILURE",
                message="The Quranic text has changed between loads. "
                        "This is a critical integrity failure. "
                        "The pipeline is aborted.",
            )

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for running the full ETL pipeline."""
    import os

    settings = ETLSettings()
    corpus_path = os.getenv("QURANIC_CORPUS_FILE", "quranic-corpus-morphology.txt")

    result = asyncio.run(run_full_pipeline(settings, corpus_path))

    print("\n" + "=" * 60)
    print("ETL Pipeline Summary")
    print("=" * 60)
    print(f"Load ID:          {result.load_id}")
    print(f"Duration:         {result.duration_sec:.1f}s")
    print(f"Success:          {result.success}")
    print(f"Surahs:           {result.surahs_fetched}")
    print(f"Ayahs:            {result.ayahs_fetched}")
    print(f"Words:            {result.words_fetched}")
    print(f"Roots:            {result.roots_extracted}")
    print(f"Tajweed annots:   {result.tajweed_annotations}")
    print(f"Audio files:      {result.audio_files_fetched}")
    print(f"Diff identical:   {result.diff_identical}")
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for e in result.errors:
            print(f"  ✗ {e}")
    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"  ⚠ {w}")
    print("=" * 60)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
