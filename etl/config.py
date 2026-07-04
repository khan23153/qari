"""ETL pipeline configuration."""
from pydantic_settings import BaseSettings


class ETLSettings(BaseSettings):
    # Source APIs
    QURAN_COM_API_BASE: str = "https://api.quran.com/api/v4"
    CORPUS_QURAN_BASE: str = "https://corpus.quran.com"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://qari:qari@localhost:5432/qari"

    # CDN
    CDN_BASE_URL: str = "https://cdn.qari.app"

    # Validation
    EXPECTED_SURAH_COUNT: int = 114
    EXPECTED_AYAH_COUNT: int = 6236
    EXPECTED_WORD_COUNT: int = 77430


settings = ETLSettings()
