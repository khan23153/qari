"""A fresh native suffix may reuse independently confirmed live evidence."""
import json,copy
from pathlib import Path
import pytest
from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher,WordState,WordStatus
DATA=json.loads((Path(__file__).parent/'fixtures/complete_baqarah_native_evidence.json').read_text())

def complete_session(monkeypatch):
 monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt');monkeypatch.setattr(ss,'EVIDENCE_POLICY','tier2')
 s=ss.StreamingRecitationSession();s._is_stub=False;s.reference_words=DATA['reference'];s._pcm=bytearray(DATA['total_samples']*2);s._timed_evidence_seen=True
 d=StreamingMatcher(s.reference_words);s._matcher=main._ConservativeLiveMatcher(s.reference_words,delegate=d);s._matcher.max_live_words=59
 s._hypothesis=DATA['hypothesis'].copy();s._hypothesis_confs=DATA['confidences'].copy();s._hypothesis_timings=list(map(tuple,DATA['timings']));d._live_hyp_indices={int(k):v for k,v in DATA['slots'].items()};d._cursor=s._matcher._cursor=DATA['cursor'];d._hyp_cursor=s._matcher._hyp_cursor=len(s._hypothesis)
 d._resolved_states=[WordState(i,s.reference_words[i],WordStatus.MATCHED,s._hypothesis[slot],s._hypothesis_confs[slot])for i,slot in d._live_hyp_indices.items()];d._resolved={x.index:x.status for x in d._resolved_states};s._last_native_view=copy.deepcopy(DATA['last_native_view']);return s

def test_captured_complete_evidence_qualifies_without_stitched_final_transcript(monkeypatch):
 s=complete_session(monkeypatch);assert s._native_final_evidence_complete()

@pytest.mark.parametrize('kind',['stale_pcm','missing_view','weak_tail','wrong_tail','extra_tail','missing_map','duplicate_map','skipped','error','weak_live','nan_live','wrong_spoken','pending_revision'])
def test_uncertain_evidence_requires_original_full_recording_review(monkeypatch,kind):
 s=complete_session(monkeypatch);d=s._matcher._delegate
 if kind=='stale_pcm':s._pcm.extend(b'\0\0')
 if kind=='missing_view':s._last_native_view=None
 if kind=='weak_tail':s._last_native_view[3][-1]=.2
 if kind=='wrong_tail':s._last_native_view[2][-1]='عظيم'
 if kind=='extra_tail':
  s._last_native_view[2].append('عظيم');s._last_native_view[3].append(.99);s._last_native_view[4].append([20.,20.])
 if kind=='missing_map':d._live_hyp_indices.pop(13)
 if kind=='duplicate_map':d._live_hyp_indices[13]=d._live_hyp_indices[12]
 if kind in {'skipped','error'}:d._resolved_states[13].status=WordStatus.SKIPPED if kind=='skipped'else WordStatus.ERROR
 if kind=='weak_live':d._resolved_states[13].confidence=.2
 if kind=='nan_live':d._resolved_states[13].confidence=float('nan')
 if kind=='wrong_spoken':d._resolved_states[13].spoken='الصمد'
 if kind=='pending_revision':s._pending_gap_revisions[13]=(1,1.,1,1,())
 assert not s._native_final_evidence_complete()

@pytest.mark.asyncio
async def test_finalization_reuses_native_witnesses_without_calling_full_asr(monkeypatch):
 s=complete_session(monkeypatch);s._pcm=bytearray(b'\x00\x20'*DATA['total_samples']);calls=[]
 def forbidden(*args):
  calls.append(len(args[0]));raise AssertionError('Redundant full ASR must not run')
 monkeypatch.setattr(ss,'_independent_transcriber',forbidden)
 async def noop(*args):pass
 s._persist=noop;s._write_wav=lambda:None
 final=await main._original_stream_finalize(s)
 assert calls==[]
 assert [v['word_index']for v in final['word_verdicts']if v['is_correct']]==list(range(56))
 assert all(v['word_index']<56 for v in final['word_verdicts'])

def test_suffix_text_at_unrelated_audio_frames_cannot_certify_final(monkeypatch):
 s=complete_session(monkeypatch);s._last_native_view[4]=[[i*.08,i*.08]for i in range(len(s._last_native_view[2]))]
 assert not s._native_final_evidence_complete()

def test_extra_reference_word_from_an_older_occurrence_requires_full_review(monkeypatch):
 s=complete_session(monkeypatch)
 s._last_native_view[2].insert(0,s.reference_words[44]);s._last_native_view[3].insert(0,.99);s._last_native_view[4].insert(0,[0.,0.])
 assert not s._native_final_evidence_complete()
