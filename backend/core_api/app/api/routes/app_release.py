"""App release routes: version info + APK download for OTA updates.

The release artifacts (``app_release.json`` and the signed ``app-release.apk``)
live on the host in a directory bind-mounted into the container at
``/app/releases`` (read-only).  To publish a new build, drop the APK
and update ``app_release.json`` on the host — no rebuild/restart needed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

logger = None  # set lazily to avoid import-time side effects

RELEASES_DIR = Path(os.environ.get("APP_RELEASES_DIR", "/app/releases"))
RELEASE_JSON = RELEASES_DIR / "app_release.json"
DEFAULT_APK = "app-release.apk"

router = APIRouter(prefix="/v1", tags=["app-release"])


def _load_release() -> Dict[str, Any]:
    if not RELEASE_JSON.exists():
        raise HTTPException(
            status_code=503,
            detail={
                "type": "about:blank",
                "title": "Unavailable",
                "status": 503,
                "detail": "No app release configured.",
            },
        )
    try:
        return json.loads(RELEASE_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "type": "about:blank",
                "title": "Unavailable",
                "status": 503,
                "detail": f"Failed to read release config: {exc}",
            },
        )


@router.get("/app/version")
async def app_version() -> Dict[str, Any]:
    """Return the latest app version + OTA update metadata.

    The Flutter app calls this on launch and compares ``version_code``
    against its own ``package_info_plus`` version to decide whether to
    prompt (or force) an update.
    """
    return JSONResponse(_load_release())


@router.get("/app/download")
async def app_download(
    file: str = Query(DEFAULT_APK, description="APK filename in the releases dir"),
) -> FileResponse:
    """Stream the latest release APK for in-app (OTA) installation."""
    # Prevent path traversal: only allow a bare filename inside RELEASES_DIR.
    candidate = (RELEASES_DIR / os.path.basename(file)).resolve()
    if not str(candidate).startswith(str(RELEASES_DIR.resolve())) or not candidate.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": "APK not found.",
            },
        )
    return FileResponse(
        str(candidate),
        media_type="application/vnd.android.package-archive",
        filename=candidate.name,
    )
