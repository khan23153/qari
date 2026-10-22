"""Private native-job boundaries; no network, credentials or gated fixtures."""
import hashlib
import importlib
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf


def module():return importlib.import_module('ml.training.kaggle_realized_phone_job')


def audio_case(amplitude=.1):
    output=io.BytesIO();audio=(amplitude*np.sin(np.arange(8000)*.1)).astype(np.float32)
    sf.write(output,audio,16000,format='WAV',subtype='PCM_16');raw=output.getvalue()
    actual,_=sf.read(io.BytesIO(raw),dtype='float32')
    return raw,{'encoded_bytes':len(raw),'encoded_sha256':hashlib.sha256(raw).hexdigest(),
        'original_sample_rate':16000,'channels':1,'source_frames':8000,'source_format':'WAV',
        'sample_count':8000,'float_pcm_sha256':hashlib.sha256(actual.astype('<f4').tobytes()).hexdigest(),
        'rms':float(np.sqrt(np.mean(actual**2))),'accepted':amplitude!=0,
        'reason':None if amplitude else 'original_speech_rms_guard'}


def test_direct_cli_rejects_non_kaggle_before_heavy_import_or_output(tmp_path):
    script=Path(__file__).resolve().parents[1]/'training/kaggle_realized_phone_job.py'
    result=subprocess.run([sys.executable,str(script),'--input',str(tmp_path/'missing'),
        '--output',str(tmp_path/'absent')],capture_output=True,text=True)
    assert result.returncode!=0 and 'Kaggle' in result.stderr
    assert 'ModuleNotFoundError' not in result.stderr and not (tmp_path/'absent').exists()


@pytest.mark.parametrize('change',['platform','output','input'])
def test_existing_context_and_path_containment_required_before_writes(tmp_path,monkeypatch,change):
    job=module();working=tmp_path/'working';inputs=tmp_path/'input';working.mkdir();inputs.mkdir()
    monkeypatch.setattr(job.platform,'system',lambda:'Linux')
    monkeypatch.setattr(job.platform,'machine',lambda:'x86_64' if change!='platform' else 'aarch64')
    source=inputs/'data';source.mkdir();output=working/'output'
    if change=='output':output=tmp_path/'outside'
    if change=='input':source=tmp_path/'elsewhere'
    with pytest.raises(ValueError):job.require_context(source,output,working=working,inputs=inputs)
    assert not output.exists()


def test_no_cuda_rejects_before_creating_output(tmp_path):
    torch=pytest.importorskip('torch')
    if torch.cuda.is_available():pytest.skip('CPU guard characterization')
    with pytest.raises(RuntimeError,match='CUDA|GPU'):module().require_cuda()
    assert list(tmp_path.iterdir())==[]


@pytest.mark.parametrize('change',['encoded','pcm','rate','quiet_accept'])
def test_source_identity_and_original_speech_guards_cannot_be_normalized_away(change):
    raw,row=audio_case(0. if change=='quiet_accept' else .1)
    if change=='encoded':raw=raw[:-1]+bytes([raw[-1]^1])
    if change=='pcm':row['float_pcm_sha256']='0'*64
    if change=='rate':row['original_sample_rate']=8000
    if change=='quiet_accept':row.update(accepted=True,reason=None)
    with pytest.raises(ValueError):module().verify_encoded_audio(raw,row)


def test_source_verification_preserves_pcm_and_excluded_silence():
    raw,row=audio_case();audio=module().verify_encoded_audio(raw,row)
    assert hashlib.sha256(audio.astype('<f4').tobytes()).hexdigest()==row['float_pcm_sha256']
    raw,row=audio_case(0.)
    assert module().verify_encoded_audio(raw,row) is None


def test_native_frontend_normalizes_only_after_source_verification():
    torch=pytest.importorskip('torch');transformers=pytest.importorskip('transformers')
    raw,row=audio_case();audio=module().verify_encoded_audio(raw,row)
    processor=transformers.Wav2Vec2FeatureExtractor(do_normalize=True,sampling_rate=16000,
        return_attention_mask=True,feature_size=1,padding_value=0.)
    prepared=module().frontend_values(audio,processor)
    assert prepared.dtype==torch.float32 and len(prepared)==8000
    assert abs(float(prepared.mean()))<1e-6 and abs(float(prepared.var(unbiased=False))-1)<1e-3
    assert hashlib.sha256(audio.astype('<f4').tobytes()).hexdigest()==row['float_pcm_sha256']


