"""Application configuration via environment variables."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    ENV: str = "dev"
    LOG_LEVEL: str = "info"

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://qari:qari@localhost:5432/qari"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET: str = "change-me-in-production"

    # S3 / CDN
    S3_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET_NAME: str = "qari-media"
    CDN_BASE_URL: str = "https://cdn.qari.app"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Feature flags
    RECITATION_VERDICTS_ENABLED: bool = False

    # Rate limiting
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_RECITATION: str = "60/day"

    @property
    def is_prod(self) -> bool:
        return self.ENV == "prod"


settings = Settings()
