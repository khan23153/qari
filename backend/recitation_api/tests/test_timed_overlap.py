"""Old words in a repeated PCM window cannot become a new spoken mistake."""

from types import SimpleNamespace

import pytest

from app.services import streaming_session as ss
from ml.inference import faster_whisper_transcriber as fw
from ml.inference import fastconformer_transcriber as rnnt
from ml.inference.transcript import TimedTranscript
from tests.test_streaming import _pcm_seconds


class TimedDecode(tuple):
    def __new__(cls, words, confidences, timings):
        value = super().__new__(cls, (words, confidences))
        value.timings = timings
        return value


@pytest.fixture
def session(monkeypatch):
    words = ['قل', 'هو', 'الله', 'احد', 'الله', 'الصمد']
    entries = [{'text_with_tashkeel': w, 'clean_text': w} for w in words]
    monkeypatch.setattr(ss.settings, 'ml_use_stub', False)
    monkeypatch.setattr(ss, 'EVIDENCE_POLICY', 'tier2')
    monkeypatch.setattr(ss, 'resolve_reference_words_sequence', lambda refs: (words, words, '', entries, []))
    monkeypatch.setattr(ss, '_get_live_error_vocabulary', lambda: frozenset(words + ['بسم', 'الرحمن', 'الرحيم']))
    monkeypatch.setattr(fw, 'get_transcriber', lambda: SimpleNamespace(load=lambda: None))
    result = ss.StreamingRecitationSession(surah=112)
    result.load_reference()
    return result


@pytest.mark.asyncio
async def test_old_invocation_cannot_substitute_the_next_ikhlas_word(session, monkeypatch):
    decodes = iter([
        TimedDecode(['قل', 'هو', 'الله'], [.95] * 3, [(.1, .3), (.4, .6), (.7, .9)]),
        TimedDecode(
            ['بسم', 'الله', 'الرحمن', 'الرحيم', 'قل', 'هو', 'الله', 'وفت', 'الله', 'الصمد'],
            [.95] * 7 + [.2] * 3,
            [(0, .1), (.2, .3), (.35, .4), (.45, .5), (.55, .6), (.65, .7), (.75, .9), (1.5, 1.7), (1.8, 1.9), (2, 2.1)],
        ),
        TimedDecode(['قل', 'هو', 'الله', 'احد', 'الله', 'الصمد'], [.95] * 6,
                    [(.1, .3), (.4, .6), (.7, .9), (1.5, 1.7), (1.8, 1.9), (2, 2.1)]),
    ])
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: next(decodes))
    session.add_audio(_pcm_seconds(1.5))
    assert [e['word_index'] for e in await session.maybe_transcribe()] == [0, 1, 2]
    session.add_audio(_pcm_seconds(1.5))
    assert await session.maybe_transcribe() == []
    assert session._matcher._cursor == 3
    session.add_audio(_pcm_seconds(1.5))
    events = await session.maybe_transcribe()
    assert [(e['word_index'], e['status']) for e in events] == [(3, 'match'), (4, 'match'), (5, 'match')]


@pytest.mark.asyncio
async def test_past_pair_removes_a_later_timestamp_revision_of_the_same_word(session, monkeypatch):
    decodes = iter([
        TimedDecode(['قل', 'هو', 'الله'], [.95] * 3, [(.1, .3), (.4, .6), (.7, .9)]),
        TimedDecode(['قل', 'هو', 'الله', 'الصمد'], [.95] * 4,
                    [(.1, .3), (.4, .6), (1.1, 1.3), (1.8, 2.0)]),
    ])
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: next(decodes))
    session.add_audio(_pcm_seconds(1.5))
    await session.maybe_transcribe()
    session.add_audio(_pcm_seconds(1.5))
    events = await session.maybe_transcribe()
    assert all(e['spoken'] != 'الله' or e['status'] != 'error_skipped' for e in events)


@pytest.mark.asyncio
async def test_timed_partial_word_can_gain_confidence_on_overlap(session, monkeypatch):
    decodes = iter([
        TimedDecode(['قل', 'هو'], [.95, .2], [(.1, .3), (.4, .6)]),
        TimedDecode(['قل', 'هو', 'الله'], [.95] * 3, [(.1, .3), (.4, .6), (.7, .9)]),
    ])
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: next(decodes))
    session.add_audio(_pcm_seconds(1.5))
    assert [e['word_index'] for e in await session.maybe_transcribe()] == [0]
    session.add_audio(_pcm_seconds(1.5))
    assert [e['word_index'] for e in await session.maybe_transcribe()] == [1, 2]


@pytest.mark.asyncio
@pytest.mark.parametrize('timings', [[(0, 50)], [(float('nan'), .5)], []])
async def test_bad_time_metadata_cannot_reveal_a_word(session, monkeypatch, timings):
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: TimedDecode(['قل'], [.95], timings))
    session.add_audio(_pcm_seconds(1.5))
    assert await session.maybe_transcribe() == []
    assert session._matcher._cursor == 0


def test_optional_live_engine_loads_and_warms_only_the_independent_adapter(session, monkeypatch):
    from app import main
    calls = []
    def forbidden():
        raise AssertionError('RNNT readiness cannot depend on the unused prompted model')
    monkeypatch.setenv('QARI_LIVE_ASR_ENGINE', 'fastconformer_rnnt')
    monkeypatch.setattr(rnnt, 'get_transcriber', lambda: SimpleNamespace(load=lambda: calls.append('rnnt')))
    monkeypatch.setattr(fw, 'get_transcriber', forbidden)
    monkeypatch.setattr(ss, '_get_reference_store', lambda: None)
    session.load_reference()
    assert calls == ['rnnt'] and session._is_stub is False
    calls.clear()
    main._warmup_ml()
    assert calls == ['rnnt']


def test_independent_adapter_retains_timestamps_when_normalizing(session, monkeypatch):
    monkeypatch.setenv('QARI_LIVE_ASR_ENGINE', 'fastconformer_rnnt')
    decoded = TimedTranscript(['ٱلْعَـٰلَمِينَ', '.'], [.9, .1], [(0, .5), (.6, .6)])
    monkeypatch.setattr(rnnt, 'get_transcriber', lambda: SimpleNamespace(transcribe=lambda *args: decoded))
    result = ss._independent_transcriber([.1], 16000)
    assert result.words == ['العالمين']
    assert result.confidences == [.9]
    assert result.timings == [(0, .5)]
