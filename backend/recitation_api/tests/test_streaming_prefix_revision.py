"""A corrected prefix has different first emissions but the same bounded word."""
import copy
import json
from pathlib import Path

import pytest
from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher, WordStatus

DATA = json.loads((Path(__file__).parent / 'fixtures/timed_prefix_revision.json').read_text())


def session():
    s = ss.StreamingRecitationSession()
    s.reference_words = DATA['reference']
    d = StreamingMatcher(s.reference_words, known_error_words=set(s.reference_words) | {'هم'})
    s._matcher = main._ConservativeLiveMatcher(s.reference_words, delegate=d)
    s._matcher.max_live_words = 3
    seed = DATA['seed']
    s._matcher.evaluate(seed['words'], seed['confidences'])
    s._hypothesis = seed['words'].copy()
    s._hypothesis_confs = seed['confidences'].copy()
    s._hypothesis_timings = list(map(tuple, seed['timings']))
    s._consumed_audio_end = seed['timings'][-1][1]
    s._last_status = {x.index: x.status.value for x in d._resolved_states}
    assert d._resolved[1] == WordStatus.ERROR
    return s


def view(s, row):
    s._pcm = bytearray(row['endpoint_samples'] * 2)
    s._revise_supported_timed_errors(
        row['words'], row['confidences'], row['timings'],
        window_start=row['window_start'], window_seconds=row['window_seconds'],
        right_context_seconds=.24, endpoint_samples=row['endpoint_samples'],
    )


def test_two_bounded_native_prefix_corrections_reveal_only_previously_rejected_word():
    s = session()
    before = (s._matcher._cursor, s._matcher._hyp_cursor, s._consumed_audio_end)
    view(s, DATA['views'][0])
    assert s._matcher._delegate._resolved[1] == WordStatus.ERROR
    view(s, DATA['views'][1])
    states = s._matcher.evaluate(s._hypothesis, s._hypothesis_confs)
    assert [(e['word_index'], e['status']) for e in s._diff_events(states)] == [(1, 'match')]
    assert s._hypothesis == ['اكثرهم', 'فهم', 'لا']
    assert (s._matcher._cursor, s._matcher._hyp_cursor, s._consumed_audio_end) == before
    assert not s._diff_events(states)


@pytest.mark.parametrize('kind', [
    'same_endpoint', 'weak_left', 'weak_right', 'weak_word', 'missing_left',
    'wrong_left', 'wrong_right', 'different_occurrence', 'target_not_contained',
    'anchor_drift', 'shared_left_frame', 'shared_right_frame', 'below_budget',
])
def test_unproven_prefix_correction_cannot_reveal(kind):
    s = session()
    if kind == 'missing_left':
        s._matcher._delegate._live_hyp_indices.pop(0)
    if kind == 'below_budget':
        s._matcher.max_live_words = 1
    for n, original in enumerate(DATA['views']):
        r = copy.deepcopy(DATA['views'][0] if kind == 'same_endpoint' else original)
        i = r['words'].index('اكثرهم') + 1
        if kind.startswith('weak_'):
            j = {'weak_left': i-1, 'weak_right': i+1, 'weak_word': i}[kind]
            r['confidences'][j] = .2
        if kind == 'wrong_left': r['words'][i-1] = 'اباوهم'
        if kind == 'wrong_right': r['words'][i+1] = 'ما'
        if kind == 'different_occurrence':
            r['window_start'] += 3; r['endpoint_samples'] += 48000
        if kind == 'target_not_contained':
            r['timings'][i] = [v-.4 for v in r['timings'][i]]
        if kind == 'anchor_drift':
            r['timings'][i+1] = [v+.3 for v in r['timings'][i+1]]
        if kind.startswith('shared_'):
            j = i-1 if kind == 'shared_left_frame' else i+1
            for key in ['words', 'confidences', 'timings']:
                r[key].insert(j, copy.deepcopy(r[key][j]))
        view(s, r)
    assert s._matcher._delegate._resolved[1] == WordStatus.ERROR
    assert s._hypothesis == DATA['seed']['words']
