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


def test_consumed_yatim_article_variant_is_not_a_second_audio_occurrence():
    # Captured from Duha at PCM endpoint57.6s. The earlier decode omitted al-.
    words, confs, times = ss._stitch_timed_hypothesis(
        ['فاغني', 'فم', 'يتيم'], [.993230314, .456420013, .870173309],
        [(49.399999619, 50.199998856), (51.599999857, 54.799999905),
         (55.439999771, 55.999999714)],
        ['فاغني', 'فاما', 'اليتيم', 'فلا'],
        [.806, .649, .709034503, .986609323],
        [(12.479999542, 13.359999657), (14.63999939, 15.119999886),
         (18.399999619, 19.039999008), (19.760000229, 19.760000229)],
        consumed=3, consumed_end=55.999999714, window_start=37,
        window_seconds=20.6, confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == ['فاغني', 'فم', 'يتيم', 'فلا']
    assert confs == [.993230314, .456420013, .870173309, .986609323]
    assert times[-1] == (56.760000229, 56.760000229)


def test_later_article_variant_has_its_own_audio_occurrence():
    words, _, _ = ss._stitch_timed_hypothesis(
        ['يتيم'], [.9], [(1., 1.4)],
        ['اليتيم', 'فلا'], [.9, .9], [(2., 2.4), (3., 3.2)],
        consumed=1, consumed_end=1.4, window_start=0, window_seconds=4,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == ['يتيم', 'اليتيم', 'فلا']


@pytest.mark.parametrize('a,b', [('الله', 'لله'), ('فابي', 'فاوي'), ('تقهر', 'تنهر')])
def test_stitch_identity_does_not_alias_distinct_critical_words(a, b):
    assert not ss._words_similar(a, b)


def test_non_article_alwanehu_and_wa_annahu_remain_distinct():
    assert not ss._words_similar('ألوانه', 'وأنه')
    words, _, _ = ss._stitch_timed_hypothesis(
        ['ألوانه'], [.9], [(1., 1.4)],
        ['وأنه'], [.9], [(1.42, 1.46)],
        consumed=1, consumed_end=1.4, window_start=0, window_seconds=2,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == ['ألوانه', 'وأنه']


@pytest.mark.parametrize('a,b', [('اللهم', 'لهم'), ('التقى', 'تقي')])
def test_wasla_lam_does_not_merge_a_different_word(a, b):
    assert not ss._words_similar(a, b)
    words, _, _ = ss._stitch_timed_hypothesis(
        [a], [.9], [(1., 1.4)], [b], [.9], [(1.42, 1.46)],
        consumed=1, consumed_end=1.4, window_start=0, window_seconds=2,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == [a, b]


@pytest.mark.parametrize('a,b', [('اليتيم', 'يتيم'), ('السايل', 'سايل')])
def test_reviewed_article_identity_is_symmetric(a, b):
    assert ss._words_similar(a, b)
    assert ss._words_similar(b, a)


def _stitch_captured_sail_revision(*, weak_anchor=False, later_repeat=False):
    # Actual Duha64.8→65.7s. A weak Waamma lies between two strong past words.
    shift = 4. if later_repeat else 0.
    return ss._stitch_timed_hypothesis(
        ['تقهر', 'وانا', 'السايل'], [.870438, .434, .802],
        [(57.600000381, 58.079999924), (59.379999924, 61.219999924),
         (61.859999924, 64.019999924)],
        ['تقهر', 'واما', 'السايل', 'فلا'],
        [.2 if weak_anchor else .928, .923, .805, .868],
        [(12.63999939, 13.43999958), (14.319999695, 16.559999466),
         (16.879999161+shift, 19.600000381+shift),
         (19.760000229+shift, 19.760000229+shift)],
        consumed=3, consumed_end=64.019999924, window_start=45,
        window_seconds=25. if later_repeat else 20.7,
        confidence_threshold=.55, right_context_seconds=.24,
    )


def test_two_strong_past_occurrences_prevent_sail_duplication_across_a_weak_gap():
    words, confs, _ = _stitch_captured_sail_revision()
    assert words == ['تقهر', 'وانا', 'السايل', 'فلا']
    assert confs == [.870438, .434, .802, .868]


@pytest.mark.parametrize('kind', ['weak_anchor', 'later_repeat'])
def test_unproven_sail_revision_cannot_remove_a_new_occurrence(kind):
    words, _, _ = _stitch_captured_sail_revision(**{kind: True})
    assert words == ['تقهر', 'وانا', 'السايل', 'السايل', 'فلا']


@pytest.mark.parametrize('kind', ['shared_frame', 'weak_past', 'changed_anchor', 'drift', 'short_span', 'crossing'])
def test_two_anchor_stitch_rejects_unproven_or_ambiguous_occurrences(kind):
    prefix = ['تقهر', 'وانا', 'السايل']
    scores = [.9, .4, .9]
    past = [(0., .4), (.5, .7), (1., 2.)]
    words = ['تقهر', 'واما', 'السايل', 'فلا']
    confs = [.9, .9, .9, .9]
    times = [(.04, .44), (.52, .72), (1.04, 2.6), (2.8, 2.9)]
    if kind == 'shared_frame':
        words.insert(3, 'لفظ'); confs.insert(3, .9); times.insert(3, (1.04, 2.6))
    if kind == 'weak_past': scores[0] = .2
    if kind == 'changed_anchor': words[0] = 'تنهر'
    if kind == 'drift': times[2] = (1.12, 2.6)
    if kind == 'short_span': past[2] = (1., 1.08)
    if kind == 'crossing': past[1] = (.5, 1.2)
    stitched, _, _ = ss._stitch_timed_hypothesis(
        prefix, scores, past, words, confs, times, consumed=3,
        consumed_end=past[-1][1], window_start=0, window_seconds=3.6,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert stitched.count('السايل') == 2


def test_two_past_anchor_proof_still_retains_a_genuine_following_repeat():
    words, _, _ = ss._stitch_timed_hypothesis(
        ['تقهر', 'وانا', 'السايل'], [.9, .4, .9],
        [(0., .4), (.5, .7), (1., 2.)],
        ['تقهر', 'واما', 'السايل', 'السايل', 'فلا'], [.9] * 5,
        [(.04, .44), (.52, .72), (1.04, 2.6), (2.8, 3.), (3.2, 3.3)],
        consumed=3, consumed_end=2., window_start=0, window_seconds=4.,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words == ['تقهر', 'وانا', 'السايل', 'السايل', 'فلا']


def test_two_anchor_stitch_cannot_use_one_shared_identifying_frame():
    words, _, _ = ss._stitch_timed_hypothesis(
        ['تقهر', 'وانا', 'السايل'], [.9, .4, .9],
        [(1., 1.), (1., 1.), (1., 1.3)],
        ['تقهر', 'واما', 'السايل'], [.9, .4, .9],
        [(1.04, 1.04), (1.04, 1.04), (1.04, 1.9)],
        consumed=3, consumed_end=1.3, window_start=0, window_seconds=3.,
        confidence_threshold=.55, right_context_seconds=.24,
    )
    assert words.count('السايل') == 2
