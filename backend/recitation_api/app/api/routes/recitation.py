"""Recitation upload route: multipart audio upload with validation."""

import json
import os
import uuid
import wave
from typing import Optional

from fastapi import APIRouter, Form, File, UploadFile, HTTPException, status
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.recitation import (
    RecitationUploadResponse,
    RecitationSessionResult,
    RecitationWordResult,
)
import redis.asyncio as redis

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/recitations", tags=["recitation"])

_redis: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _validate_wav_header(content: bytes) -> tuple[int, int, int]:
    """Validate WAV header and return (sample_rate, channels, bits_per_sample).

    Raises HTTPException if the file is not a valid mono 16kHz WAV.
    """
    if len(content) < 44:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "about:blank",
                "title": "Invalid Audio File",
                "status": 422,
                "detail": "File too small to be a valid WAV",
            },
        )

    # Check RIFF header
    if content[:4] != b"RIFF" or content[8:12] != b"WAVE":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "about:blank",
                "title": "Invalid Audio File",
                "status": 422,
                "detail": "Not a valid WAV file (missing RIFF/WAVE header)",
            },
        )

    # Parse fmt chunk
    import struct
    try:
        # Find fmt chunk
        idx = 12
        fmt_found = False
        sample_rate = channels = bits_per_sample = 0
        while idx < len(content) - 8:
            chunk_id = content[idx:idx+4]
            chunk_size = struct.unpack_from("<I", content, idx+4)[0]
            if chunk_id == b"fmt ":
                fmt_found = True
                audio_format = struct.unpack_from("<H", content, idx+8)[0]
                channels = struct.unpack_from("<H", content, idx+10)[0]
                sample_rate = struct.unpack_from("<I", content, idx+12)[0]
                bits_per_sample = struct.unpack_from("<H", content, idx+22)[0]
                break
            idx += 8 + chunk_size + (chunk_size % 2)  # pad to even

        if not fmt_found:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "about:blank",
                    "title": "Invalid Audio File",
                    "status": 422,
                    "detail": "WAV file missing fmt chunk",
                },
            )

        return sample_rate, channels, bits_per_sample

    except struct.error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "about:blank",
                "title": "Invalid Audio File",
                "status": 422,
                "detail": "Corrupted WAV header",
            },
        )


