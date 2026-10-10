"""Final results must retain independent speech evidence and its uncertainty."""

from types import SimpleNamespace

import pytest

from app.services import streaming_session as ss
from app import main as api_main
from ml.inference import faster_whisper_transcriber
from tests.test_streaming import REFERENCE, REFERENCE_ENTRIES, _pcm_seconds


@pytest.fixture
def production_session(monkeypatch):
    monkeypatch.setattr(ss.settings, 'ml_use_stub', False)
    monkeypatch.setattr(ss, 'EVIDENCE_POLICY', 'tier2')
    monkeypatch.setattr(
        ss, 'resolve_reference_words_sequence',
        lambda refs: (REFERENCE, REFERENCE, '', REFERENCE_ENTRIES, []),
    )
    monkeypatch.setattr(ss, '_get_live_error_vocabulary', lambda: frozenset({'الناس'}))
    monkeypatch.setattr(
        faster_whisper_transcriber, 'get_transcriber',
        lambda: SimpleNamespace(load=lambda: None),
    )
    monkeypatch.setattr(ss.StreamingRecitationSession, '_run_tajweed_checks', lambda *args: None)
    session = ss.StreamingRecitationSession()
    session.load_reference()
    return session


@pytest.mark.asyncio
async def test_final_result_preserves_confidence_and_omits_unconfirmed_indices(production_session):
    session = production_session
    session._last_hypothesis = REFERENCE[:3]
    session._hypothesis_confs = [.8, .2, .9]
    result = await session.finalize()
    assert [verdict['word_index'] for verdict in result['word_verdicts']] == [0, 2]
    assert [verdict['confidence'] for verdict in result['word_verdicts']] == [.8, .9]
    assert result['confidence'] == pytest.approx(.85)
    assert len(session.reference_words) == 4


@pytest.mark.asyncio
async def test_final_result_with_only_uncertain_words_has_no_confirmed_verdicts(production_session):
    session = production_session
    session._last_hypothesis = REFERENCE
    session._hypothesis_confs = [.2] * 4
    result = await session.finalize()
    assert result['word_verdicts'] == []
    assert result['confidence'] == 0
    assert result['accuracy_score'] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('inner_finalizer', [False, True])
async def test_final_fallback_on_silence_never_invokes_any_model(
    monkeypatch, production_session, inner_finalizer,
):
    def forbidden(*args):
        pytest.fail('Silent finalization must not invoke recognition')
    monkeypatch.setattr(ss, '_independent_transcriber', forbidden)
    production_session._transcriber = forbidden
    production_session.add_audio(_pcm_seconds(1.5, silent=True))
    result = await (
        api_main._original_stream_finalize(production_session)
        if inner_finalizer else production_session.finalize()
    )
    assert result['word_verdicts'] == []
    assert result['confidence'] == 0


@pytest.mark.asyncio
async def test_real_final_fallback_uses_independent_words_and_confidence(monkeypatch, production_session):
    def independent(audio, sr):
        assert sr == 16000 and ss._rms_energy(audio) > .006
        return ['بسم', 'الناس', 'الرحمن'], [.8, .9, .7]
    def oracle(*args):
        pytest.fail('Production finalization must not use the primary model')
    monkeypatch.setattr(ss, '_independent_transcriber', independent)
    production_session._transcriber = oracle
    production_session.add_audio(_pcm_seconds(1.5))
    result = await production_session.finalize()
    assert [verdict['word_index'] for verdict in result['word_verdicts']] == [0, 1, 2]
    assert [verdict['is_correct'] for verdict in result['word_verdicts']] == [True, False, True]
    assert result['word_verdicts'][1]['actual_text'] == 'الناس'
    assert result['word_verdicts'][1]['confidence'] == .9
    assert result['confidence'] == pytest.approx(.8)
    assert result['accuracy_score'] == pytest.approx(.6667)


@pytest.mark.parametrize('decode', [([], []), (REFERENCE, [])])
@pytest.mark.asyncio
async def test_empty_or_unscored_independent_fallback_cannot_promote_oracle(
    monkeypatch, production_session, decode,
):
    monkeypatch.setattr(ss, '_independent_transcriber', lambda audio, sr: decode)
    production_session._transcriber = lambda *args: (REFERENCE, [.95] * 4)
    production_session.add_audio(_pcm_seconds(1.5))
    result = await production_session.finalize()
    assert result['word_verdicts'] == []
    assert result['confidence'] == 0
    assert result['accuracy_score'] == 0


@pytest.mark.asyncio
async def test_trusted_final_error_remains_red_and_continuation_keeps_global_indices(production_session):
    session = production_session
    session._last_hypothesis = ['بسم', 'الناس', 'الرحمن', 'الرحيم']
    session._hypothesis_confs = [.95] * 4
    result = await session.finalize()
    assert [verdict['word_index'] for verdict in result['word_verdicts']] == [0, 1, 2, 3]
    assert [verdict['is_correct'] for verdict in result['word_verdicts']] == [True, False, True, True]
    assert result['word_verdicts'][1]['error_type'] == 'error'
    assert result['confidence'] == .95
