"""WebSocket route for real-time recitation results."""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["websocket"])

_redis: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


@router.websocket("/ws/recitation/{session_id}")
async def recitation_websocket(websocket: WebSocket, session_id: str):
    """WebSocket for real-time recitation results.

    The client connects after uploading audio and receiving a session_id.
    The server:
    1. Validates the session exists in Redis.
    2. Subscribes to the session's Redis Pub/Sub channel.
    3. Forwards progress updates and word results to the client.
    4. Closes when the session reaches a terminal state (completed/failed).
    """
    await websocket.accept()
    r = _get_redis()

    # --- Validate session ---
    session_data = await r.hgetall(f"qari:recitation:session:{session_id}")
    if not session_data:
        await websocket.send_json({
            "type": "about:blank",
            "title": "Not Found",
            "status": 404,
            "detail": f"Recitation session '{session_id}' not found",
        })
        await websocket.close(code=4004)
        return

    current_status = session_data.get("status", "queued")

    # If already terminal, send final result and close
    if current_status in ("completed", "failed"):
        await _send_final_result(websocket, r, session_id, session_data)
        await websocket.close()
        return

    # --- Send initial status ---
    await websocket.send_json({
        "session_id": session_id,
        "status": current_status,
        "message": "Connected, waiting for inference results...",
    })

    # --- Subscribe to Redis Pub/Sub channel ---
    channel = settings.recitation_results_channel.format(session_id=session_id)
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)

    # --- Also poll session status as fallback ---
    try:
        while True:
            # Check for Pub/Sub messages
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)

                    # Check if terminal
                    if data.get("status") in ("completed", "failed"):
                        break
                except json.JSONDecodeError:
                    logger.warning("ws.invalid_message", session_id=session_id)

            # Fallback: poll session status
            session_data = await r.hgetall(f"qari:recitation:session:{session_id}")
            if session_data:
                new_status = session_data.get("status", "queued")
                if new_status in ("completed", "failed") and new_status != current_status:
                    await _send_final_result(websocket, r, session_id, session_data)
                    break
                current_status = new_status

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info("ws.disconnected", session_id=session_id)
    except Exception as exc:
        logger.error("ws.error", session_id=session_id, error=str(exc))
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        try:
            await websocket.close()
        except Exception:
            pass


async def _send_final_result(websocket: WebSocket, r: redis.Redis, session_id: str, session_data: dict) -> None:
    """Send the final result payload over WebSocket."""
    # Get all word results
    word_results_raw = await r.lrange(f"qari:recitation:results:{session_id}", 0, -1)
    word_results = []
    for raw in word_results_raw:
        try:
            word_results.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    final_payload = {
        "session_id": session_id,
        "status": session_data.get("status", "completed"),
        "total_words": int(session_data["total_words"]) if "total_words" in session_data else None,
        "correct_words": int(session_data["correct_words"]) if "correct_words" in session_data else None,
        "accuracy_pct": float(session_data["accuracy_pct"]) if "accuracy_pct" in session_data else None,
        "error_message": session_data.get("error_message"),
        "completed_at": session_data.get("completed_at"),
        "word_results": word_results,
    }
    await websocket.send_json(final_payload)
