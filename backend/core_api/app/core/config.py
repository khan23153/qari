"""Core configuration for the Qari core_api service."""

from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="QARI_",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "qari-core-api"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://qari:qari@localhost:5432/qari"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 3600

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # --- JWT ---
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # --- Firebase ---
    firebase_credentials_json: Optional[str] = None
    firebase_project_id: Optional[str] = None

    # --- CORS ---
    cors_origins: list[str] = ["*"]

    # --- Rate limiting ---
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_sec: int = 60

    # --- Flashcards ---
    flashcard_daily_cap: int = 20

    # --- Streak ---
    streak_freeze_window_days: int = 30
    streak_freeze_grant: int = 1

    # --- Recitation API ---
    recitation_api_url: str = "http://recitation-api:8001"

    # --- Prometheus ---
    prometheus_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def database_url_sync(self) -> str:
        """Sync URL for Alembic / migrations."""
        return self.database_url.replace("+asyncpg", "+psycopg2")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings = get_settings()
