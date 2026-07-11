"""RFC 7807 problem+json exception handlers and custom exceptions."""

from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import structlog

logger = structlog.get_logger(__name__)


class ProblemException(Exception):
    """Raised to produce an RFC 7807 problem+json response."""

    def __init__(
        self,
        status: int = 400,
        title: str = "Bad Request",
        detail: str = "",
        type: str = "about:blank",
        instance: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type
        self.instance = instance
        self.extra = extra or {}
        super().__init__(detail)


class NotFoundError(ProblemException):
    def __init__(self, resource: str, resource_id: str | int, instance: Optional[str] = None):
        super().__init__(
            status=404,
            title="Not Found",
            detail=f"{resource} '{resource_id}' not found",
            type="about:blank",
            instance=instance,
        )


class ConflictError(ProblemException):
    def __init__(self, detail: str, instance: Optional[str] = None):
        super().__init__(
            status=409,
            title="Conflict",
            detail=detail,
            type="about:blank",
            instance=instance,
        )


class ForbiddenError(ProblemException):
    def __init__(self, detail: str = "You do not have access to this resource", instance: Optional[str] = None):
        super().__init__(
            status=403,
            title="Forbidden",
            detail=detail,
            type="about:blank",
            instance=instance,
        )


class RateLimitExceeded(ProblemException):
    def __init__(self, detail: str = "Rate limit exceeded", instance: Optional[str] = None):
        super().__init__(
            status=429,
            title="Too Many Requests",
            detail=detail,
            type="about:blank",
            instance=instance,
        )


def _problem_response(
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    instance: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> JSONResponse:
    """Build a problem+json JSONResponse."""
    body: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
    }
    if instance:
        body["instance"] = instance
    if extra:
        body.update(extra)
    return JSONResponse(
        status_code=status,
        content=jsonable_encoder(body),
        media_type="application/problem+json",
        headers={"Content-Type": "application/problem+json"},
    )


async def problem_exception_handler(request: Request, exc: ProblemException) -> JSONResponse:
    """Handle ProblemException → problem+json."""
    return _problem_response(
        status=exc.status,
        title=exc.title,
        detail=exc.detail,
        type_=exc.type,
        instance=exc.instance or str(request.url.path),
        extra=exc.extra,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Convert Starlette/FastAPI HTTPException → problem+json."""
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    title_map = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    return _problem_response(
        status=exc.status_code,
        title=title_map.get(exc.status_code, "Error"),
        detail=detail,
        instance=str(request.url.path),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic validation errors → problem+json."""
    return _problem_response(
        status=422,
        title="Validation Failed",
        detail="One or more fields failed validation",
        instance=str(request.url.path),
        extra={"errors": jsonable_encoder(exc.errors())},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions → 500 problem+json."""
    # Always log the full traceback so failures are diagnosable.
    logger.error("unhandled_exception", path=request.url.path, exc_info=exc)

    from app.core.config import settings

    detail = "An unexpected error occurred"
    # Surface the underlying error message outside production to aid debugging.
    if not settings.is_production:
        detail = f"{type(exc).__name__}: {exc}"

    return _problem_response(
        status=500,
        title="Internal Server Error",
        detail=detail,
        instance=str(request.url.path),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all problem+json exception handlers on *app*."""
    app.add_exception_handler(ProblemException, problem_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
