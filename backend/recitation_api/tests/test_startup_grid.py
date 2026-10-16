"""First-word scheduling must preserve the PCM grid and bounded retries."""
from types import SimpleNamespace

import pytest

from app.services import streaming_session as ss


@pytest.fixture
def session(monkeypatch):
    monkeypatch.setattr(ss, "EARLY_FIRST_PASS", False)
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    instance = ss.StreamingRecitationSession()
    instance._is_stub = False
    instance._matcher = SimpleNamespace(_cursor=0)
    return instance


def test_startup_checks_earlier_without_reference_progress(session):
    assert session._next_interval_sec() == pytest.approx(.6)


@pytest.mark.parametrize("used,next_target", [
    (134400, 144000), (144000, 158400), (144001, 158400),
    (158399, 158400), (288003, 302400),
])
def test_progress_restores_absolute_grid_with_irregular_samples(session, used, next_target):
    session._matcher._cursor = 3
    session._samples_at_last_transcribe = used
    interval = session._next_interval_sec()
    assert interval > 0
    assert used + session._next_interval_samples() == next_target
    assert session._samples_at_last_transcribe == used
    assert session._matcher._cursor == 3
    assert session._next_interval_sec() == interval


def test_audio_ready_uses_the_startup_threshold(session):
    session.add_audio(bytes(9599 * 2))
    assert not session._audio_ready.is_set()
    session.add_audio(bytes(2))
    assert session._audio_ready.is_set()


def test_whisper_and_stub_keep_existing_interval(session, monkeypatch):
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "faster_whisper")
    assert session._next_interval_sec() == ss.TRANSCRIBE_INTERVAL_SEC
    monkeypatch.setattr(ss, "_live_asr_engine", lambda: "fastconformer_rnnt")
    session._is_stub = True
    assert session._next_interval_sec() == ss.TRANSCRIBE_INTERVAL_SEC


def test_explicit_early_first_pass_stays_authoritative(session, monkeypatch):
    monkeypatch.setattr(ss, "EARLY_FIRST_PASS", True)
    assert session._next_interval_sec() == ss.EARLY_FIRST_PASS_SEC


def test_audio_ready_waits_for_exact_grid_sample(session):
    session._matcher._cursor = 3
    session._samples_at_last_transcribe = 158400 - 1001
    session._pcm = bytearray(session._samples_at_last_transcribe * 2)
    session.add_audio(bytes(1000 * 2))
    assert not session._audio_ready.is_set()
    session.add_audio(bytes(2))
    assert session._audio_ready.is_set()


@pytest.mark.asyncio
async def test_native_failure_keeps_bounded_retry_near_grid(session, monkeypatch):
    session._matcher._cursor = 3
    session._samples_at_last_transcribe = 158399
    session._pcm = bytearray(158400 * 2)
    delays = []

    async def fail_before_consumption():
        raise RuntimeError("controlled pre-consumption failure")

    async def record_sleep(delay):
        delays.append(delay)
        session._transcribe_stop = True

    monkeypatch.setattr(session, "maybe_transcribe", fail_before_consumption)
    monkeypatch.setattr(ss.asyncio, "sleep", record_sleep)
    await session._audio_driven_transcription_loop(SimpleNamespace())
    assert len(delays) == 1
    assert delays[0] >= ss.RNNT_TRANSCRIBE_INTERVAL_SEC
