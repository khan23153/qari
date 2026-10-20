"""Private CUDA-only realized-phone job; reject local use before heavy imports."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import time

MODEL='MostafaMaroof/wav2vec2-arabic-phoneme-asr'
MODEL_REVISION='0a32c641aaaeec6957e41a794add52e024e46b50'
MODEL_SHA='582149e3e913a0fc7f29c116530e0b1b6ae7a7ab23eef4efc3fc2acc760e2b75'
MODEL_BYTES=1262135432
MANIFEST_SHA='e9f880d0c3b7056b4ca8e87635d5a5aad4a71e1d9f7fc7d2a26176e90f44016f'
META_PINS={
    'vocab.json':'253e79d757c9946dab216846aa0ff383a0b36e200a728f9be2cd2c135312a5ac',
    'tokenizer_config.json':'b242d716d2a5845ead29edda147962ffaa717462849427fdf37b5654bbc42670',
    'processor_config.json':'8bc3c8d6d97ea61524d5c15d8554b4baf072d2264c0bda1839bc7a822c200d66',
    'config.json':'f584748e877ea68db8dab9a4ef1fd1bf025a590405535331c892d399bf9c697a'}


def file_sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
    return digest.hexdigest()


def require_context(source,output,*,working=Path('/kaggle/working'),inputs=Path('/kaggle/input')):
    source,output,working,inputs=map(lambda p:Path(p).resolve(),(source,output,working,inputs))
    if (platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64')
            or not working.is_dir() or not inputs.is_dir() or not source.is_dir()
            or not source.is_relative_to(inputs) or source==inputs
            or not output.is_relative_to(working) or output==working):
        raise ValueError('Existing Linux/x86 Kaggle input/working context and contained paths required')


def require_cuda():
    import torch
    if not torch.cuda.is_available():raise RuntimeError('Remote CUDA GPU required; no CPU full fallback')


def validate_native_config(config):
    expected={'num_hidden_layers':24,'hidden_size':1024,'vocab_size':80,'pad_token_id':77,
        'conv_kernel':[10,3,3,3,3,2,2],'conv_stride':[5,2,2,2,2,2,2],
        'feat_extract_norm':'layer','mask_time_prob':.075,'ctc_loss_reduction':'mean','ctc_zero_infinity':False}
    if any(config.get(k)!=v for k,v in expected.items()):
        raise ValueError('Pinned native model dimensions/blank/frontend/CTC configuration required')


def verify_encoded_audio(raw,row):
    import io
    import numpy as np
    import soundfile as sf
    if (not isinstance(raw,bytes) or not 1<=len(raw)<=3*1024**2
            or len(raw)!=row['encoded_bytes'] or hashlib.sha256(raw).hexdigest()!=row['encoded_sha256']):
        raise ValueError('Original source bytes/SHA mismatch')
    info=sf.info(io.BytesIO(raw))
    if (info.samplerate!=16000 or info.channels!=1 or info.format!='WAV'
            or info.samplerate!=row['original_sample_rate'] or info.channels!=row['channels']
            or info.format!=row['source_format'] or info.frames!=row['source_frames']):
        raise ValueError('Original rate/channels/source format mismatch; no implicit resampling')
    if not 4000<=info.frames<=480000:
        if row['accepted'] or row['reason']!='duration_guard':raise ValueError('Original duration guard mismatch')
        return None
    audio,sr=sf.read(io.BytesIO(raw),dtype='float32',always_2d=False)
    if (audio.ndim!=1 or not np.isfinite(audio).all() or np.max(np.abs(audio))>1.01
            or len(audio)!=row['sample_count']
            or hashlib.sha256(audio.astype('<f4',copy=False).tobytes()).hexdigest()!=row['float_pcm_sha256']):
        raise ValueError('Actual lossless source PCM identity mismatch')
    rms=float(np.sqrt(np.mean(audio**2)))
    if abs(rms-row['rms'])>1e-7:raise ValueError('Original PCM RMS audit mismatch')
    if rms<.006:
        if row['accepted'] or row['reason']!='original_speech_rms_guard':raise ValueError('Original speech guard mismatch')
        return None
    if not row['accepted']:
        if row['reason']!='duplicate_pcm_quarantine':raise ValueError('Unexplained original speech exclusion')
        return None
    return audio


def frontend_values(audio,processor):
    import numpy as np
    import torch
    # No text/reference/labels are accepted by this acoustic-only boundary.
    values=processor(audio,sampling_rate=16000,return_tensors='pt',return_attention_mask=True)
    if set(values)!={'input_values','attention_mask'}:raise ValueError('Native acoustic frontend fields required')
    result=values['input_values'][0].to(dtype=torch.float32)
    if result.shape!=(len(audio),) or not torch.isfinite(result).all():raise ValueError('Invalid normalized native frontend')
    return result


def resource_guard(output,deadline):
    import resource
    import shutil
    import torch
    if time.monotonic()>=deadline:raise TimeoutError('Remote7100s whole-job deadline reached')
    if shutil.disk_usage(output).free<4*1024**3:raise RuntimeError('Remote4GiB disk reserve reached')
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>12*1024**2:raise RuntimeError('Remote12GiB RSS limit reached')
    if torch.cuda.mem_get_info()[0]<2*1024**3:raise RuntimeError('Remote2GiB GPU reserve reached')


def verify_input(source):
    from ml.training.realized_phone_data import SOURCE_SHA, validate_realized_manifest
    source=Path(source)
    manifest=json.loads((source/'source-manifest.json').read_text())
    validate_realized_manifest(manifest)
    if manifest['manifest_sha256']!=MANIFEST_SHA:raise ValueError('Frozen prospective manifest identity changed')
    parquet=source/'train-pinned.parquet'
    if parquet.stat().st_size!=208493997 or file_sha(parquet)!=SOURCE_SHA:
        raise ValueError('Pinned full parquet byte identity mismatch')
    for name,digest in META_PINS.items():
        if file_sha(source/name)!=digest:raise ValueError('Pinned public native metadata mismatch')
    config=json.loads((source/'config.json').read_text());validate_native_config(config)
    vocabulary=json.loads((source/'vocab.json').read_text())
    tokenizer=json.loads((source/'tokenizer_config.json').read_text())
    for index,item in tokenizer['added_tokens_decoder'].items():vocabulary[item['content']]=int(index)
    if vocabulary!=manifest['native_vocabulary']:raise ValueError('Native vocabulary identity mismatch')
    return manifest,config


def prepare_rows(source,manifest,processor,check):
    import duckdb
    from ml.training.realized_phone_data import _metadata_sha
    connection=duckdb.connect();connection.execute("SET memory_limit='256MB'");connection.execute('SET threads=1')
    path=str(Path(source)/'train-pinned.parquet')
    names=['id','sentence','phoneme_ref','phoneme_mis','audio_path']
    metadata=[dict(zip(names,row)) for row in connection.execute(
        'SELECT id,sentence,phoneme_ref,phoneme_mis,audio.path FROM read_parquet(?)',[path]).fetchall()]
    if metadata!=manifest['metadata'] or _metadata_sha(metadata)!=manifest['metadata_sha256']:
        raise ValueError('Actual parquet metadata/realized targets changed')
    audited={r['id']:r for r in manifest['source_audit']['cases']}
    cases={r['id']:r for r in manifest['cases']};seen=set();rows=[];cached_bytes=0
    query=connection.execute('SELECT id,audio.bytes FROM read_parquet(?)',[path])
    while True:
        batch=query.fetchmany(16)
        if not batch:break
        check()
        for name,raw in batch:
            if name in seen or name not in cases:raise ValueError('Unexpected/duplicate actual source ID')
            seen.add(name);audio=verify_encoded_audio(raw,audited[name]);case=cases[name]
            if case['training_eligible'] or case['evaluation_eligible']:
                if audio is None:raise ValueError('Assigned source failed original PCM guard')
                cached_bytes+=audio.nbytes
                if cached_bytes>1024**3:raise ValueError('Selected waveform cache exceeds1GiB')
                rows.append({'id':name,'role':case['role'],'target_ids':case['target_ids'],
                             'input_values':frontend_values(audio,processor)})
        print(json.dumps({'event':'realized_phone.source_verified','sources':len(seen),'selected':len(rows)}),flush=True)
    connection.close()
    if seen!=set(cases) or len(rows)!=639:raise ValueError('Exact original source and selected-role counts required')
    return sorted(rows,key=lambda r:r['id'])


def download_base(path,check):
    import requests
    url=f'https://huggingface.co/{MODEL}/resolve/{MODEL_REVISION}/model.safetensors?download=true'
    with requests.get(url,stream=True,timeout=(30,60)) as response:
        response.raise_for_status();digest=hashlib.sha256();size=0
        with Path(path).open('wb') as stream:
            for block in response.iter_content(1024**2):
                if not block:continue
                check();size+=len(block)
                if size>MODEL_BYTES:raise ValueError('Native model download byte limit exceeded')
                stream.write(block);digest.update(block)
    if size!=MODEL_BYTES or digest.hexdigest()!=MODEL_SHA:raise ValueError('Pinned native safetensors identity mismatch')


def run(source,output,deadline):
    require_context(source,output);require_cuda()
    # Verify all input identities before creating outputs or downloading weights.
    manifest,config=verify_input(source)
    import inspect
    import importlib.metadata
    import signal
    import torch
    import transformers
    from safetensors.torch import load_file
    from ml.training.realized_phone_adaptation import train_adapter
    signal.alarm(max(1,int(deadline-time.monotonic())))
    torch.set_num_threads(2);torch.manual_seed(42);torch.cuda.manual_seed_all(42)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    scratch=output.parent/'native-realized-scratch';scratch.mkdir(exist_ok=True)
    check=lambda:resource_guard(output,deadline)
    check()
    frontend_config=json.loads((Path(source)/'processor_config.json').read_text())['feature_extractor']
    processor=transformers.Wav2Vec2FeatureExtractor(**frontend_config)
    rows=prepare_rows(source,manifest,processor,check)
    weights=scratch/'model.safetensors';download_base(weights,check)
    native_config=transformers.Wav2Vec2Config.from_dict(config);native_config._attn_implementation='eager'
    with torch.device('meta'):model=transformers.Wav2Vec2ForCTC(native_config)
    state=load_file(str(weights));model.load_state_dict(state,strict=True,assign=True);del state
    if any(p.is_meta for p in model.parameters()):raise ValueError('Incomplete native strict materialization')
    model=model.to('cuda');check()
    splits=[{k:row[k] for k in ('id','role','target_ids')} for row in manifest['cases']]
    identity={'base_sha256':MODEL_SHA,'vocabulary_sha256':manifest['vocabulary_sha256'],
        'frontend_sha256':hashlib.sha256(json.dumps(frontend_config,sort_keys=True).encode()).hexdigest(),
        'manifest_sha256':manifest['manifest_sha256'],
        'split_sha256':hashlib.sha256(json.dumps(splits,sort_keys=True).encode()).hexdigest(),
        'base_repo':MODEL,'base_revision':MODEL_REVISION,'source_sha256':manifest['source_parquet_sha256'],
        'metadata_sha256':manifest['metadata_sha256'],'implementation_sha256':{
            name:file_sha(Path(__file__).with_name(name+'.py')) for name in
            ('realized_phone_data','realized_phone_adaptation','kaggle_realized_phone_job')},
        'runtime_versions':{name:importlib.metadata.version(name) for name in
            ('torch','transformers','numpy','soundfile','duckdb','safetensors')},
        'native_implementation_sha256':file_sha(inspect.getfile(transformers.Wav2Vec2ForCTC)),
        'frontend_implementation_sha256':file_sha(inspect.getfile(type(processor))),
        'precision':'float32','attention':'eager','qualified':False,'production_changed':False}
    report=train_adapter(model,rows,identity,output,max_epochs=20,resource_check=check)
    print(json.dumps({'event':'realized_phone.complete','best_epoch':report['best_epoch'],
        'baseline_test_per':report['baseline']['test']['phone_per'],
        'adapted_test_per':report['final_test']['phone_per'],'qualified':False}),flush=True)
    weights.unlink();signal.alarm(0)
    return report



def build_launcher(sources):
    """Embed code only; provider/source/device guard precedes pip and unpacking."""
    import base64
    import zlib
    allowed={'ml/__init__.py','ml/training/__init__.py','ml/training/realized_phone_data.py',
             'ml/training/realized_phone_adaptation.py','ml/training/kaggle_realized_phone_job.py'}
    if not isinstance(sources,dict) or not set(sources)<=allowed:
        raise ValueError('Only explicit research Python sources may enter private launcher')
    for name,source in sources.items():compile(source,name,'exec')
    encoded=base64.b85encode(zlib.compress(json.dumps(sources,sort_keys=True).encode(),9)).decode()
    return """import base64,json,platform,signal,subprocess,sys,time,zlib
