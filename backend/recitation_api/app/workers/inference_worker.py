"""Inference worker: consumes recitation jobs from Redis Streams.

This worker runs as a separate process (or sidecar) that:
1. Reads jobs from the `qari:recitation:jobs` Redis Stream.
2. Loads the audio file from disk.
3. Runs the ML inference pipeline (delegates to the ML engine service).
4. Stores per-word results in Redis and publishes them via Pub/Sub.
5. Updates the session status in Redis.

In production, the actual ML inference call would be an HTTP/gRPC request
to the ML engine service. Here we implement the full stream consumption
loop with a pluggable inference callback.
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Inference callback type
# ---------------------------------------------------------------------------

InferenceCallback = Callable[[dict], "asyncio.Future"]


async def _default_inference(job: dict) -> dict:
    """Default inference stub.

    In production, replace this with an HTTP call to the ML engine service:

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.ml_engine_url}/infer",
                json=job,
                timeout=300,
            )
            return resp.json()

    For now, we simulate a result with placeholder verdicts.
    """
    surah = int(job.get("surah_number", 1))
    ayah_from = int(job.get("ayah_from", 1))
    ayah_to = int(job.get("ayah_to", 1))

    # Simulate processing time
    await asyncio.sleep(2)

    # Generate placeholder word results
    word_results = []
    for ayah in range(ayah_from, ayah_to + 1):
        for pos in range(1, 6):  # assume ~5 words per ayah
            word_results.append({
                "surah_number": surah,
                "ayah_number": ayah,
                "word_position": pos,
                "expected_text": f"word_{surah}_{ayah}_{pos}",
                "detected_text": f"word_{surah}_{ayah}_{pos}",
                "verdict": "correct",
                "confidence": 0.95,
                "audio_start_sec": pos * 0.5,
                "audio_end_sec": (pos + 1) * 0.5,
            })

    total = len(word_results)
    correct = sum(1 for w in word_results if w["verdict"] == "correct")
    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        "word_results": word_results,
        "total_words": total,
        "correct_words": correct,
        "accuracy_pct": round(accuracy, 2),
    }


class InferenceWorker:
    """Redis Streams consumer for recitation inference jobs.

    Usage::

        worker = InferenceWorker()
        await worker.start()
        # ... runs until cancelled
        await worker.stop()
    """

    def __init__(
        self,
        *,
        inference_callback: Optional[InferenceCallback] = None,
        consumer_name: Optional[str] = None,
    ):
        self._redis: Optional[redis.Redis] = None
        self._inference = inference_callback or _default_inference
        self._consumer_name = consumer_name or settings.recitation_consumer_name
        self._group = settings.recitation_consumer_group
        self._stream = settings.recitation_stream
        self._running = False
        self._processed = 0
        self._errors = 0

    async def start(self) -> None:
        """Start the worker loop."""
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._running = True

        # Ensure consumer group exists
        await self._ensure_consumer_group()

        logger.info(
            "worker.started",
            stream=self._stream,
            group=self._group,
            consumer=self._consumer_name,
        )

        try:
            await self._consume_loop()
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the worker and close Redis connection."""
        self._running = False
        if self._redis:
            await self._redis.aclose()
            self._redis = None
        logger.info("worker.stopped", processed=self._processed, errors=self._errors)

    async def _ensure_consumer_group(self) -> None:
        """Create the consumer group if it doesn't exist."""
        try:
            await self._redis.xgroup_create(
                self._stream,
                self._group,
                id="0",
                mkstream=True,
            )
            logger.info("worker.group_created", group=self._group)
        except redis.ResponseError as exc:
            if "BUSYGROUP" in str(exc):
                logger.info("worker.group_exists", group=self._group)
            else:
                raise

    async def _consume_loop(self) -> None:
        """Main consumption loop reading from the Redis Stream."""
        while self._running:
            try:
                # Read new messages
                response = await self._redis.xreadgroup(
                    groupname=self._group,
                    consumername=self._consumer_name,
                    streams={self._stream: ">"},
                    count=1,
                    block=settings.poll_timeout_ms,
                )

                if not response:
                    # No new messages — check for pending messages
                    await self._process_pending()
                    continue

                for stream_name, messages in response:
                    for msg_id, fields in messages:
                        await self._process_message(msg_id, fields)

            except asyncio.CancelledError:
                logger.info("worker.cancelled")
                break
            except Exception as exc:
                logger.error("worker.loop_error", error=str(exc))
                self._errors += 1
                await asyncio.sleep(settings.worker_poll_interval_sec)

    async def _process_pending(self) -> None:
        """Reclaim and process pending messages from crashed workers."""
        try:
            response = await self._redis.xautoclaim(
                self._stream,
                self._group,
                self._consumer_name,
                min_idle_time=60000,  # 60s before reclaiming
                start_id="0-0",
                count=1,
            )
            if response and response[1]:
                for msg_id, fields in response[1]:
                    logger.info("worker.reclaimed", msg_id=msg_id)
                    await self._process_message(msg_id, fields)
        except Exception as exc:
            logger.debug("worker.no_pending", error=str(exc))

    async def _process_message(self, msg_id: str, fields: dict) -> None:
        """Process a single recitation job message."""
        session_id = fields.get("session_id", "")
        logger.info("worker.processing", msg_id=msg_id, session_id=session_id)
        self._processed += 1

        try:
            # --- Update session status to processing ---
            await self._redis.hset(
                f"qari:recitation:session:{session_id}",
                mapping={
                    "status": "processing",
                    "processing_started_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Publish progress
            await self._publish_progress(session_id, {
                "session_id": session_id,
                "status": "processing",
                "progress_pct": 0.0,
                "processed_words": 0,
            })

            # --- Run inference ---
            result = await self._inference(fields)

            # --- Store word results in Redis ---
            word_results = result.get("word_results", [])
            results_key = f"qari:recitation:results:{session_id}"
            for wr in word_results:
                await self._redis.rpush(results_key, json.dumps(wr))
            await self._redis.expire(results_key, 86400)

            # --- Update session with final results ---
            now = datetime.now(timezone.utc).isoformat()
            await self._redis.hset(
                f"qari:recitation:session:{session_id}",
                mapping={
                    "status": "completed",
                    "total_words": str(result.get("total_words", len(word_results))),
                    "correct_words": str(result.get("correct_words", 0)),
                    "accuracy_pct": str(result.get("accuracy_pct", 0)),
                    "completed_at": now,
                },
            )

            # --- Publish final result ---
            await self._publish_progress(session_id, {
                "session_id": session_id,
                "status": "completed",
                "progress_pct": 100.0,
                "processed_words": len(word_results),
                "total_words": result.get("total_words", len(word_results)),
                "accuracy_pct": result.get("accuracy_pct", 0),
                "word_results": word_results,
            })

            # --- Acknowledge the message ---
            await self._redis.xack(self._stream, self._group, msg_id)

            logger.info(
                "worker.completed",
                msg_id=msg_id,
                session_id=session_id,
                words=len(word_results),
                accuracy=result.get("accuracy_pct", 0),
            )

        except Exception as exc:
            logger.error("worker.processing_error", msg_id=msg_id, session_id=session_id, error=str(exc))
            self._errors += 1

            # --- Mark session as failed ---
            await self._redis.hset(
                f"qari:recitation:session:{session_id}",
                mapping={
                    "status": "failed",
                    "error_message": str(exc)[:500],
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            # --- Publish failure ---
            await self._publish_progress(session_id, {
                "session_id": session_id,
                "status": "failed",
                "error_message": str(exc)[:500],
            })

            # --- Acknowledge to avoid reprocessing ---
            await self._redis.xack(self._stream, self._group, msg_id)

    async def _publish_progress(self, session_id: str, data: dict) -> None:
        """Publish a progress update to the session's Pub/Sub channel."""
        channel = settings.recitation_results_channel.format(session_id=session_id)
        try:
            await self._redis.publish(channel, json.dumps(data, default=str))
        except Exception as exc:
            logger.warning("worker.publish_failed", session_id=session_id, error=str(exc))


# ---------------------------------------------------------------------------
# Entry point for running the worker as a standalone process
# ---------------------------------------------------------------------------

async def run_worker() -> None:
    """Run the inference worker. Entry point for `python -m app.workers.inference_worker`."""
    worker = InferenceWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(run_worker())
