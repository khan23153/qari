"""Bounded native CTC adaptation to human REALIZED phones. Never live grading."""
import hashlib
import json
import math
from pathlib import Path
import random
import re

import numpy as np
import torch
import torch.nn.functional as F

from ml.training.realized_phone_data import BLANK, DELIMITER, native_output_frames

RECIPE={'seed':42,'lr':1e-5,'weight_decay':.01,'betas':[.9,.999],'eps':1e-8,
        'clip_norm':1.,'effective_batch':16,'microbatch':2,'max_epochs':20,
        'patience':4,'min_epochs':3,'precision':'float32','attention':'eager',
        'selection':'validation_aggregate_phone_per','target':'human_realized_native_delimited'}
IDENTITY_KEYS={'base_sha256','vocabulary_sha256','frontend_sha256','manifest_sha256','split_sha256'}


def _identity(identity):
    if (not isinstance(identity,dict) or not IDENTITY_KEYS<=identity.keys()
            or any(not isinstance(identity[k],str) or re.fullmatch('[0-9a-f]{64}',identity[k]) is None
                   for k in IDENTITY_KEYS)):
        raise ValueError('Immutable base/frontend/vocabulary/data/split identity required')
    # Safe checkpoint metadata consists only of JSON primitives.
    return json.loads(json.dumps(identity,allow_nan=False))


def adapter_keys(model):
    layers=len(model.wav2vec2.encoder.layers)
    if (layers<2 or model.config.vocab_size!=80 or model.config.pad_token_id!=BLANK
            or list(model.config.conv_kernel)!=[10,3,3,3,3,2,2]
            or list(model.config.conv_stride)!=[5,2,2,2,2,2,2]
            or model.config.ctc_zero_infinity or model.config.ctc_loss_reduction!='mean'):
        raise ValueError('Original native CTC configuration required')
    prefixes=tuple(f'wav2vec2.encoder.layers.{i}.' for i in (layers-2,layers-1))+('lm_head.',)
    return sorted(n for n,_ in model.named_parameters() if n.startswith(prefixes))


def freeze_adapter(model):
    allowed=adapter_keys(model)
    model.requires_grad_(False)
    model.freeze_feature_encoder()
    model.gradient_checkpointing_disable()
    model.config._attn_implementation='eager'
    for name,p in model.named_parameters():p.requires_grad_(name in allowed)
    return allowed


def frozen_digest(model):
    allowed=set(adapter_keys(model));digest=hashlib.sha256()
    for name,value in sorted(model.state_dict().items()):
        if name in allowed:continue
        value=value.detach().cpu().contiguous()
        digest.update(json.dumps([name,list(value.shape),str(value.dtype)]).encode())
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def decode_phones(path):
    result=[];previous=None
    for token in path:
        token=int(token)
        if not 0<=token<80:raise ValueError('Native prediction outside vocabulary')
        if token!=previous and token not in (BLANK,DELIMITER):result.append(token)
        previous=token
    return result


def _distance(a,b):
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]
        for j,y in enumerate(b,1):
            current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=current
    return previous[-1]


def _batch(batch,device):
    lengths=[len(r['input_values']) for r in batch]
    values=torch.zeros(len(batch),max(lengths),dtype=torch.float32,device=device)
    mask=torch.zeros_like(values,dtype=torch.long)
    for i,row in enumerate(batch):
        values[i,:lengths[i]]=row['input_values'].to(device=device,dtype=torch.float32)
        mask[i,:lengths[i]]=1
    return {'input_values':values,'attention_mask':mask},torch.tensor(
        [native_output_frames(n) for n in lengths],dtype=torch.long,device=device)


def _finite(value,what):
    if not torch.isfinite(value).all():raise ValueError(f'Nonfinite {what}')


