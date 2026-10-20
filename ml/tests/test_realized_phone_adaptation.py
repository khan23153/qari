"""Small actual native-model contracts; no gated data or pretrained weights."""
import copy
import importlib
from pathlib import Path

import pytest

torch=pytest.importorskip('torch')
transformers=pytest.importorskip('transformers')


def module():
    return importlib.import_module('ml.training.realized_phone_adaptation')


def tiny():
    torch.manual_seed(42)
    config=transformers.Wav2Vec2Config(vocab_size=80,pad_token_id=77,
        hidden_size=16,num_hidden_layers=3,num_attention_heads=2,intermediate_size=32,
        conv_dim=(8,)*7,conv_kernel=(10,3,3,3,3,2,2),conv_stride=(5,2,2,2,2,2,2),
        num_conv_pos_embedding_groups=2,num_conv_pos_embeddings=16,feat_extract_norm='layer',
        hidden_dropout=0.,attention_dropout=0.,activation_dropout=0.,feat_proj_dropout=0.,
        final_dropout=0.,layerdrop=0.,mask_time_prob=0.,mask_feature_prob=0.,
        ctc_loss_reduction='mean',ctc_zero_infinity=False)
    config._attn_implementation='eager'
    return transformers.Wav2Vec2ForCTC(config)


def rows(n=5):
    return [{'id':str(i),'role':'train' if i<n-2 else 'validation' if i==n-2 else 'test',
             'input_values':torch.sin(torch.arange(4000+i*100)*.037+i).float(),
             'target_ids':[53,75,64,75,45]} for i in range(n)]


def identity():
    return {k:str(i)*64 for i,k in enumerate(('base_sha256','vocabulary_sha256',
        'frontend_sha256','manifest_sha256','split_sha256'),1)}


def test_blank_aware_decoder_retains_real_zero_and_special_predictions():
    assert module().decode_phones([0,0,77,0,75,64,64,77,64,76,79])==[0,0,64,64,76,79]


def test_freeze_native_feature_encoder_prevents_whole_backbone_graph():
    model=tiny();allowed=module().freeze_adapter(model)
    assert set(allowed)=={n for n,p in model.named_parameters() if p.requires_grad}
    assert all(n.startswith(('wav2vec2.encoder.layers.1.','wav2vec2.encoder.layers.2.','lm_head.')) for n in allowed)
    assert not model.wav2vec2.feature_extractor._requires_grad
    seen=[]
    handle=model.wav2vec2.encoder.layers[0].register_forward_pre_hook(lambda m,args:seen.append(args[0].requires_grad))
    model.train();model(input_values=rows()[0]['input_values'][None]).logits.sum().backward();handle.remove()
    assert seen==[False]


def test_actual_native_training_updates_only_allowed_and_delta_roundtrips(tmp_path):
    model=tiny();original=copy.deepcopy(model);before={k:v.clone() for k,v in model.state_dict().items()}
    report=module().train_adapter(model,rows(),identity(),tmp_path,max_epochs=2)
    allowed=set(module().adapter_keys(model))
    assert any(not torch.equal(before[k],model.state_dict()[k]) for k in allowed)
    assert all(torch.equal(before[k],model.state_dict()[k]) for k in before.keys()-allowed)
    assert report['frozen_before_sha256']==report['frozen_after_sha256']
    assert report['qualified'] is False and report['production_changed'] is False
    assert len(report['history'])==2 and len(report['baseline']['test']['predictions'])==1
    assert report['final_test']['reference_phones']==3
    assert model.config.pad_token_id==77 and model.config.vocab_size==80
    module().load_delta(original,tmp_path/'candidate-delta.pt',identity())
    model.eval();original.eval();x=rows()[0]['input_values'][None]
    assert torch.equal(model(x).logits,original(x).logits)
    assert all(p.dtype==torch.float32 for p in model.parameters())


def test_partial_microbatches_weight_actual_samples_like_one_full_batch(tmp_path):
    one=tiny();two=copy.deepcopy(one)
    module().train_adapter(one,rows(),identity(),tmp_path/'one',max_epochs=1,microbatch=1)
    module().train_adapter(two,rows(),identity(),tmp_path/'two',max_epochs=1,microbatch=3)
    for key in module().adapter_keys(one):
        assert torch.allclose(one.state_dict()[key],two.state_dict()[key],atol=2e-7,rtol=1e-5),key


