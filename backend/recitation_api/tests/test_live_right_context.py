"""A partial edge prediction is not a completed live word."""
import math
import struct
from types import SimpleNamespace

import pytest

from app import main
from app.services import streaming_session as ss
from ml.inference import faster_whisper_transcriber as fw
from ml.inference import fastconformer_transcriber as rnnt
from ml.inference.transcript import TimedTranscript


def pcm(seconds):
    return b''.join(struct.pack('<h',int(10000*math.sin(2*math.pi*220*i/16000)))
                    for i in range(int(seconds*16000)))


def test_live_context_counts_the_last_emission_frame_before_three_future_frames():
    words, _, _ = ss._stitch_timed_hypothesis(
        [], [], [], ['عليهم'], [.8468536879946981],
        [(4.960000038146973, 5.359999656677246)],
        consumed=0, consumed_end=float('-inf'), window_start=0,
        window_seconds=5.6, confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == []


@pytest.mark.asyncio
async def test_partial_known_word_on_the_context_boundary_cannot_become_green(monkeypatch):
    words = ['صراط', 'الذين', 'انعمت', 'عليهم', 'غير']
    entries = [{'text_with_tashkeel': w, 'clean_text': w} for w in words]
    monkeypatch.setattr(ss, 'resolve_reference_words_sequence', lambda _: (
        words, words, '', entries, [{'word_index_end': 4, 'word_count': 5}],
    ))
    monkeypatch.setattr(ss, '_get_live_error_vocabulary', lambda: frozenset([*words, 'عليكم']))
    monkeypatch.setattr(ss, '_get_live_word_aliases', lambda: {})
    monkeypatch.setattr(ss.settings, 'ml_use_stub', False)
    monkeypatch.setattr(ss, 'EVIDENCE_POLICY', 'tier2')
    monkeypatch.setattr(ss, 'TRANSCRIBE_INTERVAL_SEC', .6)
    monkeypatch.setattr(fw, 'get_transcriber', lambda: SimpleNamespace(load=lambda: None))
    decodes = iter([
        TimedTranscript(words[:3], [.95] * 3,
                        [(.48, 1.12), (2.24, 2.24), (3.6, 4.24)]),
        TimedTranscript(words[:4], [.95, .95, .95, .8468536879946981],
                        [(.48, 1.12), (2.24, 2.24), (3.6, 4.24),
                         (4.960000038146973, 5.359999656677246)]),
        TimedTranscript(words[:3] + ['عليكم', 'غير'], [.95] * 5,
                        [(.48, 1.12), (2.24, 2.24), (3.6, 4.24), (5.12, 5.12), (6.0, 6.4)]),
    ])
    monkeypatch.setattr(ss, '_independent_transcriber', lambda *_: next(decodes))
    session = ss.StreamingRecitationSession(surah=1, ayah_from=7, ayah_to=7)
    session.load_reference()
    assert isinstance(session._matcher, main._ConservativeLiveMatcher)
    session.add_audio(pcm(5.0))
    first = await session.maybe_transcribe()
    assert [e['word_index'] for e in first if e['status'] == 'match'] == [0, 1, 2]
    session.add_audio(pcm(.6))
    assert await session.maybe_transcribe() == []
    session.add_audio(pcm(1.2))
    second = await session.maybe_transcribe()
    assert [(e['word_index'], e['status']) for e in second] == [(3, 'error_skipped'), (4, 'match')]
    assert second[0]['spoken'] == 'عليكم'
    assert second[0]['evidence_confirmed'] is True


@pytest.mark.asyncio
async def test_partial_known_word_waits_for_context_and_corrected_substitution_is_red(monkeypatch):
    words = ['انعمت','عليهم','غير']
    entries = [{'text_with_tashkeel':w,'clean_text':w} for w in words]
    monkeypatch.setattr(ss,'resolve_reference_words_sequence',lambda _: (
        words,words,'',entries,[{'word_index_end':2,'word_count':3}],
    ))
    monkeypatch.setattr(ss,'_get_live_error_vocabulary',lambda:frozenset([*words,'عليكم']))
    monkeypatch.setattr(ss,'_get_live_word_aliases',lambda:{})
    monkeypatch.setattr(ss.settings,'ml_use_stub',False)
    monkeypatch.setattr(ss,'EVIDENCE_POLICY','tier2')
    monkeypatch.setattr(fw,'get_transcriber',lambda:SimpleNamespace(load=lambda:None))
    decodes = iter([
        TimedTranscript(['انعمت','عليهم'],[.95,.794],[(3.6,4.24),(5.04,5.52)]),
        TimedTranscript(['انعمت','عليكم','غير'],[.95,.841,.95],[(3.6,4.24),(5.12,5.44),(6.0,6.5)]),
    ])
    monkeypatch.setattr(ss,'_independent_transcriber',lambda *_:next(decodes))
    session = ss.StreamingRecitationSession(surah=1,ayah_from=7,ayah_to=7)
    session.load_reference()
    assert isinstance(session._matcher,main._ConservativeLiveMatcher)
    session.add_audio(pcm(5.7))
    first = await session.maybe_transcribe()
    assert [event['word_index'] for event in first if event['status']=='match'] == [0]
    session.add_audio(pcm(1.2))
    second = await session.maybe_transcribe()
    assert not any(event['word_index']==1 and event['status']=='match' for event in first+second)
    error = next(event for event in second if event['word_index']==1)
    assert error['status']=='error_skipped'
    assert error['spoken']=='عليكم'
    assert error['evidence_confirmed'] is True
    assert any(event['word_index']==2 and event['status']=='match' for event in second)


def test_background_warmup_prepares_comparison_metadata_before_asr(monkeypatch):
    calls = []
    monkeypatch.setattr(ss,'_get_reference_store',lambda:calls.append('reference'))
    monkeypatch.setattr(ss,'_get_live_error_vocabulary',lambda:calls.append('vocabulary'))
    monkeypatch.setattr(ss,'_get_live_word_aliases',lambda:calls.append('aliases'))
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')
    monkeypatch.setattr(rnnt,'get_transcriber',lambda:SimpleNamespace(load=lambda:calls.append('asr')))
    main._warmup_ml()
    assert calls == ['reference','vocabulary','aliases','asr']


def test_default_timed_stitch_preserves_native_frame_rounding_at_stop():
    words,confidences,times = ss._stitch_timed_hypothesis(
        [],[],[],['الرحيم'],[.95],[(.96,1.04)],
        consumed=0,consumed_end=float('-inf'),window_start=0.0,window_seconds=1.0,
        confidence_threshold=.55,
    )
    assert words == ['الرحيم']
    assert confidences == [.95]
    assert times == [(.96,1.04)]


@pytest.mark.asyncio
async def test_edge_held_last_word_is_recovered_by_independent_final_review(monkeypatch):
    words = ['انعمت','عليهم','غير']
    entries = [{'text_with_tashkeel':w,'clean_text':w} for w in words]
    monkeypatch.setattr(ss,'resolve_reference_words_sequence',lambda _: (
        words,words,'',entries,[{'word_index_end':2,'word_count':3}],
    ))
    monkeypatch.setattr(ss,'_get_live_error_vocabulary',lambda:frozenset(words))
    monkeypatch.setattr(ss,'_get_live_word_aliases',lambda:{})
    monkeypatch.setattr(ss.settings,'ml_use_stub',False)
    monkeypatch.setattr(ss,'EVIDENCE_POLICY','tier2')
    monkeypatch.setattr(fw,'get_transcriber',lambda:SimpleNamespace(load=lambda:None))
    decodes = []
    def recognize(*_):
        decodes.append(True)
        return TimedTranscript(words,[.95]*3,[(3.6,4.24),(5.12,5.44),(6.0,6.6)])
    monkeypatch.setattr(ss,'_independent_transcriber',recognize)
    session = ss.StreamingRecitationSession(surah=1,ayah_from=7,ayah_to=7)
    session.load_reference()
    async def no_persist(*_):
        pass
    session._persist = no_persist
    session._write_wav = lambda:None
    session.add_audio(pcm(6.7))
    events = await session.maybe_transcribe()
    assert [e['word_index'] for e in events if e['status']=='match'] == [0,1]
    assert await session.maybe_transcribe(force=True) == []
    assert len(decodes)==1
    result = await session.finalize()
    assert len(decodes)==2
    assert [v['word_index'] for v in result['word_verdicts'] if v['is_correct']] == [0,1,2]
