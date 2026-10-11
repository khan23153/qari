"""Final review must not reclassify stitched window overlap as speech."""

import pytest

from app.services import streaming_session as ss
from tests.test_production_matcher_policy import production_session, pcm, WORDS


@pytest.fixture(autouse=True)
def no_tajweed_decode(monkeypatch):
    monkeypatch.setattr(ss.StreamingRecitationSession, '_run_tajweed_checks', lambda *args: None)


@pytest.mark.asyncio
async def test_final_uses_one_full_recording_decode_instead_of_stitched_overlap(
    production_session, monkeypatch,
):
    session = production_session
    recording = pcm(3)
    session.add_audio(recording)
    session._last_hypothesis = WORDS[:2] + WORDS
    session._hypothesis_confs = [.9] * 6
    calls = []
    def recognize(audio, sample_rate):
        calls.append((len(audio), sample_rate))
        return WORDS, [.81, .82, .83, .84]
    monkeypatch.setattr(ss, '_independent_transcriber', recognize)
    result = await session.finalize()
    assert [v['is_correct'] for v in result['word_verdicts']] == [True] * 4
    assert [v['confidence'] for v in result['word_verdicts']] == [.81, .82, .83, .84]
    assert calls == [(48000, 16000)]


@pytest.mark.asyncio
async def test_independent_final_skips_prompted_acoustic_pass_and_marks_metrics_unavailable(
    production_session, monkeypatch,
):
    def forbidden(audio):
        pytest.fail('Independent word review must not run the prompted full-audio model')
    monkeypatch.setattr(production_session, '_run_tajweed_checks', forbidden)
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: (WORDS, [.9] * 4))
    production_session.add_audio(pcm(3))
    result = await production_session.finalize()
    assert result['accuracy_score'] == 1
    for metric in ('tajweed', 'pronunciation', 'fluency'):
        assert result[f'{metric}_available'] is False
        assert result[f'{metric}_score'] == 0


@pytest.mark.asyncio
async def test_final_skips_long_invocation_before_first_reference_anchor(
    production_session, monkeypatch,
):
    production_session.add_audio(pcm(4))
    invocation = ['اعوذ', 'بالله', 'من', 'الشيطان', 'الرجيم']
    monkeypatch.setattr(ss, '_independent_transcriber',
                        lambda audio, sr: (invocation + WORDS, [.9] * 9))
    result = await production_session.finalize()
    assert [v['word_index'] for v in result['word_verdicts']] == [0, 1, 2, 3]
    assert all(v['is_correct'] for v in result['word_verdicts'])


@pytest.mark.asyncio
async def test_shared_allah_without_distinct_adjacent_anchor_cannot_start_final(
    production_session, monkeypatch,
):
    production_session.add_audio(pcm(3))
    monkeypatch.setattr(ss, '_independent_transcriber',
                        lambda audio, sr: (['اعوذ', 'الله', 'الناس'], [.95] * 3))
    result = await production_session.finalize()
    assert result['word_verdicts'] == []
    assert result['confidence'] == 0


@pytest.mark.asyncio
async def test_two_distinct_adjacent_anchors_leave_missing_opening_unconfirmed(
    production_session, monkeypatch,
):
    production_session.add_audio(pcm(3))
    monkeypatch.setattr(ss, '_independent_transcriber',
                        lambda audio, sr: (['اعوذ', 'الرحمن', 'الرحيم'], [.9] * 3))
    result = await production_session.finalize()
    assert [v['word_index'] for v in result['word_verdicts']] == [2, 3]
    assert all(v['is_correct'] for v in result['word_verdicts'])


@pytest.mark.asyncio
@pytest.mark.parametrize('decode', [([], []), (WORDS, []), (['بسم', 'الناس'], [.9, .9])])
async def test_final_preserves_confirmed_live_evidence_when_final_witness_fails_or_disagrees(
    production_session, monkeypatch, decode,
):
    session = production_session
    session.add_audio(pcm(3))
    session._matcher.max_live_words = 4
    session._matcher.evaluate(WORDS, [.81, .82, .83, .84])
    session._matcher.evaluate(WORDS, [.81, .82, .83, .84])
    session._last_hypothesis = WORDS[:2] + WORDS
    session._hypothesis_confs = [.95] * 6
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: decode)
    result = await session.finalize()
    assert [v['word_index'] for v in result['word_verdicts']] == [0, 1, 2, 3]
    assert all(v['is_correct'] for v in result['word_verdicts'])
    assert [v['confidence'] for v in result['word_verdicts']] == [.81, .82, .83, .84]