def test_caller_autocast_does_not_change_fp32_training(tmp_path):
    one=tiny();two=copy.deepcopy(one)
    module().train_adapter(one,rows(),identity(),tmp_path/'one',max_epochs=1)
    with torch.autocast('cpu',dtype=torch.bfloat16):
        module().train_adapter(two,rows(),identity(),tmp_path/'two',max_epochs=1)
    for key in module().adapter_keys(one):assert torch.equal(one.state_dict()[key],two.state_dict()[key]),key


@pytest.mark.parametrize('kind',['rows','epochs','parameters'])
def test_local_caps_reject_before_outputs_or_optimizer(tmp_path,monkeypatch,kind):
    model=tiny();data=rows();epochs=1
    if kind=='rows':data=rows(33)
    if kind=='epochs':epochs=3
    if kind=='parameters':model.extra=torch.nn.Parameter(torch.zeros(1_000_001))
    def forbidden(*a,**k):raise AssertionError('optimizer initialized before guard')
    monkeypatch.setattr(torch.optim,'AdamW',forbidden)
    with pytest.raises(ValueError,match='local|fixture|bound'):
        module().train_adapter(model,data,identity(),tmp_path/'absent',max_epochs=epochs)
    assert not (tmp_path/'absent').exists()


@pytest.mark.parametrize('kind',['input','loss','gradient'])
def test_nonfinite_fails_without_candidate(tmp_path,kind):
    model=tiny();data=rows()
    if kind=='input':data[0]['input_values'][0]=float('nan')
    if kind=='loss':
        model.lm_head.register_forward_hook(lambda m,a,out:out*float('nan'))
    if kind=='gradient':model.lm_head.weight.register_hook(lambda g:g*float('nan'))
    with pytest.raises((ValueError,RuntimeError),match='finite'):
        module().train_adapter(model,data,identity(),tmp_path,max_epochs=1)
    assert not (tmp_path/'candidate-delta.pt').exists()


@pytest.mark.parametrize('change',['missing','extra','shape','nonfinite','identity'])
def test_delta_rejects_malformed_or_different_base(tmp_path,change):
    model=tiny();module().train_adapter(model,rows(),identity(),tmp_path,max_epochs=1)
    path=tmp_path/'candidate-delta.pt';packet=torch.load(path,weights_only=True)
    key=next(iter(packet['state_dict']))
    if change=='missing':packet['state_dict'].pop(key)
    if change=='extra':packet['state_dict']['lm_head.other']=torch.zeros(1)
    if change=='shape':packet['state_dict'][key]=torch.zeros(1)
    if change=='nonfinite':packet['state_dict'][key].view(-1)[0]=float('nan')
    if change=='identity':packet['identity']['base_sha256']='0'*64
    torch.save(packet,path)
    target=tiny();before={k:v.clone() for k,v in target.state_dict().items()}
    with pytest.raises(ValueError):module().load_delta(target,path,identity())
    assert all(torch.equal(before[k],target.state_dict()[k]) for k in before)


def test_delta_rejects_different_actual_frozen_base_even_with_same_claimed_identity(tmp_path):
    source=tiny();module().train_adapter(source,rows(),identity(),tmp_path,max_epochs=1)
    target=tiny()
    with torch.no_grad():target.wav2vec2.feature_projection.projection.weight.add_(.01)
    before={k:v.clone() for k,v in target.state_dict().items()}
    with pytest.raises(ValueError,match='frozen|base'):
        module().load_delta(target,tmp_path/'candidate-delta.pt',identity())
    assert all(torch.equal(before[k],target.state_dict()[k]) for k in before)


def test_evaluation_never_passes_target_text_and_keeps_unrepresentable_reference_denominator():
    model=tiny();data=rows()[3:];data[0]['target_ids']=[53,75]*20+[45]
    keys=[]
    handle=model.register_forward_pre_hook(lambda m,args,kwargs:keys.append(set(kwargs)),with_kwargs=True)
    result=module().evaluate(model,data);handle.remove()
    assert result['reference_phones']==24 and len(result['predictions'])==2
    assert keys and all(k=={'input_values','attention_mask'} for k in keys)
