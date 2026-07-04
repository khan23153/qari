"""Common Pydantic schemas: pagination, error responses, language parameter."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from shared import AppLanguage

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False


class ProblemDetail(BaseModel):
    """RFC 7807 problem+json response body."""
    type: str = "about:blank"
    title: str = "Error"
    status: int
    detail: str = ""
    instance: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": "Surah 115 not found",
                "instance": "/v1/surahs/115",
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    service: str = "qari-core-api"
    version: str = "1.0.0"


class LangQueryParams(BaseModel):
    """Common ?lang= query parameter."""
    lang: AppLanguage = AppLanguage.en