@router.post("/upload", response_model=RecitationUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_recitation(
    surah_number: int = Form(..., ge=1, le=114),
    ayah_from: int = Form(..., ge=1),
    ayah_to: int = Form(..., ge=ayah_from),
    qari_id: Optional[int] = Form(None),
    audio: UploadFile = File(...),
):
    """Upload a recitation audio file for AI evaluation.

    Accepts mono 16kHz WAV files. Returns 202 with a session_id.
    The audio is enqueued onto a Redis Stream for GPU inference.
    """
    # --- Validate file size ---
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    content = await audio.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "type": "about:blank",
                "title": "Payload Too Large",
                "status": 413,
                "detail": f"Audio file exceeds {settings.max_upload_size_mb}MB limit",
            },
        )

    # --- Validate content type ---
    content_type = audio.content_type or ""
    if "wav" not in content_type.lower() and not audio.filename.lower().endswith(".wav"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "type": "about:blank",
                "title": "Unsupported Media Type",
                "status": 415,
                "detail": f"Only WAV files are accepted, got '{content_type or audio.filename}'",
            },
        )

    # --- Validate WAV format ---
    sample_rate, channels, bits_per_sample = _validate_wav_header(content)

    if sample_rate != settings.audio_sample_rate:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "about:blank",
                "title": "Invalid Audio Format",
                "status": 422,
                "detail": f"Sample rate must be {settings.audio_sample_rate}Hz, got {sample_rate}Hz",
            },
        )

    if channels != settings.audio_channels:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "about:blank",
                "title": "Invalid Audio Format",
                "status": 422,
                "detail": f"Audio must be mono (1 channel), got {channels} channels",
            },
        )

    # --- Compute duration ---
    # Duration = (data_size) / (sample_rate * channels * bits_per_sample/8)
    # Approximate: total file size minus header
    data_size = len(content) - 44
    bytes_per_sample = bits_per_sample // 8
    duration_sec = data_size / (sample_rate * channels * bytes_per_sample) if bytes_per_sample > 0 else 0

    # --- Generate session ID ---
    session_id = str(uuid.uuid4())

    # --- Save audio file ---
    storage_path = os.path.join(settings.audio_storage_path, session_id)
    os.makedirs(storage_path, exist_ok=True)
    file_path = os.path.join(storage_path, "audio.wav")
    with open(file_path, "wb") as f:
        f.write(content)

    # --- Store session metadata in Redis ---
    r = _get_redis()
    session_meta = {
        "session_id": session_id,
        "surah_number": str(surah_number),
        "ayah_from": str(ayah_from),
        "ayah_to": str(ayah_to),
        "qari_id": str(qari_id) if qari_id else "",
        "status": "queued",
        "audio_path": file_path,
        "audio_duration_sec": str(round(duration_sec, 2)),
        "queued_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }
    await r.hset(f"qari:recitation:session:{session_id}", mapping=session_meta)
    await r.expire(f"qari:recitation:session:{session_id}", 86400)  # 24h TTL

    # --- Enqueue job onto Redis Stream ---
    job_payload = {
        "session_id": session_id,
        "surah_number": str(surah_number),
        "ayah_from": str(ayah_from),
        "ayah_to": str(ayah_to),
        "audio_path": file_path,
        "audio_duration_sec": str(round(duration_sec, 2)),
    }
    if qari_id:
        job_payload["qari_id"] = str(qari_id)

    entry_id = await r.xadd(
        settings.recitation_stream,
        job_payload,
        maxlen=settings.stream_max_len,
        approximate=True,
    )

    logger.info(
        "recitation.uploaded",
        session_id=session_id,
        surah=surah_number,
        ayah_range=f"{ayah_from}-{ayah_to}",
        duration_sec=round(duration_sec, 2),
        stream_entry_id=entry_id,
        size_bytes=len(content),
    )

    return RecitationUploadResponse(
        session_id=uuid.UUID(session_id),
        status="queued",
        message="Audio uploaded and queued for inference",
        estimated_wait_sec=30,
    )


@router.get("/{session_id}", response_model=RecitationSessionResult)
async def get_recitation_result(session_id: str):
    """Poll for recitation results by session_id."""
    r = _get_redis()

    # Get session metadata
    session_data = await r.hgetall(f"qari:recitation:session:{session_id}")
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": f"Recitation session '{session_id}' not found",
            },
        )

    # Get word results from Redis list
    word_results_raw = await r.lrange(f"qari:recitation:results:{session_id}", 0, -1)
    word_results = []
    for raw in word_results_raw:
        try:
            wr = json.loads(raw)
            word_results.append(RecitationWordResult(**wr))
        except (json.JSONDecodeError, ValidationError):
            continue

    status_val = session_data.get("status", "queued")

    result = RecitationSessionResult(
        session_id=uuid.UUID(session_id),
        surah_number=int(session_data.get("surah_number", 0)),
        ayah_from=int(session_data.get("ayah_from", 0)),
        ayah_to=int(session_data.get("ayah_to", 0)),
        status=status_val,
        total_words=int(session_data["total_words"]) if "total_words" in session_data else None,
        correct_words=int(session_data["correct_words"]) if "correct_words" in session_data else None,
        accuracy_pct=float(session_data["accuracy_pct"]) if "accuracy_pct" in session_data else None,
        error_message=session_data.get("error_message"),
        audio_duration_sec=float(session_data["audio_duration_sec"]) if "audio_duration_sec" in session_data else None,
        queued_at=session_data.get("queued_at"),
        completed_at=session_data.get("completed_at"),
        word_results=word_results,
    )

    return result
