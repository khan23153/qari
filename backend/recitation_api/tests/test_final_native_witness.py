"""A weak final token must retain two stronger witnesses of the SAME audio."""
import copy
import json
from pathlib import Path

import pytest

from app import main
from app.services import streaming_session as ss
from ml.alignment.streaming_matcher import StreamingMatcher, WordState, WordStatus
from ml.inference.transcript import TimedTranscript

DATA = json.loads((Path(__file__).parent / 'fixtures/baqarah_final_native_witness.json').read_text())


def captured(monkeypatch):
    monkeypatch.setattr(ss, '_live_asr_engine', lambda: 'fastconformer_rnnt')
    monkeypatch.setattr(ss, 'EVIDENCE_POLICY', 'tier2')
    s = ss.StreamingRecitationSession()
    s._is_stub = False
    s.reference_words = DATA['reference'].copy()
    s._matcher = main._ConservativeLiveMatcher(s.reference_words, delegate=StreamingMatcher(s.reference_words))
    s._matcher.max_live_words = 230
    s._pcm = bytearray(b'\xcc\x0c' * DATA['samples'])
    s._previous_native_view, s._last_native_view = copy.deepcopy(DATA['views'])
    states = [WordState(r['word_index'], r['expected_text'], WordStatus.MATCHED,
                        r['actual_text'], r['confidence']) for r in DATA['states']]
    row = DATA['final_native']
    native = TimedTranscript(row['words'].copy(), row['confidences'].copy(),
                             copy.deepcopy(row['timings']))
    return s, states, native


def test_actual_two_native_views_confirm_weak_final_word_without_changing_live_progress(monkeypatch):
    s, states, native = captured(monkeypatch)
    before = (s._matcher._cursor, s._matcher._hyp_cursor, s._hypothesis.copy())
    result = s._repair_final_native_words(states, native)
    assert [(x.index, x.spoken) for x in result] == [(227, 'كل'), (228, 'شي'), (229, 'قدير')]
    assert result[1].confidence == pytest.approx(.5767269034101713)
    assert result[1].status == WordStatus.MATCHED
    assert (s._matcher._cursor, s._matcher._hyp_cursor, s._hypothesis) == before
    assert len(states) == 2  # The final merge does not mutate live WordStates.


@pytest.mark.parametrize('kind', [
    'stub', 'explicit', 'oracle', 'other_engine', 'budget', 'stale',
    'missing_previous', 'same_endpoint', 'weak', 'wrong_word', 'rereading',
    'untimed_final', 'bad_final_times', 'ambiguous_reference', 'ambiguous_final',
    'missing_anchor', 'weak_anchor', 'original_omission', 'original_other_word',
    'already_error', 'already_used',
])
def test_uncertain_wrong_stale_or_ambiguous_audio_cannot_confirm_the_final_gap(kind, monkeypatch):
    s, states, native = captured(monkeypatch)
    if kind == 'stub': s._is_stub = True
    if kind == 'explicit': s._explicit_transcriber = lambda *args: None
    if kind == 'oracle': monkeypatch.setattr(ss, 'EVIDENCE_POLICY', 'corroborated')
    if kind == 'other_engine': monkeypatch.setattr(ss, '_live_asr_engine', lambda: 'faster_whisper')
    if kind == 'budget': s._matcher.max_live_words = 228
    if kind == 'stale': s._pcm.extend(b'\0\0' * 16000)
    if kind == 'missing_previous': s._previous_native_view = None
    if kind == 'same_endpoint': s._previous_native_view = s._last_native_view
    if kind in {'weak', 'wrong_word', 'rereading'}:
        view = s._last_native_view
        slot = view[2].index('شي')
        if kind == 'weak': view[3][slot] = .2
        if kind == 'wrong_word': view[2][slot] = 'لي'
        if kind == 'rereading': view[4][slot - 1][0] += .8
    if kind == 'untimed_final': native = (native.words, native.confidences)
    if kind == 'bad_final_times': native.timings[-1] = (float('nan'), float('nan'))
    if kind == 'ambiguous_reference': s.reference_words[0] = 'كل'
    if kind == 'ambiguous_final': native.words[0] = 'كل'
    if kind == 'missing_anchor': states.pop()
    if kind == 'weak_anchor': states[0].confidence = .2
    if kind == 'original_omission':
        j = native.words.index('شي')
        for values in (native.words, native.confidences, native.timings): values.pop(j)
    if kind == 'original_other_word': native.words[native.words.index('شي')] = 'لي'
    if kind == 'already_error': states.append(WordState(228, 'شي', WordStatus.ERROR, 'لي', .9))
    if kind == 'already_used': states.append(WordState(210, 'اضا', WordStatus.ERROR, 'شي', .9))
    before = [(x.index, x.status, x.spoken, x.confidence) for x in states]
    result = s._repair_final_native_words(states, native)
    assert [(x.index, x.status, x.spoken, x.confidence) for x in result] == before


@pytest.mark.asyncio
async def test_final_result_uses_native_witnesses_without_an_additional_decode(monkeypatch):
    s, states, native = captured(monkeypatch)
    calls = []
    def recording(audio, sr):
        calls.append((len(audio), sr))
        return native
    async def no_persist(*args): pass
    monkeypatch.setattr(ss, '_independent_recording_transcriber', recording)
    monkeypatch.setattr(s._matcher, 'finalize_independent', lambda *args: states)
    s._write_wav = lambda: None
    s._persist = no_persist
    final = await main._original_stream_finalize(s)
    assert [(r['word_index'], r['is_correct']) for r in final['word_verdicts']] == [(227, True), (228, True), (229, True)]
    assert final['word_verdicts'][1]['confidence'] == .577
    assert calls == [(3130368, 16000)]


@pytest.mark.parametrize('source', ['hypothesis', 'native_repair'])
@pytest.mark.parametrize('status', [WordStatus.MATCHED, WordStatus.ERROR])
def test_source_already_assigned_to_other_text_cannot_be_reused(source, status, monkeypatch):
    s, states, native = captured(monkeypatch)
    span = (193.919998, 194.159988)
    other = WordState(210, 'اضا', status, 'اضا' if status == WordStatus.MATCHED else 'لي', .9)
    states.append(other)
    s._matcher._delegate._resolved_states = [other]
    if source == 'hypothesis':
        s._matcher._delegate._live_hyp_indices[210] = 0
        s._hypothesis_timings = [span]
    else:
        s._native_word_repairs[210] = {'spans': [span, span, span]}
    result = s._repair_final_native_words(states, native)
    assert not any(x.index == 228 for x in result)
