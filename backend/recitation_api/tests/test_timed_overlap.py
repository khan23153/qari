"""Old words in a repeated PCM window cannot become a new spoken mistake."""

from types import SimpleNamespace

import pytest

from app import main
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


def test_single_consumed_word_cannot_repeat_when_its_end_emission_is_revised():
    words, confs, times = ss._stitch_timed_hypothesis(
        ['قل'], [.878], [(.16, .16)],
        ['قل', 'الله'], [.999, .989], [(.16, .56), (1.12, 1.44)],
        consumed=1, consumed_end=.16, window_start=0, window_seconds=1.8,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == ['قل', 'الله']
    assert confs == [.878, .989]
    assert times == [(.16, .16), (1.12, 1.44)]


def test_a_genuine_later_repeat_after_the_single_past_anchor_is_retained():
    words, confs, times = ss._stitch_timed_hypothesis(
        ['قل'], [.878], [(.16, .16)],
        ['قل', 'قل', 'الله'], [.999, .91, .989],
        [(.16, .56), (.64, 1.04), (1.12, 1.44)],
        consumed=1, consumed_end=.16, window_start=0, window_seconds=1.8,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == ['قل', 'قل', 'الله']
    assert confs == [.878, .91, .989]
    assert times == [(.16, .16), (.64, 1.04), (1.12, 1.44)]


@pytest.mark.parametrize('window_start,timings', [
    (0.0, [(.24, .64), (.8, 1.04)]),
    (.08, [(.16, .56), (.72, .96)]),
])
def test_a_repeat_one_frame_later_is_not_an_anchor_for_the_consumed_word(window_start, timings):
    words, _, _ = ss._stitch_timed_hypothesis(
        ['قل'], [.95], [(.16, .16)],
        ['قل', 'الله'], [.95, .95], timings,
        consumed=1, consumed_end=.16, window_start=window_start, window_seconds=1.5,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == ['قل', 'قل', 'الله']


def test_the_same_absolute_start_frame_anchors_a_revised_sliding_window():
    words, _, _ = ss._stitch_timed_hypothesis(
        ['قل'], [.95], [(.16, .16)],
        ['قل', 'الله'], [.95, .95], [(.08, .48), (1.04, 1.36)],
        consumed=1, consumed_end=.16, window_start=.08, window_seconds=1.8,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == ['قل', 'الله']


def test_a_long_consumed_word_cannot_repeat_when_its_last_emission_moves():
    words, _, _ = ss._stitch_timed_hypothesis(
        ['الرحمن'], [.9], [(.16, .16)],
        ['الرحمن', 'الرحيم'], [.99, .95], [(.16, 1.44), (1.52, 1.6)],
        consumed=1, consumed_end=.16, window_start=0, window_seconds=2,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == ['الرحمن', 'الرحيم']


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
async def test_revised_qul_emissions_cannot_turn_an_omitted_huwa_red(session, monkeypatch):
    decodes = iter([
        TimedDecode(['قل', 'الله'], [.878, .975], [(.16, .16), (.8, .8)]),
        TimedDecode(['قل', 'الله'], [.999, .989], [(.16, .56), (1.12, 1.44)]),
    ])
    monkeypatch.setattr(ss, 'TRANSCRIBE_INTERVAL_SEC', .6)
    monkeypatch.setattr(ss, '_independent_transcriber', lambda *_: next(decodes))
    # At the first tick only one reference word has enough measured speech
    # budget. The next chunk unlocks the following words, as in the real WAV.
    session.add_audio(_pcm_seconds(.6) + bytes(19200))
    first = await session.maybe_transcribe()
    assert [(e['word_index'], e['status']) for e in first] == [(0, 'match')]
    session.add_audio(_pcm_seconds(.6))
    second = await session.maybe_transcribe()
    assert [(e['word_index'], e['status']) for e in second] == [(2, 'match')]
    assert not any(e['word_index'] == 1 for e in first + second)


@pytest.mark.asyncio
@pytest.mark.parametrize('engine', ['fastconformer_rnnt', 'faster_whisper'])
async def test_fast_rnnt_reveals_new_audio_before_the_legacy_decode_interval(session, monkeypatch, engine):
    monkeypatch.setenv('QARI_LIVE_ASR_ENGINE', engine)
    assert isinstance(session._matcher, main._ConservativeLiveMatcher)
    decodes = iter([
        TimedDecode(['قل'], [.95], [(.08, .16)]),
        TimedDecode(['قل', 'هو'], [.95, .95], [(.08, .16), (.64, .8)]),
    ])
    monkeypatch.setattr(ss, '_independent_transcriber', lambda *_: next(decodes))
    session.add_audio(_pcm_seconds(.9))
    first = await session.maybe_transcribe()
    assert [(e['word_index'], e['status']) for e in first] == (
        [(0, 'match')] if engine == 'fastconformer_rnnt' else []
    )
    session.add_audio(_pcm_seconds(.9))
    second = await session.maybe_transcribe()
    assert [(e['word_index'], e['status']) for e in second] == (
        [(1, 'match')] if engine == 'fastconformer_rnnt' else [(0, 'match')]
    )


@pytest.mark.asyncio
async def test_fast_rnnt_quiet_interval_does_not_decode_or_reveal_old_speech(session, monkeypatch):
    monkeypatch.setenv('QARI_LIVE_ASR_ENGINE', 'fastconformer_rnnt')
    assert isinstance(session._matcher, main._ConservativeLiveMatcher)
    monkeypatch.setattr(ss, '_independent_transcriber', lambda *_:
                        TimedDecode(['قل'], [.95], [(.08, .16)]))
    session.add_audio(_pcm_seconds(.9))
    assert [e['word_index'] for e in await session.maybe_transcribe()] == [0]
    session.add_audio(bytes(28800))
    assert await session.maybe_transcribe() == []
    assert session._pass_count == 1
    assert session._matcher._cursor == 1


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


@pytest.mark.asyncio
@pytest.mark.parametrize('interruption', [([], []), (['قل', 'هو', 'الله', 'احد'], [.95] * 4)])
async def test_decode_failure_or_missing_metadata_does_not_poison_timed_history(session, monkeypatch, interruption):
    decodes = iter([
        TimedDecode(['قل', 'هو', 'الله'], [.95] * 3, [(.1, .3), (.4, .6), (.7, .9)]),
        interruption,
        TimedDecode(['قل', 'هو', 'الله', 'احد', 'الله', 'الصمد'], [.95] * 6,
                    [(.1, .3), (.4, .6), (.7, .9), (1.5, 1.7), (1.8, 1.9), (2, 2.1)]),
    ])
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: next(decodes))
    session.add_audio(_pcm_seconds(1.5))
    await session.maybe_transcribe()
    times = list(session._hypothesis_timings)
    session.add_audio(_pcm_seconds(1.5))
    assert await session.maybe_transcribe() == []
    assert session._hypothesis_timings == times
    assert session._matcher._cursor == 3
    session.add_audio(_pcm_seconds(1.5))
    events = await session.maybe_transcribe()
    assert [(e['word_index'], e['status']) for e in events] == [(3, 'match'), (4, 'match'), (5, 'match')]


def test_future_second_token_cannot_be_trimmed_as_past_context():
    words, confs, times = ss._stitch_timed_hypothesis(
        ['قل', 'هو', 'الله'], [.95] * 3, [(.1, .3), (.4, .6), (.7, .9)],
        ['هو', 'الله', 'الصمد'], [.95] * 3, [(.4, .6), (4.2, 4.4), (4.6, 4.8)],
        consumed=3, consumed_end=.9, window_start=0, window_seconds=6,
        confidence_threshold=.55,
    )
    assert words == ['قل', 'هو', 'الله', 'الله', 'الصمد']
    assert times[-2:] == [(4.2, 4.4), (4.6, 4.8)]
