"""Schemas for recitation API."""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class RecitationUploadResponse(BaseModel):
    session_id: UUID
    status: str = "queued"
    estimated_wait_s: int = 5


class RecitationResultWord(BaseModel):
    key: str
    verdict: str = Field(..., pattern="^(correct|mispronounced|omitted|inserted_extra|low_confidence)$")
    error_detail: Optional[dict] = None
    user_clip: Optional[dict] = None
    reference_audio_url: Optional[str] = None


class RecitationResult(BaseModel):
    session_id: UUID
    overall_score: Optional[int] = None
    fluency_score: Optional[int] = None
    tajweed_score: Optional[int] = None
    words: list[RecitationResultWord] = []
    model_version: str
