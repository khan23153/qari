"""Pinned human realized-phone research contracts; no inference or live grading."""
import copy
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict

DATASET='IqraEval/Iqra_Extra_IS26'
REVISION='4e996ef87c6d1da517a4f21bca91e0d577dd8c82'
SOURCE_SHA='9b0fed74472edd02c1f787839e51a7523df9fd32df7e98c9857d8cc30366b84c'
VOCAB_SHA='35284b9210e55abef46e8e8c061cafa0324495b8f9998e012bfe1ff28a4311b1'
BLANK=77
DELIMITER=75
SPLIT_RULE='prospective_collection_content_split_v1'


def _json_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def _metadata_sha(rows):
    return hashlib.sha256((json.dumps(rows,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()


def _is_sha(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def _check_vocab(vocabulary):
    if (not isinstance(vocabulary,dict) or len(vocabulary)!=80
            or any(type(v) is not int for v in vocabulary.values())
            or set(vocabulary.values())!=set(range(80))
            or vocabulary.get('[PAD]')!=BLANK or vocabulary.get('|')!=DELIMITER
            or _json_sha(vocabulary)!=VOCAB_SHA):
        raise ValueError('Pinned native vocabulary/blank/delimiter identity required')


def realized_targets(row,vocabulary):
    """Keep the native between-phone delimiter convention; never canonical fallback."""
    _check_vocab(vocabulary)
    text=row.get('phoneme_mis')
    phones=text.split() if isinstance(text,str) else []
    if (not 1<=len(phones)<=500 or any(p not in vocabulary or p in
            ('|','[PAD]','[UNK]','<s>','</s>') for p in phones)):
        raise ValueError('Explicit valid human realized phones required')
    result=[]
    for phone in phones:
        if result:result.append(DELIMITER)
        result.append(vocabulary[phone])
    return result


def native_output_frames(samples):
    if type(samples) is not int or samples<=0:
        raise ValueError('Positive integer native sample count required')
    for kernel,stride in zip((10,3,3,3,3,2,2),(5,2,2,2,2,2,2)):
        samples=(samples-kernel)//stride+1
    return max(0,samples)


def _normalize_content(text):
    if not isinstance(text,str):raise ValueError('Reference content text required')
    text=unicodedata.normalize('NFKC',text).translate(str.maketrans(
        {'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ـ':''}))
    text=' '.join(''.join(c for c in text if c.isalpha() or c.isspace()).split())
    if not text:raise ValueError('Nonempty normalized reference content required')
    return text


def _source_map(metadata,audit):
    if not isinstance(metadata,list) or not 1<=len(metadata)<=1330:
        raise ValueError('Bounded human source rows required')
    ids=[r.get('id') for r in metadata]
    if (any(not isinstance(i,str) or re.fullmatch(r'\d+_\d+',i) is None for i in ids)
            or len(set(ids))!=len(ids)):
        raise ValueError('Unique source IDs with preserved numeric prefix required')
    records=audit.get('cases',[])
    sources={r.get('id'):r for r in records}
    if len(sources)!=len(records) or set(sources)!=set(ids):
        raise ValueError('Exact source audit/metadata identity required')
    return sources


def split_realized_sources(metadata,audit):
    """Collection/content disjoint roles. Prefixes are NOT verified speaker IDs."""
    sources=_source_map(metadata,audit)
    parent={r['id']:r['id'] for r in metadata}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    normalized={r['id']:_normalize_content(r.get('sentence')) for r in metadata}
    for selector in (lambda r:normalized[r['id']],
                     lambda r:' '.join(r.get('phoneme_ref','').split())):
        seen={}
        for row in metadata:
            key=selector(row)
            if not key:raise ValueError('Expected reference is required for content grouping only')
            if key in seen:union(row['id'],seen[key])
            else:seen[key]=row['id']
    groups=defaultdict(list)
    for row in metadata:groups[find(row['id'])].append(row['id'])
    representatives={k:min(normalized[i] for i in ids) for k,ids in groups.items()}
    ordered=sorted(groups,key=lambda k:hashlib.sha256(
        ('qari-real-phone-v1:content:'+representatives[k]).encode()).hexdigest())
    count=math.ceil(.15*len(ordered))
    content_roles={k:'validation' if i<count else 'test' if i<2*count else 'train'
                   for i,k in enumerate(ordered)}
    prefixes=Counter(r['id'].rsplit('_',1)[0] for r in metadata if sources[r['id']]['accepted'])
    eligible=sorted((k for k,n in prefixes.items() if n>=40),key=lambda k:hashlib.sha256(
        ('qari-real-phone-v1:prefix:'+k).encode()).hexdigest())
    prefix_roles={r['id'].rsplit('_',1)[0]:'train' for r in metadata}
    for k in eligible[:2]:prefix_roles[k]='validation'
    for k in eligible[2:5]:prefix_roles[k]='test'
    result=[]
    for row in metadata:
        name=row['id'];source=sources[name];prefix=name.rsplit('_',1)[0]
        group=find(name);pr,cr=prefix_roles[prefix],content_roles[group]
        role=('excluded_source_guard' if not source['accepted'] else pr if pr==cr
              else 'cross_group_quarantine')
        samples=source.get('sample_count')
        frames=native_output_frames(samples) if samples is not None else None
        # Targets insert one native delimiter between each original phone token.
        needed=2*len(row.get('phoneme_mis','').split())-1
        result.append({'id':name,'id_prefix_group':prefix,'prefix_role':pr,
            'content_group':hashlib.sha256(representatives[group].encode()).hexdigest(),
            'content_role':cr,'role':role,'native_output_frames':frames,
            'ctc_required_frames':needed,'ctc_representable':frames is not None and frames>=needed})
    return sorted(result,key=lambda r:r['id'])


def _validate_source_inputs(metadata,audit,vocabulary):
    _check_vocab(vocabulary)
    sources=_source_map(metadata,audit)
    if (audit.get('dataset')!=DATASET or audit.get('revision')!=REVISION
            or audit.get('source_parquet_sha256')!=SOURCE_SHA
            or audit.get('full_parquet_sha_verified') is not True
            or audit.get('metadata_matches_pinned_file') is not True
            or audit.get('rows')!=1330 or len(metadata)!=1330
            or audit.get('metadata_sha256')!=_metadata_sha(metadata)):
        raise ValueError('Pinned full source and actual metadata audit required')
    if audit.get('physical_speaker_identity_verified') is not False:
        raise ValueError('Collection groups cannot claim verified physical speakers')
    pcm=defaultdict(list)
    for name,s in sources.items():
        if type(s.get('accepted')) is not bool or s.get('id_prefix_group')!=name.rsplit('_',1)[0]:
            raise ValueError('Explicit audited source acceptance and prefix required')
        if (not _is_sha(s.get('encoded_sha256')) or type(s.get('encoded_bytes')) is not int
                or not 1<=s['encoded_bytes']<=3*1024**2):
            raise ValueError('Bounded source bytes/SHA required')
        if s.get('float_pcm_sha256') is not None:
            if not _is_sha(s['float_pcm_sha256']):raise ValueError('Actual PCM SHA required')
            pcm[s['float_pcm_sha256']].append(s)
        if s['accepted']:
            n=s.get('sample_count');rms=s.get('rms')
            if (s.get('original_sample_rate')!=16000 or s.get('channels')!=1
                    or s.get('source_format')!='WAV' or type(n) is not int
                    or not 4000<=n<=30*16000 or s.get('source_frames')!=n
                    or not _is_sha(s.get('float_pcm_sha256'))
                    or not isinstance(rms,(float,int)) or not math.isfinite(rms) or rms<.006
                    or s.get('reason') is not None):
                raise ValueError('Original source PCM/rate/duration/speech guards required')
        elif s.get('reason') not in ('original_speech_rms_guard','duration_guard','duplicate_pcm_quarantine'):
            raise ValueError('Only declared source-guard/quarantine exclusions allowed')
    if any(len(rows)>1 and any(r['accepted'] or r.get('reason')!='duplicate_pcm_quarantine'
                               for r in rows) for rows in pcm.values()):
        raise ValueError('Duplicate PCM must be quarantined in all source copies')
    for row in metadata:realized_targets(row,vocabulary)
    return sources


def _assemble_manifest(metadata,audit,vocabulary):
    sources=_validate_source_inputs(metadata,audit,vocabulary)
    rows={r['id']:r for r in metadata};cases=[]
    for split in split_realized_sources(metadata,audit):
        row=rows[split['id']];source=sources[split['id']]
        cases.append({**split,'target_ids':realized_targets(row,vocabulary),
            'encoded_sha256':source['encoded_sha256'],
            'float_pcm_sha256':source.get('float_pcm_sha256'),
            'sample_count':source.get('sample_count'),'rms':source.get('rms'),
            'training_eligible':split['role']=='train' and split['ctc_representable'],
            'evaluation_eligible':split['role'] in ('validation','test')})
    counts=dict(Counter(r['role'] for r in cases))
    if (sum(r['training_eligible'] for r in cases)<200 or counts.get('validation',0)<20
            or counts.get('test',0)<20):
        raise ValueError('Insufficient disjoint human-phone research support')
    result={'schema':'human_realized_phone_research_v1','label_type':'human_realized_phone',
        'split_rule':SPLIT_RULE,'dataset':DATASET,'revision':REVISION,
        'source_parquet_sha256':SOURCE_SHA,'metadata_sha256':audit['metadata_sha256'],
        'source_audit_sha256':_json_sha(audit),'vocabulary_sha256':_json_sha(vocabulary),
        'native_blank':BLANK,'native_delimiter':DELIMITER,'counts':counts,
        'physical_speaker_identity_verified':False,'qualified':False,'production_changed':False,
        'metadata':copy.deepcopy(metadata),'source_audit':copy.deepcopy(audit),
        'native_vocabulary':dict(vocabulary),'cases':cases}
    result['manifest_sha256']=_json_sha(result)
    return result


def build_realized_manifest(metadata,audit,vocabulary):
    return _assemble_manifest(metadata,audit,vocabulary)


def validate_realized_manifest(manifest):
    if (manifest.get('physical_speaker_identity_verified') is not False
            or manifest.get('source_audit',{}).get('physical_speaker_identity_verified') is not False):
        raise ValueError('Physical speaker verification is not established')
    expected=_assemble_manifest(manifest.get('metadata'),manifest.get('source_audit',{}),
                                manifest.get('native_vocabulary'))
    if manifest!=expected:raise ValueError('Human realized-phone manifest integrity changed')
