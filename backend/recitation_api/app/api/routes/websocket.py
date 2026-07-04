"""WebSocket endpoint for real-time recitation results (Phase 3 ready)."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as redis
import json

from app.core.config import settings

router = APIRouter()
_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.websocket("/ws/recitation/{session_id}")
async def ws_recitation(websocket: WebSocket, session_id: str):
    """WebSocket that pushes recitation results when inference completes.

    Phase 1: client polls REST, this WS is optional.
    Phase 3: server pushes per-word verdicts in real-time.
    """
    await websocket.accept()
    try:
        # Subscribe to result channel
        pubsub = _redis.pubsub()
        await pubsub.subscribe(f"recitation:ws:{session_id}")

        # Also check if result is already ready
        existing = await _redis.get(f"recitation:result:{session_id}")
        if existing:
            await websocket.send_text(existing)
            await websocket.close()
            return

        # Wait for result via pubsub
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
                await websocket.close()
                break
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"recitation:ws:{session_id}")
