"""Tests for the real-time streaming recitation WebSocket."""

import pytest
from fastapi.testclient import TestClient

import app.services.streaming_session as ss
from app.main import app


REFERENCE = ["بسم", "الله", "الرحمن", "الرحيم"]


@pytest.fixture
def stub_stream(monkeypatch):
    """Force stub transcriber + a fixed reference so the WS is model-free."""
    monkeypatch.setattr(
        ss, "resolve_reference_words",
        lambda surah, ayah: (REFERENCE, REFERENCE, "https://example/ref.mp3"),
    )
    monkeypatch.setattr(ss.settings, "ml_use_stub", True, raising=False)
    # Don't touch Redis in tests.
    async def _noop(self, result, audio_path):
        return None
    monkeypatch.setattr(ss.StreamingRecitationSession, "_persist", _noop)
    yield


def _pcm_seconds(seconds: float, sr: int = 16000) -> bytes:
    return b"\x00\x00" * int(seconds * sr)


def test_stream_handshake_sends_ready(stub_stream):
    client = TestClient(app)
    with client.websocket_connect("/ws/recitation/stream") as ws:
        ws.send_json({"type": "start", "surah_number": 1, "ayah_number": 1,
                      "mode": "memorization"})
        ready = ws.receive_json()
        assert ready["type"] == "ready"
        assert ready["word_count"] == 4
        assert [w["text"] for w in ready["words"]] == REFERENCE
        ws.send_json({"type": "stop"})
        # Drain until the final message.
        final = _recv_until(ws, "final")
        assert final["result"]["session_id"] == ready["session_id"]


def test_stream_reveals_words_live(stub_stream):
    """Streaming audio produces word 'matched' events as words are revealed."""
    client = TestClient(app)
    with client.websocket_connect("/ws/recitation/stream") as ws:
        ws.send_json({"type": "start", "surah_number": 1, "ayah_number": 1})
        ready = ws.receive_json()
        assert ready["type"] == "ready"

        # ~5s of audio → stub reveals min(4, floor(5/0.9)) = 4 words.
        ws.send_bytes(_pcm_seconds(5.0))

        matched = []
        # Collect the word events emitted for this chunk.
        for _ in range(4):
            evt = ws.receive_json()
            assert evt["type"] == "word"
            assert evt["status"] == "matched"
            matched.append(evt["word_index"])
        assert matched == [0, 1, 2, 3]

        ws.send_json({"type": "stop"})
        final = _recv_until(ws, "final")
        result = final["result"]
        assert result["accuracy_score"] == 1.0
        assert len(result["word_verdicts"]) == 4
        assert all(v["is_correct"] for v in result["word_verdicts"])


def test_stream_final_marks_unrecited_skipped(stub_stream):
    """Stopping early leaves un-recited words flagged (not falsely correct)."""
    client = TestClient(app)
    with client.websocket_connect("/ws/recitation/stream") as ws:
        ws.send_json({"type": "start", "surah_number": 1, "ayah_number": 1})
        ws.receive_json()  # ready
        ws.send_bytes(_pcm_seconds(1.6))  # ~1 word revealed
        # There may be a word event; drain then stop.
        ws.send_json({"type": "stop"})
        final = _recv_until(ws, "final")
        verdicts = final["result"]["word_verdicts"]
        assert len(verdicts) == 4
        skipped = [v for v in verdicts if v["error_type"] == "skipped"]
        assert len(skipped) >= 1


def test_stream_requires_start_first(stub_stream):
    client = TestClient(app)
    with client.websocket_connect("/ws/recitation/stream") as ws:
        ws.send_json({"type": "audio"})  # wrong first message
        msg = ws.receive_json()
        assert msg["type"] == "error"


def _recv_until(ws, msg_type, limit=50):
    for _ in range(limit):
        msg = ws.receive_json()
        if msg.get("type") == msg_type:
            return msg
    raise AssertionError(f"did not receive '{msg_type}' message")
