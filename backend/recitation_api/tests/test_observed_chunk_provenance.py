"""Validate chunk-local provenance BEFORE adding recording offsets."""
import numpy as np
import pytest
from app.services import streaming_session as ss


@pytest.mark.parametrize('bad_times', [
    [(-.2,.1),(.3,.4)],
    [(.2,1.5),(1.6,1.8)],
    [(float('nan'),.2),(.3,.4)],
    [(.6,.3),(.7,.8)],
    [(.5,.6),(.1,.2)],
])
def test_malformed_chunk_cannot_gain_plausible_global_harakat_times(monkeypatch,bad_times):
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')
    monkeypatch.setattr(ss,'FINAL_RECORDING_SINGLE_PASS_SEC',1)
    monkeypatch.setattr(ss,'FINAL_RECORDING_CHUNK_SEC',1)
    calls=[]
    def decode(*_):
        calls.append(True)
        times=[(.1,.2),(.3,.4)] if len(calls)==1 else bad_times
        return ss.ObservedTimedTranscript(['انعمت','عليهم'],[.95,.95],times,['أَنْعَمْتُ','عَلَيْهِمْ'])
    monkeypatch.setattr(ss,'_independent_transcriber',decode)
    result=ss._independent_recording_transcriber(np.full(32000,.1,dtype=np.float32),16000)
    words,scores=result
    assert len(words)==len(scores)==4
    assert not hasattr(result,'raw_words'), 'Malformed local timestamps must disable observed-vowel evidence'


def test_valid_native_chunks_retain_exact_offsets(monkeypatch):
    monkeypatch.setattr(ss,'_live_asr_engine',lambda:'fastconformer_rnnt')
    monkeypatch.setattr(ss,'FINAL_RECORDING_SINGLE_PASS_SEC',1)
    monkeypatch.setattr(ss,'FINAL_RECORDING_CHUNK_SEC',1)
    monkeypatch.setattr(ss,'_independent_transcriber',lambda *_:ss.ObservedTimedTranscript(['انعمت'],[.95],[(.1,.2)],['أَنْعَمْتُ']))
    result=ss._independent_recording_transcriber(np.full(32000,.1,dtype=np.float32),16000)
    assert result.timings==[(.1,.2),(1.1,1.2)]
    assert result.raw_words==['أَنْعَمْتُ','أَنْعَمْتُ']
