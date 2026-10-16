"""Two actual native triples may recover a frozen gap at its original occurrence."""
import copy,json
from pathlib import Path
import pytest
from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher,WordState,WordStatus
DATA=json.loads((Path(__file__).parent/'fixtures/yasin_native_backfill.json').read_text())


def seeded(case):
    s=ss.StreamingRecitationSession();s._is_stub=False;s.reference_words=case['reference']
    d=StreamingMatcher(case['reference'],known_error_words=set(case['reference'])|{'لي'},word_aliases={'هذا':'هاذا'})
    s._matcher=main._ConservativeLiveMatcher(case['reference'],delegate=d);s._matcher.max_live_words=3
    d._resolved_states=[WordState(i,case['reference'][i],WordStatus(x['status']),x['spoken'],x['confidence'])for i,x in enumerate(case['states'])]
    d._resolved={x.index:x.status for x in d._resolved_states};d._live_hyp_indices={int(k):v for k,v in case['slots'].items()}
    d._cursor=s._matcher._cursor=3;d._hyp_cursor=s._matcher._hyp_cursor=max(d._live_hyp_indices.values())+1
    s._hypothesis=[x['word']for x in case['hypothesis']];s._hypothesis_confs=[x['score']for x in case['hypothesis']];s._hypothesis_timings=[tuple(x['time'])for x in case['hypothesis']];s._consumed_audio_end=case['consumed_end']
    s._last_status={x.index:x.status.value for x in d._resolved_states}
    return s


def view(s,row):
    s._pcm=bytearray(row['endpoint']*2)
    native=(round(row['start']*16000),row['endpoint'],tuple(row['words']),tuple(row['confidences']),tuple(map(tuple,row['timings'])))
    s._repair_anchored_native_words(native)
    s._last_native_view=native


@pytest.mark.parametrize('case',DATA['cases'],ids=lambda c:str(c['original_index']))
def test_captured_consecutive_views_reveal_only_the_original_unresolved_word(case,monkeypatch):
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')
    s=seeded(case);d=s._matcher._delegate
    original=(d._cursor,d._hyp_cursor,s._consumed_audio_end,s._hypothesis.copy(),dict(d._live_hyp_indices))
    view(s,case['views'][0]);assert d._resolved[1]!=WordStatus.MATCHED
    view(s,case['views'][1]);assert d._resolved[1]==WordStatus.MATCHED
    assert [(e['word_index'],e['status'])for e in s._diff_events(d._resolved_states)]==[(1,'match')]
    assert (d._cursor,d._hyp_cursor,s._consumed_audio_end,s._hypothesis,d._live_hyp_indices)==original
    state=d._resolved_states[1];assert state.confidence>=.55 and state.spoken
    assert s._native_word_repairs[1]['endpoints']==[case['views'][0]['endpoint'],case['views'][1]['endpoint']]


@pytest.mark.parametrize('kind',['weak_word','weak_anchor','same_endpoint','rereading','shared_frame','duplicate_triple','different_word','budget','missing_anchor','already_matched','nan','contradiction'])
def test_unproven_fresh_views_cannot_backfill_a_missing_word(kind,monkeypatch):
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')
    case=copy.deepcopy(next(c for c in DATA['cases']if c['original_index']==418));s=seeded(case);d=s._matcher._delegate
    if kind=='budget':s._matcher.max_live_words=1
    if kind=='missing_anchor':d._resolved_states[0].status=WordStatus.SKIPPED
    if kind=='already_matched':d._resolved_states[1].status=WordStatus.MATCHED;d._resolved[1]=WordStatus.MATCHED
    before=[(x.status,x.spoken,x.confidence)for x in d._resolved_states]
    rows=case['views']
    if kind=='same_endpoint':rows[1]=copy.deepcopy(rows[0])
    for n,r in enumerate(rows):
        i=r['words'].index('هذا')
        if kind=='weak_word':r['confidences'][i]=.2
        if kind=='weak_anchor':r['confidences'][i+1]=.2
        if kind=='nan':r['confidences'][i]=float('nan')
        if kind=='rereading':r['start']+=3;r['endpoint']+=48000
        if kind=='shared_frame':r['timings'][i]=r['timings'][i-1].copy()
        if kind=='duplicate_triple':
            for k in ['words','confidences','timings']:r[k][i-1:i-1]=copy.deepcopy(r[k][i-1:i+2])
        if kind=='different_word' or kind=='contradiction'and n==1:r['words'][i]='ذلك'
        view(s,r)
    assert [(x.status,x.spoken,x.confidence)for x in d._resolved_states]==before
    assert s._native_word_repairs=={}


@pytest.mark.parametrize('old_score',[.9,.2])
def test_nearby_rereading_cannot_erase_an_explicit_original_mistake(old_score):
    from ml.alignment.native_evidence import prove_native_word_repair
    words=('من','لي','ما','من','لك','ما');timings=tuple((v,v)for v in(0.,.08,.16,.32,.48,.56))
    scores=(old_score,.9,old_score,.9,.9,.9)
    previous=(0,32000,words,scores,timings);current=(0,46400,words,scores,timings)
    for left,right in [((0.,0.),(.16,.16)),((.32,.32),(.56,.56))]:
        assert prove_native_word_repair(previous,current,expected=('من','لك','ما'),
            before_span=left,after_span=right,identity=lambda word:word,threshold=.55,
            sample_rate=16000,total_samples=46400,right_context_seconds=.24)is None


@pytest.mark.parametrize('kind',['stub','oracle_policy','unconsumed_anchor','matched_source','repaired_source'])
def test_native_repair_requires_independent_consumed_and_unowned_audio(kind,monkeypatch):
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')
    case=copy.deepcopy(next(c for c in DATA['cases']if c['original_index']==418));s=seeded(case);d=s._matcher._delegate
    if kind=='stub':s._is_stub=True
    if kind=='oracle_policy':monkeypatch.setattr(ss,'EVIDENCE_POLICY','corroborated')
    if kind=='unconsumed_anchor':s._matcher._hyp_cursor=d._hyp_cursor=d._live_hyp_indices[2]
    if kind in {'matched_source','repaired_source'}:
        r=case['views'][1];i=r['words'].index('هذا');span=tuple(v+r['start']for v in r['timings'][i])
        s.reference_words.append('هاذا');s._matcher.reference.append('هاذا');d.reference.append('هاذا');s._matcher.max_live_words=4;d._cursor=s._matcher._cursor=4
        d._resolved_states.append(WordState(3,'هاذا',WordStatus.MATCHED,'هذا',.99));d._resolved[3]=WordStatus.MATCHED
        if kind=='matched_source':
            slot=len(s._hypothesis);s._hypothesis.append('هذا');s._hypothesis_confs.append(.99);s._hypothesis_timings.append(span);d._live_hyp_indices[3]=slot;d._hyp_cursor=s._matcher._hyp_cursor=slot+1
        else:s._native_word_repairs[3]={'word':'هذا','confidence':.99,'spans':(span,span,span)}
    for r in case['views']:view(s,r)
    assert d._resolved[1]==WordStatus.SKIPPED
    assert 1 not in s._native_word_repairs
