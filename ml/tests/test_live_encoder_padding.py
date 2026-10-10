"""Short live decodes must avoid 30s encoding without changing shared state."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
import math
import numpy as np
import pytest
from ml.inference.faster_whisper_transcriber import FasterWhisperTranscriber


class EncodingBoundary:
    """Stand-in for expensive native encoding, using the SDK's mutable extractor contract."""
    def __init__(self, barrier=None):
        self.feature_extractor = SimpleNamespace(sampling_rate=16000, n_samples=480000, nb_max_frames=3000)
        self.seen = []
        self.barrier = barrier

    def transcribe(self, samples, **options):
        if options.get('chunk_length') is not None:
            self.feature_extractor.n_samples = options['chunk_length'] * 16000
            self.feature_extractor.nb_max_frames = options['chunk_length'] * 100
        def segments():
            if self.barrier is not None:self.barrier.wait(timeout=5)
            frames = self.feature_extractor.nb_max_frames
            self.seen.append((len(samples), frames))
            text = options.get('initial_prompt') or 'سمعنا'
            yield SimpleNamespace(text=text, avg_logprob=-.25, words=[
                SimpleNamespace(word=text, probability=.8, start=.1, end=.2)])
        return segments(), SimpleNamespace()


@pytest.mark.parametrize('samples,frames', [(32000,1500), (120000,1500), (32001,1500), (248000,1600)])
def test_live_audio_keeps_acoustic_padding_floor_and_preserves_evidence(samples, frames):
    model=EncodingBoundary();tx=FasterWhisperTranscriber(model_dir='/unused')
    tx._model_verify=model
    words, scores=tx.transcribe_independent(np.full(samples,.1,dtype=np.float32),16000)
    assert words==['سمعنا']
    assert scores==pytest.approx([math.exp(-.25)])
    assert model.seen==[(samples,frames)]
    assert model.feature_extractor.n_samples==480000
    assert model.feature_extractor.nb_max_frames==3000


def test_overlapping_live_decodes_keep_their_own_chunk_lengths():
    model=EncodingBoundary(Barrier(2));tx=FasterWhisperTranscriber(model_dir='/unused');tx._model_verify=model
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(tx.transcribe_independent,np.full(n,.1,dtype=np.float32),16000) for n in (32000,248000)]
        assert [f.result()[0] for f in futures]==[['سمعنا'],['سمعنا']]
    assert sorted(model.seen)==[(32000,1500),(248000,1600)]
    assert model.feature_extractor.nb_max_frames==3000


def test_live_crop_does_not_shorten_timestamped_review():
    model=EncodingBoundary();tx=FasterWhisperTranscriber(model_dir='/unused');tx._model_verify=model
    tx.transcribe_independent(np.full(32000,.1,dtype=np.float32),16000)
    words,scores,starts,ends=tx.transcribe_independent_with_timings(np.full(32000,.1,dtype=np.float32),16000)
    assert words==['سمعنا'];assert scores==[.8];assert starts==[100];assert ends==[200]
    assert model.seen==[(32000,1500),(32000,3000)]


def test_long_audio_keeps_existing_30_second_chunk_limit():
    model=EncodingBoundary();tx=FasterWhisperTranscriber(model_dir='/unused');tx._model_verify=model
    assert tx.transcribe_independent(np.full(496000,.1,dtype=np.float32),16000)[0]==['سمعنا']
    assert model.seen==[(496000,3000)]