from pathlib import Path
started=time.monotonic();deadline=started+7100
working=Path('/kaggle/working');inputs=Path('/kaggle/input')
if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64') or not working.is_dir() or not inputs.is_dir():
 raise RuntimeError('Existing Linux/x86 Kaggle context required before pip or source unpack')
sources=list(inputs.rglob('source-manifest.json'))
if len(sources)!=1:raise RuntimeError('Exactly one private Kaggle source input required')
source=sources[0].parent.resolve()
if not source.is_relative_to(inputs.resolve()):raise RuntimeError('Private input containment required')
subprocess.run(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],check=True,timeout=30)
signal.alarm(max(1,int(deadline-time.monotonic())))
subprocess.run([sys.executable,'-m','pip','install','--quiet','--disable-pip-version-check',
 'transformers==4.57.6','numpy==2.2.6','soundfile==0.13.1','duckdb==1.4.1'],check=True,timeout=600)
encoded=__ENCODED__
files=json.loads(zlib.decompress(base64.b85decode(encoded)))
base=Path('/kaggle/temp/qari-realized-source');base.mkdir(parents=True,exist_ok=True)
for name,code in files.items():
 path=base/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(code)
sys.path.insert(0,str(base))
from ml.training.kaggle_realized_phone_job import run
run(source,working/'realized-phone-output',deadline)
""".replace('__ENCODED__',repr(encoded))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();deadline=time.monotonic()+7100
    run(Path(args.input),Path(args.output),deadline)


if __name__=='__main__':main()
