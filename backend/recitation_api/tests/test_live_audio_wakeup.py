"""Fresh PCM and stop signals must wake the real production live worker."""
import asyncio
from contextlib import suppress
import threading
from types import SimpleNamespace

import pytest

from app import main
from app.services import streaming_session as ss
from ml.inference import fastconformer_transcriber as rnnt
from ml.inference.transcript import TimedTranscript
from tests.test_streaming import _pcm_seconds


@pytest.fixture
def session(monkeypatch):
    words = ['قل', 'هو', 'الله', 'احد']
    entries = [{'text_with_tashkeel': w, 'clean_text': w} for w in words]
    monkeypatch.setenv('QARI_LIVE_ASR_ENGINE', 'fastconformer_rnnt')
    monkeypatch.setattr(ss.settings, 'ml_use_stub', False)
    monkeypatch.setattr(ss, 'EVIDENCE_POLICY', 'tier2')
    monkeypatch.setattr(ss, 'resolve_reference_words_sequence', lambda _: (words, words, '', entries, []))
    monkeypatch.setattr(ss, '_get_live_error_vocabulary', lambda: frozenset(words))
    monkeypatch.setattr(ss, '_get_live_word_aliases', lambda: {})
    monkeypatch.setattr(rnnt, 'get_transcriber', lambda: SimpleNamespace(load=lambda: None))
    result = ss.StreamingRecitationSession(surah=112, ayah_to=1)
    result.load_reference()
    assert isinstance(result._matcher, main._ConservativeLiveMatcher)
    return result


@pytest.mark.asyncio
async def test_enough_new_pcm_wakes_the_worker_without_waiting_for_a_poll_tick(session, monkeypatch):
    monkeypatch.setattr(ss, '_independent_transcriber', lambda *_:
                        TimedTranscript(['قل'], [.95], [(.08, .16)]))
    events = asyncio.Queue()
    task = asyncio.create_task(session.transcription_loop(SimpleNamespace(send_json=events.put)))
    try:
        await asyncio.sleep(.01)
        session.add_audio(_pcm_seconds(.9))
        event = await asyncio.wait_for(events.get(), .15)
        assert (event['word_index'], event['status']) == (0, 'match')
        await session.stop_transcription()
        done, _ = await asyncio.wait({task}, timeout=.15)
        assert task in done
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_stop_wakes_an_idle_worker_without_revealing_silence(session):
    events = asyncio.Queue()
    task = asyncio.create_task(session.transcription_loop(SimpleNamespace(send_json=events.put)))
    try:
        await asyncio.sleep(.01)
        await session.stop_transcription()
        done, _ = await asyncio.wait({task}, timeout=.15)
        assert task in done
        assert events.empty()
        assert session._matcher._cursor == 0
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_stop_requested_before_worker_start_is_preserved(session):
    events = asyncio.Queue()
    await session.stop_transcription()
    task = asyncio.create_task(session.transcription_loop(SimpleNamespace(send_json=events.put)))
    try:
        done, _ = await asyncio.wait({task}, timeout=.15)
        assert task in done
        assert events.empty()
        assert session._pass_count == 0
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_audio_received_during_decode_is_processed_after_that_decode_finishes(session, monkeypatch):
    started = threading.Event()
    release = threading.Event()
    calls = 0

    def decode(*_):
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            assert release.wait(2)
            return TimedTranscript(['قل'], [.95], [(.08, .16)])
        return TimedTranscript(['قل', 'هو'], [.95, .95], [(.08, .16), (1.12, 1.36)])

    monkeypatch.setattr(ss, '_independent_transcriber', decode)
    events = asyncio.Queue()
    session.add_audio(_pcm_seconds(.9))
    task = asyncio.create_task(session.transcription_loop(SimpleNamespace(send_json=events.put)))
    try:
        assert await asyncio.to_thread(started.wait, .5)
        session.add_audio(_pcm_seconds(.9))
        release.set()
        first = await asyncio.wait_for(events.get(), .15)
        second = await asyncio.wait_for(events.get(), .15)
        assert [(first['word_index'], first['status']), (second['word_index'], second['status'])] == [
            (0, 'match'), (1, 'match'),
        ]
        await session.stop_transcription()
        done, _ = await asyncio.wait({task}, timeout=.15)
        assert task in done
    finally:
        release.set()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