def evaluate(model,rows,*,microbatch=2,resource_check=lambda:None):
    device=next(model.parameters()).device;predictions=[];errors=total=0
    model.eval()
    with torch.no_grad(),torch.autocast(device.type,enabled=False):
        for offset in range(0,len(rows),microbatch):
            resource_check();batch=rows[offset:offset+microbatch]
            inputs,lengths=_batch(batch,device);logits=model(**inputs).logits
            _finite(logits,'evaluation logits')
            paths=logits.argmax(-1).cpu().tolist()
            for row,path,n in zip(batch,paths,lengths.tolist()):
                heard=decode_phones(path[:n]);reference=[t for t in row['target_ids'] if t!=DELIMITER]
                error=_distance(reference,heard);errors+=error;total+=len(reference)
                predictions.append({'id':row['id'],'role':row['role'],'reference_ids':reference,
                                    'predicted_ids':heard,'errors':error,'reference_phones':len(reference)})
    return {'errors':errors,'reference_phones':total,'phone_per':errors/total if total else None,
            'predictions':predictions}


def _validate_rows(rows):
    if not isinstance(rows,list) or not rows:raise ValueError('Explicit bounded rows required')
    ids=set()
    for row in rows:
        values=row.get('input_values');target=row.get('target_ids')
        if (not isinstance(row.get('id'),str) or row['id'] in ids
                or row.get('role') not in ('train','validation','test')
                or not isinstance(values,torch.Tensor) or values.ndim!=1
                or values.dtype!=torch.float32 or not 4000<=len(values)<=480000
                or not isinstance(target,list) or not 1<=len(target)<=999
                or any(type(t) is not int or t in (76,77,78,79) or not 0<=t<80 for t in target)
                or any((t==DELIMITER)!=(i%2==1) for i,t in enumerate(target))
                or target[-1]==DELIMITER):
            raise ValueError('Explicit native audio/realized phone rows required')
        _finite(values,'audio input');ids.add(row['id'])
        if row['role']=='train' and native_output_frames(len(values))<len(target):
            raise ValueError('Unrepresentable CTC training row')
    if {r['role'] for r in rows}!={'train','validation','test'}:
        raise ValueError('Train/validation/test all required')