def test_wrong_native_config_rejects_before_model_creation():
    config={'num_hidden_layers':24,'hidden_size':1024,'vocab_size':80,'pad_token_id':77,
        'conv_kernel':[10,3,3,3,3,2,2],'conv_stride':[5,2,2,2,2,2,2],
        'feat_extract_norm':'layer','mask_time_prob':.075,'ctc_loss_reduction':'mean','ctc_zero_infinity':False}
    module().validate_native_config(config)
    for field,value in [('pad_token_id',0),('vocab_size',44),('mask_time_prob',0.),('ctc_zero_infinity',True)]:
        with pytest.raises(ValueError):module().validate_native_config({**config,field:value})


def test_invalid_private_input_rejects_before_outputs_or_download(tmp_path,monkeypatch):
    job=module();source=tmp_path/'source';source.mkdir();output=tmp_path/'absent'
    monkeypatch.setattr(job,'require_context',lambda *a:None)
    monkeypatch.setattr(job,'require_cuda',lambda:None)
    def forbidden(*a):raise AssertionError('download before source verification')
    monkeypatch.setattr(job,'download_base',forbidden)
    with pytest.raises(FileNotFoundError):job.run(source,output,0.)
    assert not output.exists()


def test_deadline_and_resource_reserves_fail_closed(tmp_path,monkeypatch):
    import resource
    import shutil
    from types import SimpleNamespace
    torch=pytest.importorskip('torch');job=module()
    monkeypatch.setattr(job.time,'monotonic',lambda:10.)
    with pytest.raises(TimeoutError):job.resource_guard(tmp_path,9.)
    monkeypatch.setattr(shutil,'disk_usage',lambda p:SimpleNamespace(free=3*1024**3))
    with pytest.raises(RuntimeError,match='disk'):job.resource_guard(tmp_path,20.)
    monkeypatch.setattr(shutil,'disk_usage',lambda p:SimpleNamespace(free=5*1024**3))
    monkeypatch.setattr(resource,'getrusage',lambda p:SimpleNamespace(ru_maxrss=13*1024**2))
    with pytest.raises(RuntimeError,match='RSS'):job.resource_guard(tmp_path,20.)
    monkeypatch.setattr(resource,'getrusage',lambda p:SimpleNamespace(ru_maxrss=1024))
    monkeypatch.setattr(torch.cuda,'mem_get_info',lambda:(1024**3,16*1024**3))
    with pytest.raises(RuntimeError,match='GPU'):job.resource_guard(tmp_path,20.)


def test_generated_launcher_rejects_host_before_unpack_install_or_output(tmp_path):
    launcher=module().build_launcher({'ml/training/kaggle_realized_phone_job.py':'raise AssertionError("unpacked")'})
    compile(launcher,'native-launcher','exec')
    script=tmp_path/'launcher.py';script.write_text(launcher)
    result=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,cwd=tmp_path)
    assert result.returncode!=0 and 'Kaggle' in result.stderr and 'unpacked' not in result.stderr
    assert {p.name for p in tmp_path.iterdir()}=={'launcher.py'}


def test_native_lazy_import_completes_before_meta_construction(tmp_path,monkeypatch):
    """Provider TorchAO imports build CPU lists; loading those inside meta fails."""
    import sys
    import types
    torch=pytest.importorskip('torch');native=pytest.importorskip('transformers')
    from safetensors.torch import save_file
    cls=native.Wav2Vec2ForCTC
    config=native.Wav2Vec2Config(vocab_size=80,pad_token_id=77,hidden_size=16,
        num_hidden_layers=2,num_attention_heads=2,intermediate_size=32,conv_dim=(8,)*7,
        num_conv_pos_embedding_groups=2,num_conv_pos_embeddings=16,feat_extract_norm='layer',
        mask_time_prob=0.,layerdrop=0.)
    config._attn_implementation='eager';original=cls(config).eval();weights=tmp_path/'tiny.safetensors'
    save_file({k:v.contiguous() for k,v in original.state_dict().items()},str(weights))
    proxy=types.ModuleType('transformers');proxy.__path__=native.__path__
    def imported(name):
        if name=='Wav2Vec2ForCTC':
            # Same concrete operation that the observed lazy TorchAO import performs.
            torch.linspace(0,1,4).tolist()
            return cls
        return getattr(native,name)
    proxy.__getattr__=imported;monkeypatch.setitem(sys.modules,'transformers',proxy)
    loaded=module().load_native_model(config.to_dict(),weights).eval()
    assert all(not p.is_meta for p in loaded.parameters())
    x=torch.sin(torch.arange(8000)*.03)[None]
    with torch.no_grad():assert torch.equal(original(x).logits,loaded(x).logits)
    for key,value in original.state_dict().items():assert torch.equal(value,loaded.state_dict()[key])
