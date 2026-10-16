"""Independent RNNT evidence must keep real scores and emission times."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
import hashlib
import importlib
import math
import sys
import threading
import time
from types import SimpleNamespace

import pytest


def adapter():
    return importlib.import_module('ml.inference.fastconformer_transcriber')


def result(tokens, scores, timestamps):
    return SimpleNamespace(tokens=tokens, ys_log_probs=scores,
                           timestamps=timestamps, text='unused decoder text')


def test_raw_diacritics_bpe_words_scores_and_emission_bounds_survive():
    transcript = adapter().decode_result(result(
        ['▁بِ', 'سْمِ', '▁اللَّهِ', ' ▁الرَّحْ', 'مَنِ'],
        [math.log(.81), math.log(.49), math.log(.9), math.log(.64), math.log(.25)],
        [.08, .16, .32, .48, .56],
    ))
    words, confidences = transcript
    assert words == ['بِسْمِ', 'اللَّهِ', 'الرَّحْمَنِ']
    assert confidences == pytest.approx([.63, .9, .4])
    assert transcript.timings == [(.08, .16), (.32, .32), (.48, .56)]
    with pytest.raises(FrozenInstanceError):
        transcript.words = []


def test_space_boundaries_inside_one_token_do_not_invent_times_or_scores():
    transcript = adapter().decode_result(result(['▁بسم الله'], [math.log(.2)], [.4]))
    assert transcript.words == ['بسم', 'الله']
    assert transcript.confidences == pytest.approx([.2, .2])
    assert transcript.timings == [(.4, .4), (.4, .4)]


def test_underflow_is_zero_confidence_instead_of_a_synthetic_default():
    transcript = adapter().decode_result(result(['▁خطأ'], [-1000.0], [.0]))
    assert transcript.confidences == [0.0]


@pytest.mark.parametrize('tokens,scores,timestamps', [
    (['▁بسم'], [], [.1]),
    (['▁بسم'], [-.2], []),
    (['▁بسم'], [float('nan')], [.1]),
    (['▁بسم'], [float('-inf')], [.1]),
    (['▁بسم'], [float('inf')], [.1]),
    (['▁بسم'], [.1], [.1]),
    (['▁بسم'], [None], [.1]),
    (['▁بسم'], [-.2], [float('nan')]),
    (['▁بسم'], [-.2], [float('inf')]),
    (['▁بسم'], [-.2], [-.1]),
    (['▁بسم', '▁الله'], [-.2, -.2], [.2, .1]),
    ([None], [-.2], [.1]),
])
def test_incomplete_or_invalid_decoder_evidence_fails_closed(tokens, scores, timestamps):
    with pytest.raises(ValueError):
        adapter().decode_result(result(tokens, scores, timestamps))


@pytest.mark.parametrize('missing', ['tokens', 'ys_log_probs', 'timestamps'])
def test_missing_decoder_evidence_field_is_not_trusted(missing):
    decoded = result(['▁بسم'], [-.2], [.1])
    delattr(decoded, missing)
    with pytest.raises(ValueError):
        adapter().decode_result(decoded)


def test_no_tokens_is_empty_evidence():
    transcript = adapter().decode_result(result([], [], []))
    assert tuple(transcript) == ([], [])
    assert transcript.timings == []


@pytest.fixture
def model_dir(tmp_path, monkeypatch):
    module = adapter()
    files = ['encoder.int8.onnx', 'decoder.int8.onnx', 'joiner.int8.onnx', 'tokens.txt']
    payload = b'fixture-model'
    for filename in files:
        (tmp_path / filename).write_bytes(payload)
    monkeypatch.setattr(module, 'MODEL_SHA256', {
        filename: hashlib.sha256(payload).hexdigest() for filename in files
    })
    return tmp_path


def install_decoder(monkeypatch, model_dir, decoded=None):
    """Only expensive external inference is replaced; adapter/I/O stays real."""
    decoded = decoded or result(['▁بسم'], [math.log(.8)], [.0])
    gate = threading.Lock()
    already_loaded = False

    class Recognizer:
        def create_stream(self):
            return SimpleNamespace(accept_waveform=lambda rate, samples: None,
                                   result=decoded)

        def decode_stream(self, stream):
            assert gate.acquire(blocking=False), 'shared decoder must serialize inference'
            try:
                time.sleep(.001)
            finally:
                gate.release()

    def factory(**kwargs):
        nonlocal already_loaded
        assert not already_loaded, 'concurrent readiness must load one recognizer'
        already_loaded = True
        expected = {
            'encoder': str(model_dir / 'encoder.int8.onnx'),
            'decoder': str(model_dir / 'decoder.int8.onnx'),
            'joiner': str(model_dir / 'joiner.int8.onnx'),
            'tokens': str(model_dir / 'tokens.txt'),
            'num_threads': 2, 'sample_rate': 16000, 'feature_dim': 80,
            'decoding_method': 'greedy_search', 'model_type': 'nemo_transducer',
        }
        assert kwargs == expected, 'independent RNNT has no prompt, hotwords or LM'
        return Recognizer()

    monkeypatch.setitem(sys.modules, 'sherpa_onnx', SimpleNamespace(
        OfflineRecognizer=SimpleNamespace(from_transducer=factory)))


def test_transcription_remains_independent_under_concurrent_lazy_load(model_dir, monkeypatch):
    install_decoder(monkeypatch, model_dir)
    transcriber = adapter().FastConformerTranscriber(model_dir=str(model_dir))
    with ThreadPoolExecutor(max_workers=4) as executor:
        transcripts = list(executor.map(lambda _: transcriber.transcribe([.1] * 1600), range(12)))
    assert all(t.words == ['بسم'] and t.confidences == pytest.approx([.8]) for t in transcripts)
    assert all(t.timings == [(0.0, 0.0)] for t in transcripts)


def test_audio_does_not_get_resampled_gain_changed_or_padded(model_dir, monkeypatch):
    import numpy as np

    class Recognizer:
        def create_stream(self):
            def accept(rate, samples):
                assert rate == 16000
                assert samples.dtype == np.float32
                assert samples.tolist() == [-1.0, .0, .5, 1.0]
            return SimpleNamespace(accept_waveform=accept,
                                   result=result(['▁بسم'], [math.log(.8)], [.0]))
        def decode_stream(self, stream):
            pass

    monkeypatch.setitem(sys.modules, 'sherpa_onnx', SimpleNamespace(
        OfflineRecognizer=SimpleNamespace(from_transducer=lambda **kwargs: Recognizer())))
    transcript = adapter().FastConformerTranscriber(str(model_dir)).transcribe([-1.0, .0, .5, 1.0])
    assert transcript.words == ['بسم']


@pytest.mark.parametrize('audio,sample_rate', [
    ([.1], 8000), ([[.1, .2]], 16000), ([float('nan')], 16000),
    ([float('inf')], 16000), ([1.01], 16000), ([-1.01], 16000),
    ([32767], 16000), (None, 16000),
])
def test_invalid_pcm_is_rejected_before_any_model_load(audio, sample_rate, monkeypatch):
    monkeypatch.setitem(sys.modules, 'sherpa_onnx', None)
    with pytest.raises(ValueError):
        adapter().FastConformerTranscriber('/missing-model').transcribe(audio, sample_rate)


def test_empty_audio_needs_no_optional_decoder(monkeypatch):
    monkeypatch.setitem(sys.modules, 'sherpa_onnx', None)
    transcript = adapter().FastConformerTranscriber('/missing-model').transcribe([])
    assert transcript.words == transcript.confidences == transcript.timings == []


def test_unpinned_or_corrupt_weights_fail_readiness(model_dir, monkeypatch):
    (model_dir / 'encoder.int8.onnx').write_bytes(b'wrong-model')
    monkeypatch.setitem(sys.modules, 'sherpa_onnx', None)
    with pytest.raises(ValueError, match='encoder'):
        adapter().FastConformerTranscriber(str(model_dir)).load()


def test_missing_model_assets_fail_readiness(model_dir, monkeypatch):
    (model_dir / 'tokens.txt').unlink()
    monkeypatch.setitem(sys.modules, 'sherpa_onnx', None)
    with pytest.raises(FileNotFoundError):
        adapter().FastConformerTranscriber(str(model_dir)).load()


def test_model_directory_supports_explicit_override_and_environment(monkeypatch):
    monkeypatch.setenv('QARI_FASTCONFORMER_MODEL_DIR', '/models/public-pcd')
    assert adapter().resolve_model_dir() == '/models/public-pcd'
    assert adapter().resolve_model_dir('/explicit') == '/explicit'


def test_shared_factory_reuses_one_decoder_across_live_worker_calls(model_dir, monkeypatch):
    module = adapter()
    monkeypatch.setattr(module, '_transcriber_singleton', None)
    monkeypatch.setenv('QARI_FASTCONFORMER_MODEL_DIR', str(model_dir))
    install_decoder(monkeypatch, model_dir)
    with ThreadPoolExecutor(max_workers=4) as executor:
        transcripts = list(executor.map(
            lambda _: module.get_transcriber().transcribe([.1] * 1600), range(12)))
    assert all(t.words == ['بسم'] and t.confidences == pytest.approx([.8]) for t in transcripts)
