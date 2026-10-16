"""Every RNNT view must share the encoder's original 80ms PCM frame origin."""
import pytest
from app.services import streaming_session as ss
from tests.test_native_error_event_confirmation import session_with_substitution


@pytest.fixture
def session(monkeypatch):
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')
    monkeypatch.setattr(ss.settings,'ml_use_stub',False)
    return session_with_substitution()


@pytest.mark.parametrize('end',[30.6,31.5,32.4,33.3,34.2,125.5335])
def test_ordinary_views_keep_one_encoder_phase_with_less_than_one_extra_frame(session,end):
    session._matcher._delegate._resolved_states=[]
    total=round(end*16000);default=max(0,total-120000)
    start=session._select_audio_window_start(total,default,early=False,force=False)
    assert start%1280==0
    assert 0<=default-start<1280


@pytest.mark.parametrize('end',[20.3,21.2,22.1,125.5335])
def test_recovery_views_keep_the_same_phase_and_at_most_one_extra_frame(session,end):
    total=round(end*16000)
    start=session._select_audio_window_start(total,max(0,total-120000),early=False,force=True)
    assert start%1280==0
    assert 0<=start<=total
    assert min(20.,end)<= (total-start)/16000 <20.08+1e-6


def test_legacy_and_explicit_test_decoders_do_not_get_rnnt_frame_rules(session,monkeypatch):
    default=round(32.5*16000)
    session._explicit_transcriber=lambda *_:([],[])
    assert session._select_audio_window_start(40*16000,default,early=False,force=True)==default
    session._explicit_transcriber=None
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'faster_whisper')
    assert session._select_audio_window_start(40*16000,default,early=False,force=True)==default