def _save_json(path,value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def load_delta(model,path,identity):
    identity=_identity(identity)
    packet=torch.load(path,map_location='cpu',weights_only=True)
    allowed=set(adapter_keys(model));original=model.state_dict()
    if (not isinstance(packet,dict) or set(packet)!={'schema','identity','recipe','state_dict','frozen_base_sha256'}
            or packet['schema']!='native_realized_phone_delta_v1' or packet['identity']!=identity
            or packet['recipe']!=RECIPE or packet['frozen_base_sha256']!=frozen_digest(model)
            or not isinstance(packet['state_dict'],dict)
            or set(packet['state_dict'])!=allowed):
        raise ValueError('Delta base identity/recipe/exact whitelist mismatch')
    for name,value in packet['state_dict'].items():
        if (not isinstance(value,torch.Tensor) or value.shape!=original[name].shape
                or value.dtype!=torch.float32 or not torch.isfinite(value).all()):
            raise ValueError('Delta shape/dtype/nonfinite tensor mismatch')
    # Validate the whole packet before touching any model parameter.
    with torch.no_grad():
        for name,value in packet['state_dict'].items():original[name].copy_(value)
    return packet


def train_adapter(model,rows,identity,output,*,max_epochs=20,microbatch=2,
                  resource_check=lambda:None):
    device=next(model.parameters()).device
    # Never create output/optimizer before proving the local experiment bound.
    if device.type!='cuda' and (len(rows)>32 or max_epochs>2
                                or sum(p.numel() for p in model.parameters())>1_000_000):
        raise ValueError('Local fixture bound: 32 rows/2 epochs/1M parameters')
    if type(max_epochs) is not int or not 1<=max_epochs<=20 or type(microbatch) is not int or not 1<=microbatch<=16:
        raise ValueError('Invalid bounded training recipe')
    identity=_identity(identity);_validate_rows(rows);allowed=freeze_adapter(model)
    if any(p.dtype!=torch.float32 for p in model.parameters()):raise ValueError('Native FP32 weights required')
    for p in model.parameters():_finite(p,'initial parameter')
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    if device.type=='cuda':torch.cuda.manual_seed_all(42)
    output=Path(output)
    if (output/'candidate-delta.pt').exists():raise ValueError('Refuse to overwrite an existing candidate')
    output.mkdir(parents=True,exist_ok=True)
    frozen_before=frozen_digest(model)
    grouped={role:[r for r in rows if r['role']==role] for role in ('train','validation','test')}
    report={'qualified':False,'production_changed':False,'identity':identity,'recipe':dict(RECIPE),
            'requested_epochs':max_epochs,'actual_microbatch':microbatch,
            'frozen_before_sha256':frozen_before,'history':[]}
    with torch.autocast(device.type,enabled=False):
        report['baseline']={role:evaluate(model,grouped[role],microbatch=microbatch,
                                         resource_check=resource_check) for role in ('validation','test')}
        optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
            lr=1e-5,weight_decay=.01,betas=(.9,.999),eps=1e-8)
        best=math.inf;best_state=None;best_epoch=None;stale=0
        generator=torch.Generator().manual_seed(42)
        for epoch in range(1,max_epochs+1):
            model.train();order=torch.randperm(len(grouped['train']),generator=generator).tolist()
            training=[grouped['train'][i] for i in order];epoch_loss=0.
            for start in range(0,len(training),16):
                group=training[start:start+16];optimizer.zero_grad(set_to_none=True)
                for offset in range(0,len(group),microbatch):
                    resource_check();batch=group[offset:offset+microbatch]
                    inputs,lengths=_batch(batch,device);logits=model(**inputs).logits.float()
                    _finite(logits,'training logits')
                    labels=[r['target_ids'] for r in batch]
                    targets=torch.tensor([t for row in labels for t in row],dtype=torch.long,device=device)
                    target_lengths=torch.tensor([len(row) for row in labels],dtype=torch.long,device=device)
                    losses=F.ctc_loss(logits.log_softmax(-1).transpose(0,1),targets,lengths,
                        target_lengths,blank=BLANK,reduction='none',zero_infinity=False)/target_lengths
                    _finite(losses,'CTC loss');loss=losses.sum()/len(group)
                    loss.backward();epoch_loss+=float(losses.detach().sum())
                params=[p for p in model.parameters() if p.requires_grad]
                for p in params:
                    if p.grad is not None:_finite(p.grad,'gradient')
                norm=torch.nn.utils.clip_grad_norm_(params,1.,error_if_nonfinite=True)
                _finite(norm,'gradient norm');optimizer.step()
                for p in params:_finite(p,'updated parameter')
                resource_check()
            validation=evaluate(model,grouped['validation'],microbatch=microbatch,resource_check=resource_check)
            score=validation['phone_per']
            report['history'].append({'epoch':epoch,'train_ctc_loss':epoch_loss/len(training),
                                      'validation':validation})
            print(json.dumps({'event':'realized_phone.epoch','epoch':epoch,'validation_phone_per':score,
                              'train_ctc_loss':epoch_loss/len(training)}),flush=True)
            if score<best:
                best=score;best_epoch=epoch;stale=0
                best_state={n:model.state_dict()[n].detach().cpu().clone() for n in allowed}
            else:stale+=1
            if epoch>=3 and stale>=4:break
        with torch.no_grad():
            for name,value in best_state.items():model.state_dict()[name].copy_(value)
        report['best_epoch']=best_epoch
        report['final_validation']=evaluate(model,grouped['validation'],microbatch=microbatch,resource_check=resource_check)
        report['final_test']=evaluate(model,grouped['test'],microbatch=microbatch,resource_check=resource_check)
        report['frozen_after_sha256']=frozen_digest(model)
        if report['frozen_after_sha256']!=frozen_before:raise ValueError('Frozen base state changed')
        resource_check()
        packet={'schema':'native_realized_phone_delta_v1','identity':identity,'recipe':dict(RECIPE),
                'state_dict':best_state,'frozen_base_sha256':frozen_before}
        temporary=output/'candidate-delta.pending'
        torch.save(packet,temporary);temporary.replace(output/'candidate-delta.pt')
    _save_json(output/'training-report.json',report)
    _save_json(output/'baseline-predictions.json',report['baseline'])
    _save_json(output/'phone-predictions.json',{'validation':report['final_validation'],'test':report['final_test']})
    _save_json(output/'readiness.json',{'qualified':False,'production_changed':False,
        'reason':'Human phone PER research; Quran grading and streaming latency unqualified',
        'base_training_overlap':'unknown','physical_speaker_identity_verified':False})
    return report
