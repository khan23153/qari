"""Bounded native context recovery retains the ordinary low-latency window."""
import pytest
from app.services import streaming_session as ss
from tests.test_native_error_event_confirmation import session_with_substitution

@pytest.fixture
def session(monkeypatch):
 monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt');monkeypatch.setattr(ss.settings,'ml_use_stub',False);return session_with_substitution()

def test_ordinary_window_is_unchanged_without_unresolved_evidence(session):
 session._matcher._delegate._resolved_states=[]
 assert session._select_audio_window_start(40*16000,round(32.5*16000),early=False,force=False)==round(32.5*16000)

def test_recent_native_error_gets_bounded_grid_aligned_context(session):
 assert session._select_audio_window_start(round(20.3*16000),round(12.8*16000),early=False,force=False)==0

def test_stale_error_does_not_make_later_windows_expensive(session):
 assert session._select_audio_window_start(40*16000,round(32.5*16000),early=False,force=False)==round(32.5*16000)

def test_stop_uses_at_most_21_seconds_without_reference_text(session):
 assert session._select_audio_window_start(round(125.5335*16000),round(118.0335*16000),early=False,force=True)==105*16000

def test_short_recording_and_first_pass_preserve_pcm_bounds(session):
 assert session._select_audio_window_start(3*16000,0,early=False,force=True)==0
 assert session._select_audio_window_start(40*16000,round(32.5*16000),early=True,force=False)==round(32.5*16000)

def test_legacy_engine_context_is_unchanged(session,monkeypatch):
 monkeypatch.setattr(ss,'_live_asr_engine',lambda:'faster_whisper')
 assert session._select_audio_window_start(40*16000,round(32.5*16000),early=False,force=True)==round(32.5*16000)
