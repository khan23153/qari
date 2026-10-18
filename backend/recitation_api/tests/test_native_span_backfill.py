"""Adjacent unresolved words need complete same-occurrence native provenance."""
import copy
import pytest
from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher, WordState, WordStatus


def seeded():
    words=['الدين','اياك','نعبد','واياك']
    s=ss.StreamingRecitationSession();s._is_stub=False;s.reference_words=words
    d=StreamingMatcher(words,strict_word_identity=True,known_error_words=set(words)|{'غير','الناس'})
    s._matcher=main._ConservativeLiveMatcher(words,delegate=d);s._matcher.max_live_words=4
    d._resolved_states=[WordState(0,words[0],WordStatus.MATCHED,words[0],.95),
                        WordState(1,words[1],WordStatus.SKIPPED,'',0),
                        WordState(2,words[2],WordStatus.SKIPPED,'',0),
                        WordState(3,words[3],WordStatus.MATCHED,words[3],.96)]
    d._resolved={x.index:x.status for x in d._resolved_states};d._live_hyp_indices={0:0,3:3}
    d._cursor=s._matcher._cursor=4;d._hyp_cursor=s._matcher._hyp_cursor=4
    s._hypothesis=[words[0],'غير','الناس',words[3]];s._hypothesis_confs=[.95,.8,.8,.96]
    s._hypothesis_timings=[(0.,0.),(1.,1.),(2.,2.),(3.,3.)]
    s._consumed_audio_end=3.2;s._last_status={x.index:x.status.value for x in d._resolved_states}
    return s


def views():
    words=('الدين','اياك','نعبد','واياك');scores=(.95,.81,.87,.96)
    times=((0.,0.),(1.,1.),(2.,2.),(3.,3.))
    return [(0,80000,words,scores,times),(0,94400,words,scores,times)]


def feed(s,view):
    s._pcm=bytearray(view[1]*2)
    s._repair_anchored_native_words(view)
    s._last_native_view=view


def snapshot(s):
    d=s._matcher._delegate
    return (d._cursor,d._hyp_cursor,s._consumed_audio_end,s._hypothesis.copy(),
            s._hypothesis_confs.copy(),s._hypothesis_timings.copy(),dict(d._live_hyp_indices))


def test_two_adjacent_words_reveal_only_after_two_native_views_without_moving_source(monkeypatch):
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')
    s=seeded();d=s._matcher._delegate;before=snapshot(s)
    a,b=views();feed(s,a)
    assert d._resolved[1]==d._resolved[2]==WordStatus.SKIPPED
    feed(s,b)
    assert d._resolved[1]==d._resolved[2]==WordStatus.MATCHED
    assert snapshot(s)==before
    assert [(e['word_index'],e['status'])for e in s._diff_events(d._resolved_states)]==[(1,'match'),(2,'match')]
    assert [d._resolved_states[i].confidence for i in (1,2)]==[.81,.87]
    for i in (1,2):
        assert s._native_word_repairs[i]['spans'][1]==(float(i),float(i))
        assert s._native_word_repairs[i]['endpoints']==[80000,94400]


@pytest.mark.parametrize('kind',[
    'weak_word','weak_anchor','nan','infinite','score_above_one','same_endpoint',
    'rereading','wrong_word','missing_word','shared_frame','duplicate_phrase',
    'budget','missing_anchor','weak_old_anchor','unconsumed_anchor','stub',
    'oracle_policy','matched_source','error_source','repaired_source','negative_chunk_time',
    'out_of_chunk_time','contradiction',
])
def test_uncorroborated_span_never_reveals_any_part(kind,monkeypatch):
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')
    s=seeded();d=s._matcher._delegate
    if kind=='budget':s._matcher.max_live_words=2
    if kind=='missing_anchor':d._resolved_states[0].status=WordStatus.SKIPPED
    if kind=='weak_old_anchor':d._resolved_states[0].confidence=.2
    if kind=='unconsumed_anchor':d._hyp_cursor=s._matcher._hyp_cursor=3
    if kind=='stub':s._is_stub=True
    if kind=='oracle_policy':monkeypatch.setattr(ss,'EVIDENCE_POLICY','corroborated')
    if kind in {'matched_source','error_source','repaired_source'}:
        words=s.reference_words+['غريب'];s.reference_words=words;d.reference=words;s._matcher.reference=words
        d._resolved_states.append(WordState(4,'غريب',WordStatus.MATCHED,'غريب',.95));d._resolved[4]=WordStatus.MATCHED
        d._cursor=s._matcher._cursor=5;s._matcher.max_live_words=5
        if kind in {'matched_source','error_source'}:
            if kind=='error_source':
                d._resolved_states[-1].status=WordStatus.ERROR;d._resolved[4]=WordStatus.ERROR
            d._live_hyp_indices[4]=4;s._hypothesis.append('غريب');s._hypothesis_confs.append(.95);s._hypothesis_timings.append((1.,1.))
        else:s._native_word_repairs[4]={'word':'غريب','confidence':.95,'spans':((1.,1.),)*3}
    initial=[(x.status,x.spoken,x.confidence)for x in d._resolved_states];before=snapshot(s)
    rows=copy.deepcopy(views())
    if kind=='same_endpoint':rows[1]=copy.deepcopy(rows[0])
    for n,v in enumerate(rows):
        start,end,words,scores,times=v;words=list(words);scores=list(scores);times=list(times)
        if kind=='weak_word':scores[1]=.2
        if kind=='weak_anchor':scores[3]=.2
        if kind=='nan':scores[2]=float('nan')
        if kind=='infinite':scores[2]=float('inf')
        if kind=='score_above_one':scores[2]=1.1
        if kind=='rereading':start+=48000;end+=48000
        if kind=='wrong_word' or kind=='contradiction'and n==1:words[2]='الناس'
        if kind=='missing_word':
            words.pop(1);scores.pop(1);times.pop(1)
        if kind=='shared_frame':times[2]=times[1]
        if kind=='duplicate_phrase':words+=words;scores+=scores;times+=times
        if kind=='negative_chunk_time':start=16000;times[0]=(-1.,-1.)
        if kind=='out_of_chunk_time':times[-1]=(10.,10.)
        feed(s,(start,end,tuple(words),tuple(scores),tuple(times)))
    assert [(x.status,x.spoken,x.confidence)for x in d._resolved_states]==initial
    assert snapshot(s)==before
    assert not any(i in s._native_word_repairs for i in (1,2))


