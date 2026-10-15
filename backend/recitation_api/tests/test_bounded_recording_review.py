"""Long sessions must never send the whole recording to offline RNNT."""
from types import SimpleNamespace
import numpy as np
import pytest
from ml.inference import fastconformer_transcriber as fc
from app.services import streaming_session as ss
from tests.test_production_matcher_policy import production_session, WORDS


@pytest.fixture(autouse=True)
def rnnt(monkeypatch):
    monkeypatch.setattr(ss, '_live_asr_engine', lambda: 'fastconformer_rnnt')
    monkeypatch.setattr(fc,'get_transcriber',lambda:SimpleNamespace(load=lambda:None))


def test_long_review_covers_every_sample_once_with_bounded_native_calls(monkeypatch):
    audio = np.full(4_801_600, .1, dtype=np.float32)  # 300.1 seconds
    chunks = []
    def recognize(samples, rate):
        assert rate == 16000
        assert len(samples) <= 480000, 'Oversized offline inference can exhaust memory'
        chunks.append(samples.copy())
        return ['سمع'], [.23]
    monkeypatch.setattr(ss, '_independent_transcriber', recognize)
    words, scores = ss._independent_recording_transcriber(audio, 16000)
    assert len(chunks) == 11
    assert len(chunks[-1]) == 1600
    np.testing.assert_array_equal(np.concatenate(chunks), audio)
    assert words == ['سمع'] * 11
    assert scores == [.23] * 11  # No promotion of weak native evidence


def test_existing_short_recording_keeps_single_original_native_decode(monkeypatch):
    audio = np.full(3_130_368, .1, dtype=np.float32)  # Existing 195.648s fixture
    calls = []
    def recognize(samples, rate):
        calls.append(samples)
        return ['سمع'], [.71]
    monkeypatch.setattr(ss, '_independent_transcriber', recognize)
    assert ss._independent_recording_transcriber(audio, 16000) == (['سمع'], [.71])
    assert len(calls) == 1
    assert calls[0] is audio


def test_long_silence_never_invokes_native_decoder(monkeypatch):
    def forbidden(*args):
        pytest.fail('Silent segments must not hallucinate final evidence')
    monkeypatch.setattr(ss, '_independent_transcriber', forbidden)
    assert ss._independent_recording_transcriber(np.zeros(4_800_000), 16000) == ([], [])


def test_silent_middle_and_partial_tail_do_not_discard_later_speech(monkeypatch):
    audio = np.zeros(4_801_600, dtype=np.float32)
    audio[:480000] = .1
    audio[-1600:] = -.1
    calls = []
    def recognize(samples, rate):
        calls.append(len(samples))
        return (['اول'], [.8]) if samples[0] > 0 else (['اخر'], [.9])
    monkeypatch.setattr(ss, '_independent_transcriber', recognize)
    assert ss._independent_recording_transcriber(audio,16000) == (['اول','اخر'],[.8,.9])
    assert calls == [480000,1600]


def test_empty_native_window_does_not_prevent_later_evidence(monkeypatch):
    audio = np.full(4_800_000,.1,dtype=np.float32)
    calls = []
    def recognize(samples, rate):
        calls.append(len(samples))
        return ([],[]) if len(calls) < 10 else (['اخر'],[.7])
    monkeypatch.setattr(ss,'_independent_transcriber',recognize)
    assert ss._independent_recording_transcriber(audio,16000) == (['اخر'],[.7])


@pytest.mark.asyncio
async def test_production_finalization_uses_bounded_recording_review(production_session,monkeypatch):
    # No live matches: the final result must be earned by independent audio.
    production_session.add_audio(b'\x00\x20' * 4_800_000)
    def recognize(audio, rate):
        if len(audio) > 480000:
            raise ValueError('Oversized offline inference')
        return WORDS,[.81,.82,.83,.84]
    monkeypatch.setattr(ss,'_independent_transcriber',recognize)
    monkeypatch.setattr(production_session,'_run_tajweed_checks',lambda *args: None)
    result = await production_session.finalize()
    assert [v['word_index']for v in result['word_verdicts']if v['is_correct']] == [0,1,2,3]
    assert [v['confidence']for v in result['word_verdicts']] == [.81,.82,.83,.84]
