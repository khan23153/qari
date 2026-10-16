"""Captured correct native anchors must recover a bounded recognition gap."""
import copy
import json
from pathlib import Path

import pytest
from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher, WordState, WordStatus
from ml.inference.transcript import TimedTranscript
from tests.test_streaming import _pcm_seconds

DATA = json.loads((Path(__file__).parent / 'fixtures/timed_baqarah_stall.json').read_text())


def seeded_session(monkeypatch):
    monkeypatch.setattr(ss.settings, 'ml_use_stub', False)
    monkeypatch.setattr(ss, '_live_asr_engine', lambda: 'fastconformer_rnnt')
    monkeypatch.setattr(ss, 'EVIDENCE_POLICY', 'tier2')
    s = ss.StreamingRecitationSession(surah=2, ayah_from=1, ayah_to=20, mode='memorization')
    s.reference_words = DATA['reference'].copy()
    s.reference_text_with_tashkeel_words = s.reference_words.copy()
    s.display_words = s.reference_words.copy()
    s.ayah_boundaries = DATA['ayah_boundaries']
    s._is_stub = False
    seed = DATA['seed']
    d = StreamingMatcher(s.reference_words, ayah_boundaries=s.ayah_boundaries,
        known_error_words=set(s.reference_words) | set(seed['hypothesis']))
    s._matcher = main._ConservativeLiveMatcher(s.reference_words, delegate=d)
    d._resolved_states = [WordState(x['index'], s.reference_words[x['index']],
        WordStatus(x['status']), x['spoken'], x['confidence']) for x in seed['resolved_states']]
    d._resolved = {x.index:x.status for x in d._resolved_states}
    d._live_hyp_indices = {int(k):v for k,v in seed['live_hyp_indices'].items()}
    d._cursor = s._matcher._cursor = seed['cursor']
    d._hyp_cursor = s._matcher._hyp_cursor = max(d._live_hyp_indices.values()) + 1
    d._stall_passes = 3
    s._hypothesis = seed['hypothesis'].copy()
    s._hypothesis_confs = seed['confidences'].copy()
    s._hypothesis_timings = list(map(tuple, seed['timings']))
    s._last_hypothesis = s._hypothesis
    s._consumed_audio_end = max(b for a,b in s._hypothesis_timings[:d._hyp_cursor])
    s._timed_evidence_seen = True
    s._last_status = {x.index:x.status.value for x in d._resolved_states}
    s._qari_active_speech_seconds = 144.
    s._samples_at_last_transcribe = round(144*16000)
    s._pass_count = 50
    s._matcher.max_live_words = 230
    return s


@pytest.mark.asyncio
async def test_captured_two_view_anchors_recover_without_revealing_unrecognized_gap(monkeypatch):
    # The saved recognition belongs to its exact recorded PCM origins, not
    # newly selected windows. Frame-grid policy has its own real-audio tests.
    origins = {round(row['endpoint_seconds']*16000): round(row['window_start']*16000)
               for row in DATA['views']}
    monkeypatch.setattr(ss.StreamingRecitationSession, '_select_audio_window_start',
        lambda self,total,default_start,**kwargs:origins[total])
    s = seeded_session(monkeypatch)
    d = s._matcher._delegate
    def forbidden(*_): raise AssertionError('Reference-conditioned recognition forbidden')
    s._transcriber = forbidden
    replies = iter(DATA['views'])
    def recognize(audio, sr):
        row = next(replies)
        assert sr == 16000 and len(audio) == row['samples']
        return TimedTranscript(row['words'], row['confidences'], row['timings'])
    monkeypatch.setattr(ss, '_independent_transcriber', recognize)
    events = []
    for i, row in enumerate(DATA['views']):
        s._pcm = bytearray(_pcm_seconds(row['endpoint_seconds']))
        events.extend(await s.maybe_transcribe())
        if i < 2: assert s._matcher._cursor == 166
    assert {(e['word_index'],e['status']) for e in events} == {(170,'match'),(171,'match')}
    assert s._matcher._cursor == 172
    assert all(d._resolved[i] == WordStatus.SKIPPED for i in range(166,170))


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', [
    'weak_first', 'weak_second', 'different_word', 'same_endpoint',
    'shifted_occurrence', 'shared_frame', 'duplicate_word', 'budget',
    'reach', 'ayah_ceiling', 'unanchored', 'not_stalled', 'interrupted',
])
async def test_unproven_native_anchor_does_not_recover(monkeypatch, kind):
    s = seeded_session(monkeypatch)
    d = s._matcher._delegate
    # These two captured views have distinct, consistent native frames.
    rows = copy.deepcopy(DATA['views'][1:])
    if kind == 'budget': s._matcher.max_live_words = 171
    if kind == 'reach':
        monkeypatch.setattr('ml.alignment.streaming_matcher.LIVE_SEARCH_REACH_WIDE', 5)
    if kind == 'ayah_ceiling': d._ayah_ranges = [(0,168),(169,169),(170,229)]
    if kind == 'unanchored': d._cursor = 0
    if kind == 'not_stalled': d._stall_passes = 0
    if kind == 'same_endpoint': rows[1] = copy.deepcopy(rows[0])
    before = d._cursor
    for n,row in enumerate(rows):
        i = row['words'].index('ما', row['words'].index('النار'))
        if kind in {'weak_first','weak_second'}:
            row['confidences'][i + (kind == 'weak_second')] = .2
        if kind == 'different_word': row['words'][i+1] = 'قومه'
        if kind == 'shifted_occurrence' and n == 1:
            row['window_start'] += 3
            row['endpoint_seconds'] += 3
        if kind == 'shared_frame': row['timings'][i+1] = row['timings'][i].copy()
        if kind == 'duplicate_word':
            for key in ['words','confidences','timings']:
                row[key].insert(i,copy.deepcopy(row[key][i]))
        s._pcm = bytearray(_pcm_seconds(row['endpoint_seconds']))
        # Use real stitching for the native-to-hypothesis provenance mapping.
        s._hypothesis,s._hypothesis_confs,s._hypothesis_timings = ss._stitch_timed_hypothesis(
            s._hypothesis,s._hypothesis_confs,s._hypothesis_timings,
            row['words'],row['confidences'],row['timings'],
            consumed=d._hyp_cursor,consumed_end=s._consumed_audio_end,
            window_start=row['window_start'],window_seconds=row['samples']/16000,
            confidence_threshold=.55,right_context_seconds=.24)
        s._last_native_view = (round(row['window_start']*16000),round(row['endpoint_seconds']*16000),
            tuple(row['words']),tuple(row['confidences']),tuple(map(tuple,row['timings'])))
        if kind == 'interrupted' and n == 1:
            view = s._last_native_view;s._last_native_view = None
            assert not s._recover_supported_native_anchor()
            s._last_native_view = view
        assert not s._recover_supported_native_anchor()
    assert d._cursor == before
    assert not any(i in d._resolved for i in (170,171))


