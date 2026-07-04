"""Recitation upload and result polling endpoints."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from uuid import uuid4, UUID
import redis.asyncio as redis
import json

from app.core.config import settings
from app.schemas.recitation import RecitationUploadResponse, RecitationResult

router = APIRouter()

_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.post("/recitations/upload", response_model=RecitationUploadResponse)
async def upload_recitation(
    audio: UploadFile = File(...),
    surah_number: int = Form(...),
    ayah_start: int = Form(...),
    ayah_end: int = Form(...),
    qiraat: str = Form("hafs"),
    user_id: str = Form(...),
):
    """Accept a recitation audio upload. Enqueues inference job.

    Audio must be mono 16kHz 16-bit PCM WAV.
    """
    # Validate audio format
    if audio.content_type not in ("audio/wav", "audio/wave", "audio/x-wav", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Audio must be WAV format")

    session_id = uuid4()

    # TODO: Upload to S3
    audio_key = f"recitations/{user_id}/{session_id}.wav"
    # In production: s3_client.put_object(Bucket=..., Key=audio_key, Body=await audio.read())

    # Enqueue inference job via Redis Streams
    job = {
        "session_id": str(session_id),
        "user_id": user_id,
        "surah_number": surah_number,
        "ayah_start": ayah_start,
        "ayah_end": ayah_end,
        "qiraat": qiraat,
        "audio_key": audio_key,
        "model_version": settings.MODEL_VERSION,
    }
    await _redis.xadd("recitation:jobs", job)

    return RecitationUploadResponse(
        session_id=session_id,
        status="queued",
        estimated_wait_s=settings.INFERENCE_TIMEOUT_S,
    )


@router.get("/recitations/{session_id}", response_model=RecitationResult)
async def get_recitation_result(session_id: UUID):
    """Poll for recitation results. Returns 202 if still processing."""
    raw = await _redis.get(f"recitation:result:{session_id}")
    if raw:
        return RecitationResult(**json.loads(raw))
    raise HTTPException(
        status_code=202,
        detail="Processing. Retry in a few seconds.",
        headers={"Retry-After": "3"},
    )
