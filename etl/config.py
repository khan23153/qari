"""
ETL configuration and settings.

Holds API endpoints, database URL, Redis URL, expected canonical counts,
reciter (qari) IDs, and translation edition IDs used throughout the pipeline.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List


# ---------------------------------------------------------------------------
# Canonical expected counts (the Quran has exactly these)
# ---------------------------------------------------------------------------

EXPECTED_SURAHS = 114
EXPECTED_AYAHS = 6_236
EXPECTED_WORDS = 77_430

# ---------------------------------------------------------------------------
# Quran.com API v4 base
# ---------------------------------------------------------------------------

QURAN_COM_BASE_URL = "https://api.quran.com/api/v4"
CORPUS_BASE_URL = "https://corpus.quran.com"

# ---------------------------------------------------------------------------
# Reciters (qaris) to mirror — Quran.com qari IDs
# ---------------------------------------------------------------------------

DEFAULT_QARI_IDS: List[int] = [
    1,    # Abdul Basit (Murattal)
    2,    # Abdul Basit (Mujawwad)
    3,    # Sudais
    4,    # Shuraim
    7,    # Minshawi (Murattal)
    8,    # Minshawi (Mujawwad)
    9,    # Al-Afasy
    10,  # Abdul Basit (Hafs)
]

# ---------------------------------------------------------------------------
# Translation editions to mirror (Quran.com resource IDs)
# ---------------------------------------------------------------------------

DEFAULT_TRANSLATION_IDS: List[int] = [
    131,  # Sahih International (English)
    20,   # Pickthall (English)
    85,   # Ahmed Ali (Urdu)
    149,  # Dr. Mustafa Khattab (English)
]

# Word-by-word translation / transliteration fields available on Quran.com
WORD_TRANSLATION_FIELDS: List[str] = [
    "translation",
    "transliteration",
]


@dataclass
class ETLSettings:
    """Runtime configuration for the ETL pipeline.

    All values can be overridden via environment variables so the same
    code runs locally, in CI, and in production.
    """

    # --- API endpoints -------------------------------------------------
    quran_com_base_url: str = field(
        default_factory=lambda: os.getenv("QURAN_COM_BASE_URL", QURAN_COM_BASE_URL)
    )
    corpus_base_url: str = field(
        default_factory=lambda: os.getenv("CORPUS_BASE_URL", CORPUS_BASE_URL)
    )

    # --- Database / cache ----------------------------------------------
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://qari:qari@localhost:5432/qari",
        )
    )
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )

    # --- Expected counts (for validation) ------------------------------
    expected_surahs: int = EXPECTED_SURAHS
    expected_ayahs: int = EXPECTED_AYAHS
    expected_words: int = EXPECTED_WORDS

    # --- Reciter / translation configuration ---------------------------
    qari_ids: List[int] = field(default_factory=lambda: list(DEFAULT_QARI_IDS))
    translation_ids: List[int] = field(default_factory=lambda: list(DEFAULT_TRANSLATION_IDS))

    # --- HTTP client tuning --------------------------------------------
    http_timeout: float = field(
        default_factory=lambda: float(os.getenv("ETL_HTTP_TIMEOUT", "30"))
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("ETL_MAX_RETRIES", "3"))
    )
    retry_backoff: float = field(
        default_factory=lambda: float(os.getenv("ETL_RETRY_BACKOFF", "1.0"))
    )
    rate_limit_delay: float = field(
        default_factory=lambda: float(os.getenv("ETL_RATE_LIMIT_DELAY", "0.2"))
    )

    # --- Concurrency ---------------------------------------------------
    max_concurrent_surahs: int = field(
        default_factory=lambda: int(os.getenv("ETL_MAX_CONCURRENT_SURAHS", "5"))
    )

    # --- Feature flags -------------------------------------------------
    load_audio: bool = field(
        default_factory=lambda: os.getenv("ETL_LOAD_AUDIO", "true").lower() == "true"
    )
    load_tajweed: bool = field(
        default_factory=lambda: os.getenv("ETL_LOAD_TAJWEED", "true").lower() == "true"
    )
    load_corpus: bool = field(
        default_factory=lambda: os.getenv("ETL_LOAD_CORPUS", "true").lower() == "true"
    )

    @property
    def db_schema(self) -> str:
        """Target Postgres schema for ETL tables."""
        return os.getenv("ETL_DB_SCHEMA", "quran")

    def summary(self) -> Dict[str, object]:
        """Return a JSON-serialisable summary for logging."""
        return {
            "quran_com_base_url": self.quran_com_base_url,
            "corpus_base_url": self.corpus_base_url,
            "expected_surahs": self.expected_surahs,
            "expected_ayahs": self.expected_ayahs,
            "expected_words": self.expected_words,
            "qari_ids": self.qari_ids,
            "translation_ids": self.translation_ids,
            "max_retries": self.max_retries,
            "max_concurrent_surahs": self.max_concurrent_surahs,
        }