def test_current_and_later_identical_pairs_are_not_a_unique_recovery(monkeypatch):
    monkeypatch.setattr(ss, '_live_asr_engine', lambda: 'fastconformer_rnnt')
    ref = ['root','alpha','beta','gap','other','alpha','beta','tail']
    d = StreamingMatcher(ref, known_error_words=set(ref) | {'noise'})
    s = ss.StreamingRecitationSession()
    s._matcher = main._ConservativeLiveMatcher(ref, delegate=d)
    s._matcher.max_live_words = 8
    d._resolved_states = [WordState(0,'root',WordStatus.MATCHED,'root',.9)]
    d._resolved = {0:WordStatus.MATCHED}; d._live_hyp_indices = {0:0}
    d._cursor = d._hyp_cursor = 1
    s._hypothesis = ['root'] + ['noise']*11 + ['alpha','beta']
    s._hypothesis_confs = [.9]*14
    s._hypothesis_timings = [(0.,0.)] + [(.2+.1*i,.2+.1*i)for i in range(11)] + [(2.,2.08),(2.4,2.48)]
    s._consumed_audio_end = 0.
    s._pcm = bytearray(6*32000)
    for _ in range(2): s._matcher.evaluate(s._hypothesis,s._hypothesis_confs)
    assert d._cursor == 1
    for endpoint in [4,5]:
        s._last_native_view = (0,endpoint*16000,tuple(s._hypothesis),tuple(s._hypothesis_confs),tuple(s._hypothesis_timings))
        assert not s._recover_supported_native_anchor()
    assert d._cursor == 1
    assert 5 not in d._resolved


@pytest.mark.parametrize('drift', [.08,.16,.24])
def test_revised_last_consumed_word_cannot_become_a_fresh_anchor(monkeypatch, drift):
    monkeypatch.setattr(ss, '_live_asr_engine', lambda: 'fastconformer_rnnt')
    ref = ['alpha','gap1','gap2','gap3','alpha','beta','tail']
    d = StreamingMatcher(ref, known_error_words=set(ref))
    s = ss.StreamingRecitationSession()
    s._matcher = main._ConservativeLiveMatcher(ref, delegate=d)
    s._matcher.max_live_words = 7
    d._resolved_states = [WordState(0,'alpha',WordStatus.MATCHED,'alpha',.9)]
    d._resolved = {0:WordStatus.MATCHED}; d._live_hyp_indices = {0:0}
    d._cursor = d._hyp_cursor = 1; d._stall_passes = 3
    s._hypothesis = ['alpha','alpha','beta']
    s._hypothesis_confs = [.9]*3
    spans = ((10.+drift,10.+drift+.16),(10.+drift+.4,10.+drift+.48))
    s._hypothesis_timings = [(10.,10.),*spans]
    s._consumed_audio_end = 10.
    s._pcm = bytearray(14*32000)
    for endpoint in [12,13]:
        s._last_native_view = (0,endpoint*16000,('alpha','beta'),(.9,.9),spans)
        assert not s._recover_supported_native_anchor()
    assert d._cursor == 1
