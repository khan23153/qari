import json
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes import websocket as route
from tests.support import auth_headers, OWNER_ID, OTHER_ID


def test_diagnostics_accepts_only_bounded_capture_values():
    result = route.normalize_capture_diagnostics({
        'app_version': '1.0.49', 'app_build': 76, 'capture_rate': 44100,
        'audio_source': 'MIC', 'software_gain': 3, 'resampling': True,
        'dropped_frames': 2, 'access_token': 'private-token', 'status': 'completed',
    })
    assert result == {'app_version': '1.0.49', 'app_build': 76, 'capture_rate': 44100,
        'audio_source': 'MIC', 'software_gain': 3, 'resampling': True, 'dropped_frames': 2}


def test_invalid_capture_values_cannot_be_logged():
    assert route.normalize_capture_diagnostics({
        'app_version': 'Bearer private-token', 'app_build': True, 'capture_rate': -1,
        'audio_source': 'unknown-private-text', 'software_gain': '3',
        'resampling': 'true', 'dropped_frames': 10000001,
    }) == {}
    for value in [None, [], 'private-token']:
        assert route.normalize_capture_diagnostics(value) == {}


def test_authenticated_capture_details_persist_without_changing_owner_or_words(recitation_storage, monkeypatch):
    import app.services.streaming_session as ss
    monkeypatch.setattr(ss.settings, 'ml_use_stub', True)
    monkeypatch.setattr(ss, 'resolve_reference_words_sequence', lambda refs: ([], [], '', [], []))
    with TestClient(app).websocket_connect('/ws/recitation/stream', headers=auth_headers()) as ws:
        ws.send_json({'type': 'start', 'surah_number': 1, 'words': ['بسم'],
            'client_info': {'app_version': '1.0.49', 'app_build': 76, 'access_token': 'never-store'}})
        ready = ws.receive_json()
        assert ready['type'] == 'ready' and ready['word_count'] == 1
        sid = ready['session_id']
        ws.send_json({'type': 'capture_diagnostics', 'audio_source': 'MIC', 'capture_rate': 44100,
            'resampling': True, 'software_gain': 3, 'dropped_frames': 2,
            'user_id': OTHER_ID, 'session_id': 'another-session', 'status': 'completed'})
        ws.send_json({'type': 'ping'})
        assert ws.receive_json() == {'type': 'pong'}
        meta = recitation_storage.hashes['qari:recitation:session:'+sid]
        assert meta['user_id'] == OWNER_ID and meta['status'] == 'processing'
        assert json.loads(meta['capture_diagnostics']) == {
            'app_version': '1.0.49', 'app_build': 76, 'audio_source': 'MIC', 'capture_rate': 44100,
            'resampling': True, 'software_gain': 3, 'dropped_frames': 2}
        ws.send_json({'type': 'stop'})
        assert ws.receive_json()['type'] == 'final'
    assert json.loads(meta['capture_diagnostics'])['audio_source'] == 'MIC'


def test_stalled_optional_diagnostics_cannot_block_audio_and_ping(recitation_storage, monkeypatch):
    import asyncio
    import wave
    import app.services.streaming_session as ss
    from app.core.config import settings
    from pathlib import Path
    original = recitation_storage.hset
    state = {'cancelled': False}
    async def stalled(key, mapping):
        if set(mapping) == {'capture_diagnostics'}:
            try:
                await asyncio.sleep(.5)
            except asyncio.CancelledError:
                state['cancelled'] = True
                raise
        return await original(key, mapping=mapping)
    monkeypatch.setattr(recitation_storage, 'hset', stalled)
    monkeypatch.setattr(ss.settings, 'ml_use_stub', True)
    monkeypatch.setattr(ss, 'resolve_reference_words_sequence', lambda refs: ([], [], '', [], []))
    with TestClient(app).websocket_connect('/ws/recitation/stream', headers=auth_headers()) as ws:
        ws.send_json({'type': 'start', 'surah_number': 1, 'words': ['بسم']})
        ready = ws.receive_json()
        ws.send_json({'type': 'capture_diagnostics', 'audio_source': 'MIC'})
        pcm = bytes(3200)
        ws.send_bytes(pcm)
        ws.send_json({'type': 'ping'})
        assert ws.receive_json() == {'type': 'pong'}
        assert state['cancelled'] is True
        ws.send_json({'type': 'stop'})
        assert ws.receive_json()['type'] == 'final'
    with wave.open(str(Path(settings.audio_storage_path)/ready['session_id']/'audio.wav'), 'rb') as w:
        assert w.readframes(w.getnframes()) == pcm
