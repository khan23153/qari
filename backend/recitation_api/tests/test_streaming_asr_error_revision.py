"""Captured independent ASR corrections must not replay consumed speech."""
import copy,json
from pathlib import Path
import pytest
from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher,WordStatus
DATA=json.loads((Path(__file__).parent/'fixtures/timed_yakun_revision.json').read_text())

def session_with_error():
 s=ss.StreamingRecitationSession();s.reference_words=DATA['reference'];s.reference_text_with_tashkeel_words=list(s.reference_words);s.ayah_boundaries=[];s._is_stub=False
 d=StreamingMatcher(s.reference_words,known_error_words=set(s.reference_words)|{'يقل'})
 s._matcher=main._ConservativeLiveMatcher(s.reference_words,delegate=d);s._matcher.max_live_words=15
 for row in DATA['seed']:s._matcher.evaluate(row['words'],row['confidences'])
 row=DATA['seed'][-1];s._hypothesis=list(row['words']);s._hypothesis_confs=list(row['confidences']);s._hypothesis_timings=list(map(tuple,row['timings']));s._consumed_audio_end=DATA['consumed_end']
 s._last_status={x.index:x.status.value for x in d._resolved_states}
 assert next(x for x in d._resolved_states if x.index==11).status==WordStatus.ERROR
 return s

def view(s,row):
 s._pcm=bytearray(row['endpoint_samples']*2)
 s._revise_supported_timed_errors(row['words'],row['confidences'],row['timings'],window_start=row['window_start'],window_seconds=row['window_seconds'],right_context_seconds=.24,endpoint_samples=row['endpoint_samples'])

def test_captured_two_views_correct_only_old_error_without_extra_progress():
 s=session_with_error();d=s._matcher._delegate;before=(s._matcher._cursor,s._matcher._hyp_cursor,d._cursor,d._hyp_cursor,s._consumed_audio_end,len(s._hypothesis),len(d._resolved_states))
 view(s,DATA['views'][0]);assert d._resolved[11]==WordStatus.ERROR
 view(s,DATA['views'][1]);states=s._matcher.evaluate(s._hypothesis,s._hypothesis_confs);events=s._diff_events(states)
 assert [(e['word_index'],e['status'])for e in events]==[(11,'match')]
 assert s._hypothesis[15]=='يكن' and s._hypothesis_confs[15]==DATA['views'][1]['confidences'][DATA['views'][1]['words'].index('يكن')]
 assert (s._matcher._cursor,s._matcher._hyp_cursor,d._cursor,d._hyp_cursor,s._consumed_audio_end,len(s._hypothesis),len(d._resolved_states))==before
 assert not s._diff_events(states)

def test_identical_pcm_endpoint_never_counts_as_two_views():
 s=session_with_error();view(s,DATA['views'][0]);view(s,DATA['views'][0]);assert s._matcher._delegate._resolved[11]==WordStatus.ERROR

def test_later_rereading_cannot_correct_an_earlier_mistake():
 s=session_with_error()
 for original in DATA['views']:
  r=copy.deepcopy(original);r['window_start']+=3;r['endpoint_samples']+=48000;view(s,r)
 assert s._matcher._delegate._resolved[11]==WordStatus.ERROR

@pytest.mark.parametrize('kind',['weak_word','nan_word','weak_anchor','missing_anchor','duplicate_word','no_provenance','no_anchor_state','beyond_budget','already_matched','skipped'])
def test_uncertain_or_unresolved_revision_cannot_change_live_state(kind):
 s=session_with_error();d=s._matcher._delegate;target=next(x for x in d._resolved_states if x.index==11)
 if kind=='no_provenance':d._live_hyp_indices.pop(11)
 if kind=='no_anchor_state':next(x for x in d._resolved_states if x.index==12).status=WordStatus.SKIPPED
 if kind=='beyond_budget':s._matcher.max_live_words=11
 if kind in {'already_matched','skipped'}:
  target.status=WordStatus.MATCHED if kind=='already_matched'else WordStatus.SKIPPED;d._resolved[11]=target.status
 before=(target.status,target.spoken,target.confidence,list(s._hypothesis))
 for original in DATA['views']:
  r=copy.deepcopy(original);i=r['words'].index('يكن')
  if kind=='weak_word':r['confidences'][i]=.2
  if kind=='nan_word':r['confidences'][i]=float('nan')
  if kind=='weak_anchor':r['confidences'][i+1]=.2
  if kind=='missing_anchor':
   for key in ['words','confidences','timings']:r[key].pop(i+1)
  if kind=='duplicate_word':
   for key in ['words','confidences','timings']:r[key].insert(i,copy.deepcopy(r[key][i]))
  view(s,r)
 assert (target.status,target.spoken,target.confidence,s._hypothesis)==before


