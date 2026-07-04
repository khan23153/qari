"""Recitation Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RecitationUploadRequest(BaseModel):
    """Metadata sent alongside the audio file (as form fields)."""
    surah_number: int = Field(..., ge=1, le=114)
    ayah_from: int = Field(..., ge=1)
    ayah_to: int = Field(..., ge=1)
    qari_id: Optional[int] = None


class RecitationUploadResponse(BaseModel):
    """202 Accepted response after upload."""
    session_id: uuid.UUID
    status: str = "queued"
    message: str = "Audio uploaded and queued for inference"
    estimated_wait_sec: int = 30


class RecitationWordResult(BaseModel):
    """Per-word verdict from the ML engine."""
    surah_number: int
    ayah_number: int
    word_position: int
    expected_text: str
    detected_text: Optional[str] = None
    verdict: str
    confidence: Optional[float] = None
    error_detail: Optional[str] = None
    audio_start_sec: Optional[float] = None
    audio_end_sec: Optional[float] = None


class RecitationSessionResult(BaseModel):
    """Full recitation session result (polled or WebSocket)."""
    session_id: uuid.UUID
    surah_number: int
    ayah_from: int
    ayah_to: int
    status: str
    total_words: Optional[int] = None
    correct_words: Optional[int] = None
    accuracy_pct: Optional[float] = None
    error_message: Optional[str] = None
    audio_duration_sec: Optional[float] = None
    queued_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    word_results: list[RecitationWordResult] = []


class RecitationProgressUpdate(BaseModel):
    """Real-time progress update sent over WebSocket."""
    session_id: uuid.UUID
    status: str  # queued, processing, completed, failed
    progress_pct: float = 0.0
    processed_words: int = 0
    total_words: Optional[int] = None
    word_results: list[RecitationWordResult] = []
    accuracy_pct: Optional[float] = None
    error_message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "qari-recitation-api"
    version: str = "1.0.0"
