"""Captured native evidence may repair one previously unresolved timed gap."""
import copy,json
from pathlib import Path
import pytest
from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher,WordState,WordStatus
DATA=json.loads((Path(__file__).parent/'fixtures/timed_skipped_gap.json').read_text())

def session_with_gap():
 s=ss.StreamingRecitationSession();s._is_stub=False;s.reference_words=DATA['reference'];s.reference_text_with_tashkeel_words=list(s.reference_words)
 d=StreamingMatcher(s.reference_words);s._matcher=main._ConservativeLiveMatcher(s.reference_words,delegate=d);s._matcher.max_live_words=59
 row=DATA['seed'];d._resolved_states=[WordState(x['index'],s.reference_words[x['index']],WordStatus(x['status']),x['spoken'],x['confidence'])for x in row['resolved_states']];d._resolved={x.index:x.status for x in d._resolved_states};d._live_hyp_indices={int(k):v for k,v in row['live_hyp_indices'].items()};d._cursor=s._matcher._cursor=row['cursor'];d._hyp_cursor=s._matcher._hyp_cursor=max(d._live_hyp_indices.values())+1
 s._hypothesis=row['hypothesis'].copy();s._hypothesis_confs=row['confidences'].copy();s._hypothesis_timings=list(map(tuple,row['timings']));s._consumed_audio_end=s._hypothesis_timings[d._hyp_cursor-1][1];s._last_status={x.index:x.status.value for x in d._resolved_states}
 return s

def view(s,row):
 s._pcm=bytearray(row['endpoint_samples']*2)
 s._revise_supported_timed_gaps(row['words'],row['confidences'],row['timings'],window_start=row['window_start'],window_seconds=row['window_seconds'],right_context_seconds=.24,endpoint_samples=row['endpoint_samples'])

def test_two_actual_views_repair_only_the_existing_timed_placeholder():
 s=session_with_gap();d=s._matcher._delegate;before=(d._cursor,d._hyp_cursor,s._consumed_audio_end,len(s._hypothesis),len(d._resolved_states))
 view(s,DATA['views'][0]);assert d._resolved[47]==WordStatus.SKIPPED
 view(s,DATA['views'][1]);assert d._resolved[47]==WordStatus.MATCHED
 assert d._live_hyp_indices[47]==55 and s._hypothesis[55]=='خطم'
 assert s._hypothesis_confs[55]==DATA['views'][1]['confidences'][DATA['views'][1]['words'].index('خطم')]
 assert (d._cursor,d._hyp_cursor,s._consumed_audio_end,len(s._hypothesis),len(d._resolved_states))==before
 assert [(e['word_index'],e['status'])for e in s._diff_events(d._resolved_states)]==[(47,'match')]

@pytest.mark.parametrize('kind',['weak_word','weak_anchor','duplicate','owned_slot','no_placeholder','beyond_budget','rereading','nan','no_anchor','ambiguous_anchor'])
def test_unproven_gap_cannot_be_revealed(kind):
 s=session_with_gap();d=s._matcher._delegate
 if kind=='owned_slot':d._live_hyp_indices[30]=55
 if kind=='no_placeholder':d._live_hyp_indices[48]=55
 if kind=='beyond_budget':s._matcher.max_live_words=47
 if kind=='no_anchor':next(x for x in d._resolved_states if x.index==46).status=WordStatus.SKIPPED
 before=(s._hypothesis.copy(),dict(d._live_hyp_indices))
 for original in DATA['views']:
  row=copy.deepcopy(original);i=next(i for i,w in enumerate(row['words'])if w in {'ختم','خطم'})
  if kind=='weak_word':row['confidences'][i]=.2
  if kind=='weak_anchor':row['confidences'][i+1]=.2
  if kind=='nan':row['confidences'][i]=float('nan')
  if kind=='rereading':row['window_start']+=3;row['endpoint_samples']+=48000
  if kind in {'duplicate','ambiguous_anchor'}:
   j=i if kind=='duplicate'else i+1
   for key in ['words','confidences','timings']:row[key].insert(j,copy.deepcopy(row[key][j]))
  view(s,row)
 assert d._resolved[47]==WordStatus.SKIPPED and (s._hypothesis,d._live_hyp_indices)==before

def test_same_pcm_endpoint_cannot_confirm_gap_twice():
 s=session_with_gap();view(s,DATA['views'][0]);view(s,DATA['views'][0]);assert s._matcher._delegate._resolved[47]==WordStatus.SKIPPED