@pytest.mark.asyncio
async def test_no_final_witness_cannot_score_unconfirmed_cached_words(
    production_session, monkeypatch,
):
    session = production_session
    session.add_audio(pcm(3))
    session._last_hypothesis = WORDS
    session._hypothesis_confs = [.99] * 4
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: ([], []))
    result = await session.finalize()
    assert result['word_verdicts'] == []


@pytest.mark.asyncio
async def test_fresh_confident_match_repairs_prior_live_error(production_session, monkeypatch):
    session = production_session
    session.add_audio(pcm(3))
    session._matcher.max_live_words = 4
    live_words = ['بسم', 'الناس', 'الرحمن', 'الرحيم']
    session._matcher.evaluate(live_words, [.9] * 4)
    session._matcher.evaluate(live_words, [.9] * 4)
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: (WORDS, [.8] * 4))
    result = await session.finalize()
    assert [v['is_correct'] for v in result['word_verdicts']] == [True] * 4
    assert result['word_verdicts'][1]['actual_text'] == 'الله'
    assert result['word_verdicts'][1]['confidence'] == .8


@pytest.mark.asyncio
async def test_missing_final_witness_retains_confirmed_live_error(production_session, monkeypatch):
    session = production_session
    session.add_audio(pcm(3))
    session._matcher.max_live_words = 4
    live_words = ['بسم', 'الناس', 'الرحمن', 'الرحيم']
    session._matcher.evaluate(live_words, [.9] * 4)
    session._matcher.evaluate(live_words, [.9] * 4)
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: ([], []))
    result = await session.finalize()
    assert result['word_verdicts'][1]['is_correct'] is False
    assert result['word_verdicts'][1]['actual_text'] == 'الناس'
    assert result['word_verdicts'][1]['evidence_confirmed'] is True


@pytest.mark.asyncio
@pytest.mark.parametrize('word,confidence', [('اسقباعه', .95), ('الناس', .2)])
async def test_final_unknown_or_low_confidence_substitution_stays_unconfirmed(
    production_session, monkeypatch, word, confidence,
):
    production_session.add_audio(pcm(3))
    monkeypatch.setattr(ss, '_independent_transcriber',
                        lambda audio, sr: (['بسم', word, 'الرحمن', 'الرحيم'], [.9, confidence, .9, .9]))
    result = await production_session.finalize()
    assert [v['word_index'] for v in result['word_verdicts']] == [0, 2, 3]
    assert all(v['is_correct'] for v in result['word_verdicts'])


@pytest.mark.asyncio
async def test_aligned_terminal_substitution_remains_confirmed_red(
    production_session, monkeypatch,
):
    session = production_session
    session.add_audio(pcm(3))
    session._matcher.max_live_words = 4
    session._matcher.evaluate(WORDS[:3], [.8] * 3)
    monkeypatch.setattr(ss, '_independent_transcriber',
                        lambda audio, sr: (WORDS[:3] + ['الناس'], [.9] * 4))
    result = await session.finalize()
    terminal = result['word_verdicts'][-1]
    assert terminal['word_index'] == 3
    assert terminal['is_correct'] is False
    assert terminal['actual_text'] == 'الناس'
    assert terminal['evidence_confirmed'] is True


@pytest.mark.asyncio
async def test_invocation_before_selected_surah_leaves_unrecited_page_tail_pending(
    production_session, monkeypatch,
):
    selected = ['قل', 'هو', 'الله', 'احد']
    page = selected + ['الله', 'الصمد', 'لم', 'يلد', 'ولم', 'يولد']
    matcher = production_session._matcher
    matcher.reference = page
    matcher._delegate.reference = page
    production_session.reference_words = page
    production_session.add_audio(pcm(6))
    monkeypatch.setattr(ss, '_independent_transcriber',
                        lambda audio, sr: (WORDS + selected, [.9] * 8))
    result = await production_session.finalize()
    assert [v['word_index'] for v in result['word_verdicts']] == [0, 1, 2, 3]
    assert all(v['is_correct'] for v in result['word_verdicts'])
