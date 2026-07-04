"""Recitation API configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    ENV: str = "dev"

    REDIS_URL: str = "redis://localhost:6379/1"
    CORE_API_URL: str = "http://localhost:8000/v1"

    # S3
    S3_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET_NAME: str = "qari-media"
    CDN_BASE_URL: str = "https://cdn.qari.app"

    # ML
    MODEL_VERSION: str = "whisper-base-ar-quran-v1"
    INFERENCE_TIMEOUT_S: int = 30
    MAX_AUDIO_DURATION_S: int = 60
    SAMPLE_RATE: int = 16000

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Feature flags
    RECITATION_VERDICTS_ENABLED: bool = False
    TAJWEED_CHECKS_ENABLED: bool = False
    MIN_CONFIDENCE_THRESHOLD: float = 0.85


settings = Settings()
