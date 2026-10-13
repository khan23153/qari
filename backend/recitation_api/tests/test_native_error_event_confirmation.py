"""A single timed native substitution cannot paint a falsely rejected word red."""
import pytest
from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher

@pytest.fixture(autouse=True)
def native_engine(monkeypatch):
 monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')

def session_with_substitution():
 s=ss.StreamingRecitationSession();ref=['بسم','الله','الرحمن','الرحيم'];s.reference_words=ref;s._is_stub=False;s._timed_evidence_seen=True
 d=StreamingMatcher(ref);s._matcher=main._ConservativeLiveMatcher(ref,delegate=d);s._matcher.max_live_words=4
 words=['بسم','الصمد','الرحمن','الرحيم'];s._matcher.evaluate(words,[.95]*4);s._matcher.evaluate(words,[.95]*4);s._hypothesis=words;s._hypothesis_confs=[.95]*4;s._hypothesis_timings=[(.1,.2),(.5,.7),(1.,1.1),(1.5,1.6)];s._pcm=bytearray(3*32000)
 return s

def native_view(s,end,words=None,confs=None):
 s._last_native_view=(0,round(end*16000),tuple(words or s._hypothesis),tuple(confs or [.95]*4),tuple(s._hypothesis_timings))
 s._confirm_timed_error_events()
 return s._diff_events(s._matcher._delegate._resolved_states)

def test_single_native_error_does_not_emit_confirmed_red():
 s=session_with_substitution();events=native_view(s,2.)
 assert not any(e['word_index']==1 for e in events)
 assert [e['word_index']for e in events]==[0,2,3]

def test_second_native_error_view_emits_one_red_and_preserves_cursor():
 s=session_with_substitution();before=s._matcher._cursor;native_view(s,2.);events=native_view(s,2.3)
 assert len(events)==1 and events[0]['word_index']==1 and events[0]['evidence_confirmed']is True
 assert s._matcher._cursor==before and not native_view(s,2.6)

def test_same_endpoint_is_not_a_second_error_witness():
 s=session_with_substitution();native_view(s,2.);assert not native_view(s,2.)

def test_corrected_or_weak_native_view_breaks_error_confirmation():
 for words,confs in [(['بسم','الله','الرحمن','الرحيم'],[.95]*4),(None,[.95,.2,.95,.95])]:
  s=session_with_substitution();native_view(s,2.);native_view(s,2.3,words,confs);events=native_view(s,2.6)
  assert not any(e['word_index']==1 for e in events)

def test_immature_native_error_views_cannot_confirm_red():
 s=session_with_substitution()
 for end in [2.,2.3]:
  spans=s._hypothesis_timings.copy();spans[1]=(.5,end-.01)
  s._last_native_view=(0,round(end*16000),tuple(s._hypothesis),(.95,)*4,tuple(spans));s._confirm_timed_error_events()
 events=s._diff_events(s._matcher._delegate._resolved_states)
 assert not any(e['word_index']==1 for e in events)