@pytest.mark.parametrize('kind', ['valid', 'weak_third', 'wrong_third', 'shared_third_frame', 'third_owned_by_error'])
def test_three_adjacent_words_retain_individual_source_spans(kind, monkeypatch):
    monkeypatch.setattr(ss, '_live_asr_engine', lambda: 'fastconformer_rnnt')
    words = ['الدين', 'اياك', 'نعبد', 'واياك', 'نستعين']
    s = seeded()
    d = s._matcher._delegate
    s.reference_words = d.reference = s._matcher.reference = words
    d._resolved_states = [
        WordState(i, word, WordStatus.MATCHED if i in (0, 4) else WordStatus.SKIPPED,
                  word if i in (0, 4) else '', .95 if i in (0, 4) else 0.)
        for i, word in enumerate(words)
    ]
    d._resolved = {x.index: x.status for x in d._resolved_states}
    d._live_hyp_indices = {0: 0, 4: 4}
    d._cursor = s._matcher._cursor = 5
    d._hyp_cursor = s._matcher._hyp_cursor = 5
    s._matcher.max_live_words = 5
    s._hypothesis = [words[0], 'غير', 'الناس', 'غير', words[4]]
    s._hypothesis_confs = [.95] * 5
    s._hypothesis_timings = [(float(i), float(i)) for i in range(5)]
    if kind == 'third_owned_by_error':
        words = words + ['غريب']
        s.reference_words = d.reference = s._matcher.reference = words
        d._resolved_states.append(WordState(5, words[5], WordStatus.ERROR, 'غير', .95))
        d._resolved[5] = WordStatus.ERROR
        d._live_hyp_indices[5] = 5
        d._cursor = s._matcher._cursor = 6
        d._hyp_cursor = s._matcher._hyp_cursor = 6
        s._matcher.max_live_words = 6
        s._hypothesis.append('غير')
        s._hypothesis_confs.append(.95)
        s._hypothesis_timings.append((3., 3.))
    before = snapshot(s)
    initial = copy.deepcopy(d._resolved_states)
    for endpoint in (96000, 110400):
        native_words = list(words[:5])
        scores = [.95] * 5
        times = list(s._hypothesis_timings[:5])
        if kind == 'weak_third':
            scores[3] = .2
        if kind == 'wrong_third':
            native_words[3] = 'الناس'
        if kind == 'shared_third_frame':
            times[3] = times[2]
        feed(s, (0, endpoint, tuple(native_words), tuple(scores), tuple(times)))
    assert snapshot(s) == before
    if kind != 'valid':
        assert d._resolved_states == initial
        assert not any(i in s._native_word_repairs for i in (1, 2, 3))
        return
    assert all(d._resolved[i] == WordStatus.MATCHED for i in (1, 2, 3))
    assert {i: s._native_word_repairs[i]['spans'][1] for i in (1, 2, 3)} == {
        1: (1., 1.), 2: (2., 2.), 3: (3., 3.),
    }


@pytest.mark.parametrize('words,scores', [
    (['اياك', 'الناس'], [.9, .9]),
    (['اياك', 'نعبد'], [.9, .2]),
    (['اياك', 'نعبد'], [.9, float('nan')]),
    (['اياك', 'نعبد'], [.9]),
    (['اياك', 'نعبد', 'واياك', 'نستعين'], [.9] * 4),
])
def test_span_repair_is_atomic_when_a_later_word_is_invalid(words, scores):
    s = seeded()
    d = s._matcher._delegate
    initial = copy.deepcopy(d._resolved_states)
    statuses = dict(d._resolved)
    assert not s._matcher.repair_native_span(1, words, scores)
    assert d._resolved_states == initial
    assert d._resolved == statuses
