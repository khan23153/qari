"""
Qari ETL Pipeline
=================

One-time and scheduled ETL from Quran.com API v4 and the Quranic Arabic Corpus
into the Qari Postgres + Redis + CDN mirror.

Modules
-------
config               – ETLSettings, API URLs, DB URL, expected counts
quran_com_client     – Async httpx client for Quran.com API v4
parsers.corpus_parser – Quranic Arabic Corpus TSV morphology parser
parsers.tajweed_parser – Tajweed markup annotation parser
parsers.audio_segment_parser – Audio segment timestamp parser
db_loader            – Async database upsert loader
validators           – Row-count, checksum, and diff validators
run_full_pipeline    – Orchestrates the full ETL run
"""

__version__ = "1.0.0"
