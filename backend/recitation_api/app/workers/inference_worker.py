"""GPU inference worker — consumes recitation:jobs from Redis Streams.

Runs Whisper-Quran ASR + Wav2Vec2 forced alignment + optional Tajweed checks.
Writes results to Redis and publishes via WebSocket channel.
"""
import asyncio
import json
import logging
from uuid import UUID

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)
_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def process_job(job: dict) -> dict:
    """Process a single recitation job through the ML pipeline.

    Steps:
    1. Download audio from S3
    2. ASR pass (Whisper-Quran) → hypothesis tokens
    3. Word-level alignment (Levenshtein vs expected text)
    4. Forced alignment (Wav2Vec2-CTC) → per-word timestamps
    5. Optional Tajweed checks (Phase 2)
    6. Score + persist
    """
    session_id = job["session_id"]
    surah_number = int(job["surah_number"])
    ayah_start = int(job["ayah_start"])
    ayah_end = int(job["ayah_end"])

    # TODO: Implement actual ML pipeline
    # For now, return a placeholder structure
    result = {
        "session_id": session_id,
        "overall_score": None,
        "fluency_score": None,
        "tajweed_score": None,
        "words": [],
        "model_version": settings.MODEL_VERSION,
    }

    # Persist result
    await _redis.setex(
        f"recitation:result:{session_id}",
        86400,  # 24h TTL
        json.dumps(result),
    )

    # Publish to WebSocket channel
    await _redis.publish(
        f"recitation:ws:{session_id}",
        json.dumps(result),
    )

    # TODO: Write to PostgreSQL via core-api
    # TODO: Auto-create flashcards for missed words

    logger.info(f"Processed recitation job {session_id}")
    return result


async def main():
    """Consume recitation:jobs stream and process each job."""
    logger.info("Starting recitation inference worker...")
    while True:
        # Read from stream
        response = await _redis.xread(
            {"recitation:jobs": "0"},
            count=1,
            block=5000,
        )
        if not response:
            continue

        for _stream, messages in response:
            for msg_id, job_data in messages:
                try:
                    await process_job(job_data)
                    await _redis.xdel("recitation:jobs", msg_id)
                except Exception as e:
                    logger.error(f"Job {msg_id} failed: {e}")
                    # TODO: dead-letter queue


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