def test_contradictory_view_breaks_gap_confirmation():
 s=session_with_gap();view(s,DATA['views'][0]);row=copy.deepcopy(DATA['views'][0]);row['words'][row['words'].index('ختم')]='قال';row['endpoint_samples']+=3200;row['window_seconds']+=.2;view(s,row);view(s,DATA['views'][1]);assert s._matcher._delegate._resolved[47]==WordStatus.SKIPPED

@pytest.mark.asyncio
@pytest.mark.parametrize('interruption',['empty','timeless','invalid','failure'])
async def test_unusable_native_view_resets_gap_proof_in_real_decode(monkeypatch,interruption):
 from ml.inference.transcript import TimedTranscript
 from tests.test_streaming import _pcm_seconds
 # These captured views belong to their original PCM windows; test failure
 # recovery independently of the separately tested context selection policy.
 monkeypatch.setattr(ss.StreamingRecitationSession,'_select_audio_window_start',lambda self,total,default_start,**kwargs:default_start)
 s=session_with_gap();s._qari_active_speech_seconds=50.;s._samples_at_last_transcribe=round(113.4*16000);s._transcriber=lambda *_:([],[])
 first,last=DATA['views'];good=lambda r:TimedTranscript(r['words'],r['confidences'],r['timings']);bad=([],[])
 if interruption=='timeless':bad=(first['words'],first['confidences'])
 if interruption=='invalid':
  times=copy.deepcopy(first['timings']);times[0]=[21.,21.1];bad=TimedTranscript(first['words'],first['confidences'],times)
 if interruption=='failure':bad=RuntimeError('controlled native failure')
 replies=iter([good(first),bad,good(last)])
 def recognize(*_):
  result=next(replies)
  if isinstance(result,Exception):raise result
  return result
 monkeypatch.setattr(ss,'_independent_transcriber',recognize);monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt');monkeypatch.setattr(ss,'EVIDENCE_POLICY','tier2');monkeypatch.setattr(ss,'TRANSCRIBE_WINDOW_SEC',18.5)
 for end in [114.3,114.6,115.2]:
  s._pcm=bytearray(_pcm_seconds(end));await s.maybe_transcribe(force=True)
 assert s._matcher._delegate._resolved[47]==WordStatus.SKIPPED
 assert s._pending_gap_revisions[47][3]==1

@pytest.mark.parametrize('kind',['cross_frozen_anchor','shared_frozen_frame'])
def test_native_revision_must_fit_the_retained_frozen_neighbors(kind):
 s=session_with_gap();d=s._matcher._delegate
 if kind=='shared_frozen_frame':s._hypothesis_timings[54]=(s._hypothesis_timings[55][0],s._hypothesis_timings[55][0])
 for original in DATA['views']:
  row=copy.deepcopy(original);i=next(i for i,w in enumerate(row['words'])if w in {'ختم','خطم'})
  if kind=='cross_frozen_anchor':row['timings'][i][1]=row['timings'][i+1][0]+.04
  else:row['timings'][i-1]=[s._hypothesis_timings[55][0]-.2-row['window_start']]*2
  view(s,row)
 assert d._resolved[47]==WordStatus.SKIPPED

def test_context_emission_drift_requires_two_agreeing_native_witnesses():
 s=session_with_gap();s._hypothesis_timings[55]=(s._hypothesis_timings[55][0]+.1,s._hypothesis_timings[55][1])
 for row in DATA['views']:view(s,row)
 assert s._matcher._delegate._resolved[47]==WordStatus.MATCHED

def test_candidate_views_cannot_disagree_across_the_wider_frozen_tolerance():
 s=session_with_gap();first=copy.deepcopy(DATA['views'][0]);i=first['words'].index('ختم');first['timings'][i]=[v+.22 for v in first['timings'][i]]
 view(s,first);view(s,DATA['views'][1]);assert s._matcher._delegate._resolved[47]==WordStatus.SKIPPED

def test_ambiguous_frozen_placeholder_frame_has_no_unique_occurrence():
 s=session_with_gap();s._hypothesis_timings[53]=s._hypothesis_timings[55]
 for row in DATA['views']:view(s,row)
 assert s._matcher._delegate._resolved[47]==WordStatus.SKIPPED
