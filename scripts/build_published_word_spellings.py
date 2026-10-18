"""Compile literal Hafs spelling identities; never use recognition predictions.

PYTHONPATH=.:backend/recitation_api python scripts/build_published_word_spellings.py
    --source /private/published-quran-simple-clean.json
    --reference-dir backend/recitation_api/reference_data --output /tmp/spellings.json
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from app.services.streaming_session import _normalize

SOURCE_SHA256 = 'e9f87186120851fbf1e04813a423076850e1b6b9ad769a797117dca623aad4af'


def normalize(text):
    return _normalize(text, use_published_spelling=False)


def units(tokens):
    """Canonicalize printed vocative boundaries for edition comparison only."""
    result=[]
    for token,index in tokens:
        key=normalize(token)
        if not key:continue
        if result and result[-1]['key']=='يا':
            result[-1]['raw']+=token
            result[-1]['key']+=key
            result[-1]['input_tokens']+=1
        else:result.append({'raw':token,'key':key,'index':index,'input_tokens':1})
    return result


def build(source, reference_dir):
    assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA256
    data=json.loads(source.read_text(encoding='utf-8'))['data']
    targets=defaultdict(set);raw_targets=defaultdict(set)
    examples=defaultdict(list);raw_examples=defaultdict(list)
    skipped=[];compared=0
    for surah in data['surahs']:
        for ayah in surah['ayahs']:
            number,verse=surah['number'],ayah['numberInSurah']
            reference=json.loads((reference_dir/f'{number}_{verse}.json').read_text(encoding='utf-8'))
            # Keep only the actual word, excluding separate pause ornaments.
            printed_tokens=[]
            for index,word in enumerate(reference['words']):
                parts=[t for t in (word.get('text_with_tashkeel') or word['word']).split() if normalize(t)]
                if len(parts)!=1:continue
                printed_tokens.append((parts[0],index))
            printed=units(printed_tokens)
            simple=units([(t,i)for i,t in enumerate(ayah['text'].split())])
            if len(printed)!=len(simple):
                skipped.append([number,verse,len(printed),len(simple)]);continue
            for uthmani,imlai in zip(printed,simple):
                compared+=1;key,value=uthmani['key'],imlai['key']
                targets[key].add(value)
                location={'surah':number,'ayah':verse,'word_index':uthmani['index']}
                examples[key,value].append(dict(location,uthmani=uthmani['raw'],imlai=imlai['raw']))
                if uthmani['input_tokens']==1:
                    raw_targets[uthmani['raw']].add(value)
                    raw_examples[uthmani['raw'],value].append(dict(location,imlai=imlai['raw']))
    raw_spellings=[]
    for raw,values in sorted(raw_targets.items()):
        if len(values)!=1:continue
        value=next(iter(values))
        if normalize(raw)==value:continue
        rows=raw_examples[raw,value]
        raw_spellings.append({'uthmani':raw,'imlai':rows[0]['imlai'],
                              'attestations':[{k:r[k]for k in ['surah','ayah','word_index']}for r in rows]})
    ambiguous=[]
    for key,values in sorted(targets.items()):
        if len(values)!=1:
            ambiguous.append({'uthmani_key':key,'imlai_keys':sorted(values)});continue
    manifest={'provenance':{'source_url':'https://api.alquran.cloud/v1/quran/quran-simple-clean',
                            'source_sha256':SOURCE_SHA256,
                            'reference':'immutable reference_data word.text_with_tashkeel',
                            'method':'same-ayah complete lexical-unit alignment; vocatives grouped only in edition comparison; exact raw identity before lossy normalization',
                            'compared_tokens':compared,'skipped_ayah_count':len(skipped)},
              'raw_spellings':raw_spellings}
    return manifest,{'compared_tokens':compared,'raw_spellings':len(raw_spellings),
                     'ambiguous':ambiguous,'skipped':skipped}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--reference-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--audit',type=Path)
    args=parser.parse_args()
    manifest,audit=build(args.source,args.reference_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.audit:args.audit.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items()if k not in ['ambiguous','skipped']}))
