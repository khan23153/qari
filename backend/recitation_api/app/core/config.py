"""Core configuration for the Qari recitation_api service."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for the recitation API service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="QARI_",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "qari-recitation-api"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 20

    # --- Audio upload ---
    max_upload_size_mb: int = 25
    allowed_audio_formats: list[str] = ["wav"]
    audio_sample_rate: int = 16000
    audio_channels: int = 1

    # --- Redis Streams ---
    recitation_stream: str = "qari:recitation:jobs"
    recitation_results_channel: str = "qari:recitation:results:{session_id}"
    recitation_consumer_group: str = "qari-inference-workers"
    recitation_consumer_name: str = "worker-1"
    stream_max_len: int = 10000
    poll_timeout_ms: int = 5000

    # --- CORS ---
    cors_origins: list[str] = ["*"]

    # --- Storage (audio files) ---
    audio_storage_path: str = "/tmp/qari_audio"

    # --- Recitation ML engine ---
    # When True, the worker uses the deterministic stub instead of loading the
    # real ML pipeline. Useful for local dev without GPU / model weights.
    ml_use_stub: bool = False
    # Directory of per-ayah reference JSON files ({surah}_{ayah}.json) consumed
    # by ml.tajweed.reference_store.ReferenceStore. See scripts/build_reference_bundle.py.
    reference_data_dir: str = ""
    # Base URL of core_api, used to lazily fetch reference words/tajweed when a
    # prebuilt reference file is not present.
    core_api_base_url: str = "http://localhost:8000"

    # --- Worker ---
    worker_enabled: bool = False
    worker_poll_interval_sec: int = 5

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
