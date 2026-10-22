"""The GPU runtime upgrade must preserve original waveform-to-mel processing."""
import hashlib
from pathlib import Path
import numpy as np
import pytest
from ml.training.frozen_whisper_frontend import FeatureExtractor as Frozen


@pytest.mark.parametrize('kind', ['silence', 'voice_band', 'short_impulse'])
def test_original_frontend_features_preserved(kind):
    # Other legacy tests install a lightweight faster_whisper module stub.
    # Load only the optional installed frontend file, avoiding package side effects.
    import importlib.metadata
    import importlib.util
    try:
        package=importlib.metadata.distribution('faster-whisper')
    except importlib.metadata.PackageNotFoundError:
        pytest.skip('Original frontend comparison requires optional faster-whisper')
    path=package.locate_file('faster_whisper/feature_extractor.py')
    spec=importlib.util.spec_from_file_location('original_frontend_comparison',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    Original=module.FeatureExtractor
    audio = np.zeros(16000, dtype=np.float32)
    if kind == 'voice_band':
        t=np.arange(16000, dtype=np.float32)/16000
        audio=.1*np.sin(2*np.pi*230*t)+.03*np.sin(2*np.pi*920*t)
    elif kind == 'short_impulse':
        audio[1234]=.2
    actual=Frozen()(audio);expected=Original()(audio)
    assert actual.shape==expected.shape and actual.shape[0]==80
    np.testing.assert_array_equal(actual, expected)
    assert np.isfinite(actual).all()


def test_frontend_source_is_exact_original_version():
    import ml.training.frozen_whisper_frontend as module
    assert hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()==(
        '5509a21380cc933327bcb01f1d3d2d5ee2e242a7664e672006796ed4f4491b55')