def test_contradictory_view_resets_pending_confirmation():
 s=session_with_error();view(s,DATA['views'][0]);bad=copy.deepcopy(DATA['views'][0]);bad['words'][bad['words'].index('يكن')]='يقل';bad['endpoint_samples']+=3200;bad['window_seconds']+=.2;view(s,bad);view(s,DATA['views'][1])
 assert s._matcher._delegate._resolved[11]==WordStatus.ERROR


def test_immature_anchor_does_not_count_as_a_valid_first_view():
 s=session_with_error();s._hypothesis_timings=[(a+1,b+1)for a,b in s._hypothesis_timings];s._consumed_audio_end+=1
 for original in DATA['views']:
  r=copy.deepcopy(original);i=r['words'].index('يكن')
  for j in [i,i+1]:r['timings'][j]=[v+1 for v in r['timings'][j]]
  for key in ['words','confidences','timings']:r[key]=r[key][:i+2]
  view(s,r)
 assert s._matcher._delegate._resolved[11]==WordStatus.ERROR


def test_skipped_huwa_cannot_be_fabricated_by_error_revision():
 s=ss.StreamingRecitationSession();ref=['قل','هو','الله','احد'];d=StreamingMatcher(ref,known_error_words=set(ref));s._matcher=main._ConservativeLiveMatcher(ref,delegate=d);s._matcher.max_live_words=4
 s._hypothesis=['قل','الله','احد'];s._hypothesis_confs=[.95]*3;s._hypothesis_timings=[(.1,.3),(.8,1.1),(1.6,1.9)];s._consumed_audio_end=1.9
 s._matcher.evaluate(s._hypothesis,s._hypothesis_confs);assert d._resolved[1]==WordStatus.SKIPPED
 for end in [2.7,3.3]:view(s,{'words':ref,'confidences':[.99]*4,'timings':[(.1,.3),(.55,.7),(.8,1.1),(1.6,1.9)],'window_start':0,'window_seconds':end,'endpoint_samples':round(end*16000)})
 assert d._resolved[1]==WordStatus.SKIPPED and s._hypothesis==['قل','الله','احد']


def test_later_received_pcm_does_not_change_the_native_snapshot_endpoint():
 s=session_with_error()
 for r in DATA['views']:
  s._pcm=bytearray((r['endpoint_samples']+3200)*2)
  s._revise_supported_timed_errors(r['words'],r['confidences'],r['timings'],window_start=r['window_start'],window_seconds=r['window_seconds'],right_context_seconds=.24,endpoint_samples=r['endpoint_samples'])
 assert s._matcher._delegate._resolved[11]==WordStatus.MATCHED


@pytest.mark.asyncio
@pytest.mark.parametrize('interruption',['empty','timeless','invalid','failure'])
async def test_unusable_native_view_breaks_confirmation_in_actual_decode_path(monkeypatch,interruption):
 from ml.inference.transcript import TimedTranscript
 from tests.test_streaming import _pcm_seconds
 s=session_with_error();s._qari_active_speech_seconds=6.;s._samples_at_last_transcribe=round(18.6*16000);s._transcriber=lambda *_:([],[])
 first,last=DATA['views'];good=lambda r:TimedTranscript(r['words'],r['confidences'],r['timings'])
 bad=([],[])
 if interruption=='timeless':bad=(first['words'],first['confidences'])
 if interruption=='invalid':
  times=copy.deepcopy(first['timings']);times[0]=[8.,8.1];bad=TimedTranscript(first['words'],first['confidences'],times)
 if interruption=='failure':bad=RuntimeError('controlled native failure')
 replies=iter([good(first),bad,good(last)])
 def recognize(*_):
  result=next(replies)
  if isinstance(result,Exception):raise result
  return result
 monkeypatch.setattr(ss,'_independent_transcriber',recognize);monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt');monkeypatch.setattr(ss,'EVIDENCE_POLICY','tier2')
 events=[]
 for end in [19.2,19.5,19.8]:
  s._pcm=bytearray(_pcm_seconds(end));events.extend(await s.maybe_transcribe(force=True))
 assert s._matcher._delegate._resolved[11]==WordStatus.ERROR
 assert not any(e['word_index']==11 and e['status']=='match'for e in events)
 assert s._pending_error_revisions[11][2]==1
