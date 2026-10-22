"""Synthetic contracts only: never ship gated audio or transcript fixtures."""
import copy
import hashlib
import importlib
import json

import pytest


def module():
    return importlib.import_module('ml.training.realized_phone_data')


NATIVE_TOKENS = ['$','$$','*','**','<','<<','A','AA','AH','D','DD','E','EE','H','HH','I','II',
    'S','SS','T','TT','U','UU','Z','ZZ','^','^^','a','aa','b','bb','d','dd','f','ff','g','gg','h','hh',
    'i','ii','j','jj','k','kk','l','ll','m','mm','n','nn','p','pp','q','qq','r','rr','s','sh','sil',
    'ss','t','th','tt','u','uu','v','w','ww','x','xx','y','yy','z','zz','|','[UNK]','[PAD]','<s>','</s>']
VOCAB = {token:i for i,token in enumerate(NATIVE_TOKENS)}
REVISION='4e996ef87c6d1da517a4f21bca91e0d577dd8c82'
SOURCE_SHA='9b0fed74472edd02c1f787839e51a7523df9fd32df7e98c9857d8cc30366b84c'


def metadata_sha(rows):
    return hashlib.sha256((json.dumps(rows,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()


def corpus():
    rows=[];cases=[]
    for p in range(10):
        for i in range(133):
            name=f'{p:04}_{i}'
            suffix=chr(97+i//26)+chr(97+i%26)
            rows.append({'id':name,'sentence':'reference '+suffix,'phoneme_ref':'expected '+suffix,
                         'phoneme_mis':'q u l','audio_path':None})
            cases.append({'id':name,'id_prefix_group':name.rsplit('_',1)[0],
                'encoded_sha256':hashlib.sha256(('encoded:'+name).encode()).hexdigest(),
                'encoded_bytes':32044,'accepted':True,'reason':None,
                'original_sample_rate':16000,'channels':1,'source_frames':16000,'source_format':'WAV',
                'sample_count':16000,'float_pcm_sha256':hashlib.sha256(('pcm:'+name).encode()).hexdigest(),
                'rms':.1,'duration_seconds':1.0})
    audit={'dataset':'IqraEval/Iqra_Extra_IS26','revision':REVISION,'source_parquet_sha256':SOURCE_SHA,
        'full_parquet_sha_verified':True,'metadata_matches_pinned_file':True,'rows':len(rows),
        'metadata_sha256':metadata_sha(rows),'physical_speaker_identity_verified':False,'cases':cases}
    return rows,audit


def test_realized_targets_preserve_native_ids_case_geminates_and_delimiters():
    target=module().realized_targets({'phoneme_ref':'wrong canonical','phoneme_mis':'q u l'},VOCAB)
    assert target==[53,75,64,75,45]
    assert module().realized_targets({'phoneme_mis':'u U b bb'},VOCAB)==[64,75,21,75,29,75,30]


@pytest.mark.parametrize('value',[None,'','unknown_phone','[PAD]','|','[UNK]','<s>'])
def test_missing_or_invalid_realized_phones_never_fall_back_to_canonical(value):
    with pytest.raises(ValueError):
        module().realized_targets({'phoneme_ref':'q u l','phoneme_mis':value},VOCAB)


def test_native_vocabulary_cannot_reindex_blank_or_phone_symbols():
    changed=dict(VOCAB);changed['u'],changed['U']=changed['U'],changed['u']
    with pytest.raises(ValueError,match='vocab|native'):
        module().realized_targets({'phoneme_mis':'u'},changed)


def test_manifest_has_collection_content_disjoint_roles_without_claiming_verified_speakers():
    rows,audit=corpus();manifest=module().build_realized_manifest(rows,audit,VOCAB)
    module().validate_realized_manifest(manifest)
    assert manifest['qualified'] is False and manifest['production_changed'] is False
    assert manifest['physical_speaker_identity_verified'] is False
    role_groups={role:{r['id_prefix_group'] for r in manifest['cases'] if r['role']==role}
                 for role in ('train','validation','test')}
    role_contents={role:{r['content_group'] for r in manifest['cases'] if r['role']==role}
                   for role in role_groups}
    assert len(role_groups['validation'])==2 and len(role_groups['test'])==3
    for left,right in [('train','validation'),('train','test'),('validation','test')]:
        assert role_groups[left].isdisjoint(role_groups[right])
        assert role_contents[left].isdisjoint(role_contents[right])
    assert any(r['role']=='cross_group_quarantine' for r in manifest['cases'])
    assert len(manifest['cases'])==1330
    assert all(r['target_ids']==[53,75,64,75,45] for r in manifest['cases'])
    manifest['physical_speaker_identity_verified']=True
    with pytest.raises(ValueError,match='speaker'):module().validate_realized_manifest(manifest)


def test_split_order_aliases_and_sparse_prefixes_do_not_create_leakage():
    rows,audit=corpus()
    rows[1]['sentence']=rows[0]['sentence']+'َ'
    # Reusing an expected phone sequence also aliases otherwise different content.
    rows[2]['phoneme_ref']=rows[0]['phoneme_ref']
    split=module().split_realized_sources(rows,audit)
    by_id={r['id']:r for r in split}
    assert by_id['0000_0']['content_group']==by_id['0000_1']['content_group']==by_id['0000_2']['content_group']
    reversed_split=module().split_realized_sources(list(reversed(rows)),audit)
    assert {r['id']:(r['role'],r['content_group']) for r in split}=={
        r['id']:(r['role'],r['content_group']) for r in reversed_split}
    keep=[r for r in rows if not r['id'].startswith('0000_') or int(r['id'].split('_')[1])<3]
    sparse=module().split_realized_sources(keep,{**audit,'cases':[r for r in audit['cases'] if any(x['id']==r['id'] for x in keep)]})
    assert all(r['prefix_role']=='train' for r in sparse if r['id'].startswith('0000_'))


@pytest.mark.parametrize('change',['duplicate_id','accepted_duplicate_pcm','revision','metadata','quiet_accepted'])
def test_inconsistent_source_audit_rejects_instead_of_silently_changing_training(change):
    rows,audit=corpus()
    if change=='duplicate_id':rows[1]['id']=rows[0]['id'];audit['metadata_sha256']=metadata_sha(rows)
    if change=='accepted_duplicate_pcm':audit['cases'][1]['float_pcm_sha256']=audit['cases'][0]['float_pcm_sha256']
    if change=='revision':audit['revision']='0'*40
    if change=='metadata':rows[0]['phoneme_mis']='b';
    if change=='quiet_accepted':audit['cases'][0]['rms']=.0001
    with pytest.raises(ValueError):module().build_realized_manifest(rows,audit,VOCAB)


def test_unrepresentable_ctc_is_not_trained_and_held_per_keeps_the_case():
    rows,audit=corpus();first=module().build_realized_manifest(rows,audit,VOCAB)
    wanted=[next(r['id'] for r in first['cases'] if r['role']==role) for role in ('train','validation')]
    for row in rows:
        if row['id'] in wanted:row['phoneme_mis']='q u l q u l q'
    for case in audit['cases']:
        if case['id'] in wanted:case.update(sample_count=4000,source_frames=4000,duration_seconds=.25)
    audit['metadata_sha256']=metadata_sha(rows)
    manifest=module().build_realized_manifest(rows,audit,VOCAB)
    by_id={r['id']:r for r in manifest['cases']}
    train,held=(by_id[i] for i in wanted)
    assert train['native_output_frames']==12 and train['ctc_required_frames']==13
    assert train['role']=='train' and not train['training_eligible']
    assert held['role']=='validation' and held['evaluation_eligible']
    assert not held['ctc_representable']
