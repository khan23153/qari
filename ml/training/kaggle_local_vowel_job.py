"""Bounded frozen-phonetic local vowel research, never live grading."""
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np
import torch

from ml.training.human_word_data import REFERENCES, _normalize, parse_label_row
from ml.training.kaggle_human_word_job import decode_source_audio, fetch_public, prefetch_sources
from ml.training.kaggle_phoneme_job import check_resources, file_sha, write_json
from ml.training.local_vowel_data import local_word_crops, vowel_word_labels
from ml.training.local_vowel_head import _is_sha, _json_sha, _require_kaggle_cpu, train_local_vowel_features

DATASET = 'MuazAhmad7/Surah_Ikhlas-Labeled_Dataset'
REVISION = '973b5ef1d1532bcbe7e9a5a5b0dce125cc4d0dac'
MODEL = 'obadx/muaalem-model-v3_2'
MODEL_REVISION = '01a1ef9fbe40d144ef845101e89ff924aed3fef5'
MODEL_SHA = '6b6a2e85303d17ff0f3af5e1fc79ac83daecee409c756ddf27f0ced59393bb41'


def execution_device(scope, output):
    if scope=='kaggle_cpu':
        _require_kaggle_cpu(output)
        return 'cpu'
    if scope!='cuda':
        raise ValueError('Full research requires explicit remote CPU or CUDA scope')
    if not torch.cuda.is_available():
        raise RuntimeError('Private GPU required; full research never falls back to VPS CPU')
    return 'cuda'


def _native_emissions(probabilities):
    if (probabilities.ndim != 2 or probabilities.shape[1] != 43
            or not 1 <= len(probabilities) <= 600 or not np.isfinite(probabilities).all()
            or (probabilities < 0).any() or (probabilities > 1).any()
            or not np.allclose(probabilities.sum(-1), 1., atol=.001)):
        raise ValueError('Invalid native phoneme posterior matrix')
    path = probabilities.argmax(-1); start = 0; records = []
    for end in range(1, len(path)+1):
        if end < len(path) and path[end] == path[start]:
            continue
        token = int(path[start])
        if token:
            records.append({'id': token, 'start_frame': start, 'end_frame': end,
                            'confidence': float(probabilities[start:end, token].mean())})
        start = end
    return records


def native_frame_features(samples, processor, model, *, device='cuda'):
    """Native post-adapter states/logits; reference text is not an input."""
    if (not isinstance(samples, np.ndarray) or samples.dtype != np.float32 or samples.ndim != 1
            or not 4000 <= len(samples) <= 192000 or not np.isfinite(samples).all()
            or np.max(np.abs(samples)) > 1.01 or np.sqrt(np.mean(samples**2)) < .006):
        raise ValueError('Invalid bounded native speech input')
    features = processor(samples, sampling_rate=16000, return_tensors='pt')
    if set(features)-{'input_features', 'attention_mask'} or 'input_features' not in features:
        raise ValueError('Native processor returned unsupported acoustic inputs')
    features = {k: v.to(device) for k, v in features.items()}
    model.eval()
    with torch.inference_mode():
        hidden = model.wav2vec2_bert(**features).last_hidden_state
        if (hidden.ndim != 3 or hidden.shape[0] != 1 or hidden.shape[2] != 1024
                or not 1 <= hidden.shape[1] <= 600 or not torch.isfinite(hidden).all()):
            raise ValueError('Native encoder frame shape or identity mismatch')
        logits = model.level_to_lm_head['phonemes'](model.dropout(hidden))[0]
        probabilities = logits.softmax(-1, dtype=torch.float32).cpu().numpy()
        with np.errstate(over='ignore', invalid='ignore'):
            local = hidden[0].float().cpu().numpy().astype(np.float16)
    if not np.isfinite(local).all() or abs(len(local)-len(samples)/640) > 2:
        raise ValueError('Native feature frame timebase or finite cache mismatch')
    return local, _native_emissions(probabilities)


def validate_word_references(references):
    result = {}
    for ayah, row in references['ayahs'].items():
        # U+06E5/U+06E6 are Uthmani recitation marks, not lexical waw/ya.
        # Keep their actual phonetic IDs in the reference sequence below.
        lexical = _normalize(row['uthmani'].translate(str.maketrans('', '', 'ۥۦ'))).split()
        if (int(ayah) not in REFERENCES or lexical != REFERENCES[int(ayah)].split()
                or row['reference_ids'] != [t for word in row['word_reference_ids'] for t in word]
                or row['reference_word_indices'] != [i for i, word in enumerate(row['word_reference_ids']) for _ in word]
                or len(row['word_reference_ids']) != len(REFERENCES[int(ayah)].split())):
            raise ValueError('Original Quran word reference mapping changed')
        result[ayah] = row['word_reference_ids']
    return result


def prepare_local_vowel_features(audit, references, encode, cache, output, identity,
                                 *, fetch, deadline=None, device='cpu', crop_policy='exact_only_v1'):
    if device == 'kaggle_cpu':
        _require_kaggle_cpu(output)
    if (crop_policy not in ('exact_only_v1','unique_substitution_v1')
            or identity.get('crop_policy','exact_only_v1') != crop_policy):
        raise ValueError('Explicit crop policy must match immutable encoder identity')
    if (audit.get('dataset') != DATASET or audit.get('revision') != REVISION
            or not 1 <= len(audit['cases']) <= 1506
            or not _is_sha(identity.get('model_sha256'))
            or not _is_sha(identity.get('crop_implementation_sha256'))):
        raise ValueError('Pinned source audit and immutable native identity required')
    cache, output = Path(cache), Path(output)
    cache.mkdir(parents=True, exist_ok=True); output.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic()+7100 if deadline is None else deadline
    identity_sha = _json_sha(identity)
    result = {'label_type': 'human_vowel_word_error', 'dataset': DATASET, 'revision': REVISION,
              'reserved_speakers': audit['reserved_speakers'], 'encoder_identity': identity,
              'references': validate_word_references(references), 'sources': [], 'cases': [], 'qualified': False,
              'production_changed': False, 'source_bytes': 0, 'crop_policy': crop_policy}
    seen_ids, seen_pcm = set(), set()
    for source in audit['cases']:
        source_id, pcm = source['id'], source['float_pcm_sha256']
        if (not re.fullmatch(r'ID\d+V[1-4][TF]', source_id)
                or source['source_file'] != f'data/{source_id}.wav'
                or source_id in seen_ids or pcm in seen_pcm):
            raise ValueError('Source case or duplicate PCM quarantine changed')
        seen_ids.add(source_id); seen_pcm.add(pcm)
    for source, raw in prefetch_sources(audit['cases'], fetch):
        check_resources(output, device, deadline)
        if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != source['source_sha256']:
            raise ValueError('Public source SHA identity changed')
        result['source_bytes'] += len(raw)
        if result['source_bytes'] > 1000000000:
            raise ValueError('Public source total byte budget exceeded')
        samples = decode_source_audio(raw)
        if (len(samples) != source['sample_count']
                or hashlib.sha256(samples.astype('<f4', copy=False).tobytes()).hexdigest() != source['float_pcm_sha256']):
            raise ValueError('Actual source PCM identity changed')
        features, emissions = encode(samples)
        if (not isinstance(features, np.ndarray) or features.dtype != np.float16
                or features.ndim != 2 or features.shape[1] != 1024
                or abs(len(features)-len(samples)/640) > 2 or not np.isfinite(features).all()):
            raise ValueError('Native frame timebase or feature cache identity mismatch')
        ref = references['ayahs'][str(source['ayah'])]
        crops = local_word_crops(ref['reference_ids'], ref['reference_word_indices'], emissions, len(features),
                                allow_substitutions=crop_policy=='unique_substitution_v1')
        labels = vowel_word_labels(source)
        if len(crops) != len(labels):
            raise ValueError('Native crop mapping lost an original word')
        source_fields = ('id', 'source_file', 'speaker_id', 'role', 'ayah', 'surah', 'targets', 'mask',
                         'source_label', 'source_error_type', 'source_error_location', 'source_sha256',
                         'float_pcm_sha256', 'sample_count')
        result['sources'].append({**{key: source[key] for key in source_fields},
                                  'encoder_frame_count': len(features),
                                  'native_emissions': [{key:e[key] for key in
                                      ('id','start_frame','end_frame','confidence')} for e in emissions],
                                  'rms': float(np.sqrt(np.mean(samples**2)))})
        for crop, label in zip(crops, labels):
            if crop['word_index'] != label['word_index']:
                raise ValueError('Native crop and label word identity changed')
            index = crop['word_index']
            row = {**crop, 'id': f'{source["id"]}:w{index}', 'source_case_id': source['id'],
                   'target': label['target'], 'encoder_identity_sha256': identity_sha,
                   'feature_path': None, 'feature_sha256': None}
            if label['target'] is None:
                row.update(available=False, reason='unknown_vowel_label', frame_start=None, frame_end=None)
            elif crop['available']:
                path = cache/(source['id'] + '-w' + str(index) + '.npz')
                np.savez_compressed(path, features=features[crop['frame_start']:crop['frame_end']])
                row.update(feature_path=str(path), feature_sha256=file_sha(path))
            result['cases'].append(row)
        if len(result['sources']) % 32 == 0:
            write_json(output/'local-feature-manifest.json', result)
            print('LOCAL_VOWEL_FEATURES', len(result['sources']),
                  'eligible_words', sum(r['available'] for r in result['cases']), flush=True)
    write_json(output/'local-feature-manifest.json', result)
    return result


def verify_native_model(path, pins):
    path = Path(path)
    names = {'model.safetensors', 'config.json', 'vocab.json', 'preprocessor_config.json'}
    if (pins.get('model') != MODEL or pins.get('revision') != MODEL_REVISION
            or set(pins['files']) != names or pins['files']['model.safetensors']['sha256'] != MODEL_SHA):
        raise ValueError('Pinned native model bundle identity changed')
    hashes = {}
    for name in names:
        file = path/name
        spec = pins['files'][name]
        if file.is_symlink() or not file.is_file() or file.stat().st_size != spec['bytes']:
            raise ValueError('Native model file size or path changed')
        hashes[name] = file_sha(file)
        if hashes[name] != spec['sha256']:
            raise ValueError('Native model file SHA changed')
    return hashes


def validate_audited_metadata(metadata, audit):
    """Recheck only the frozen accepted cohort; prior exclusions stay excluded."""
    import csv
    import io
    accepted = {row['source_file'] for row in audit['cases']}
    metadata_rows = {}
    for row in csv.DictReader(io.StringIO(metadata.decode('utf-8-sig'))):
        key = row['file_name']
        if key not in accepted:
            continue
        if key in metadata_rows:
            raise ValueError('Ambiguous duplicate accepted source annotation')
        metadata_rows[key] = row
    for row in audit['cases']:
        if row['source_file'] not in metadata_rows:
            raise ValueError('Accepted source labels missing from pinned metadata')
        verified = parse_label_row(metadata_rows[row['source_file']], set(audit['reserved_speakers']))
        if any(row[k] != verified[k] for k in
               ('id', 'source_file', 'speaker_id', 'role', 'ayah', 'targets', 'mask',
                'source_label', 'source_error_type', 'source_error_location')):
            raise ValueError('Pinned contributor labels or source roles changed')


def main(*, deadline=None):
    import argparse
    import inspect
    import importlib.metadata
    from ml.training import local_vowel_data

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--encoder', type=Path, required=True)
    parser.add_argument('--model-pins', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--audit-sha', required=True)
    parser.add_argument('--references', type=Path, required=True)
    parser.add_argument('--references-sha', required=True)
    parser.add_argument('--output', type=Path, default=Path('/kaggle/working'))
    parser.add_argument('--cache', type=Path, default=Path('/kaggle/temp/local-vowel-features'))
    parser.add_argument('--crop-policy', choices=('exact_only_v1','unique_substitution_v1'),
                        default='exact_only_v1')
    parser.add_argument('--execution-device',choices=('cuda','kaggle_cpu'),default='cuda')
    args = parser.parse_args()
    if args.execution_device=='kaggle_cpu':
        _require_kaggle_cpu(args.output)
    if deadline is None:
        from ml.training.kaggle_job_budget import job_budget
        with job_budget(args.output) as limit:
            return main(deadline=limit)
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        actual_device=execution_device(args.execution_device,args.output)
        from transformers import AutoFeatureExtractor
        from qari_native_phonetic_model.modeling_multi_level_ctc import Wav2Vec2BertForMultilevelCTC
        if file_sha(args.audit) != args.audit_sha or file_sha(args.references) != args.references_sha:
            raise ValueError('Audited source/reference packet SHA changed')
        audit = json.loads(args.audit.read_text())
        references = json.loads(args.references.read_text())
        validate_word_references(references)
        if (len(audit['cases']) != 1393 or len(audit['reserved_speakers']) != 24
                or len(audit['quarantined_speakers']) != 19
                or any(r['speaker_id'] in audit['quarantined_speakers'] for r in audit['cases'])
                or references.get('surah') != 112 or references.get('model_revision') != MODEL_REVISION
                or references.get('phonetizer_package') != 'quran-transcript==0.6.1'):
            raise ValueError('Frozen cohort, holdouts or reference policy changed')
        budget = {'bytes': 0}
        metadata = fetch_public('metadata.csv', budget, deadline)
        if hashlib.sha256(metadata).hexdigest() != audit['metadata_sha256']:
            raise ValueError('Public metadata SHA changed')
        validate_audited_metadata(metadata, audit)
        pins = json.loads(args.model_pins.read_text())
        hashes = verify_native_model(args.encoder, pins)
        if references['phonetic_vocab_sha256'] != hashes['vocab.json']:
            raise ValueError('Expected reference vocabulary differs from native model')
        torch.set_num_threads(2)
        if actual_device=='cuda':torch.cuda.set_device(0)
        teacher, info = Wav2Vec2BertForMultilevelCTC.from_pretrained(
            str(args.encoder), local_files_only=True, use_safetensors=True,
            torch_dtype=torch.float32, output_loading_info=True)
        if any(info.get(k) for k in ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs')):
            raise ValueError('Native model did not load every pinned weight')
        teacher.to(actual_device); teacher.eval()
        processor = AutoFeatureExtractor.from_pretrained(str(args.encoder), local_files_only=True,
                                                          trust_remote_code=False)
        if processor.sampling_rate != 16000 or teacher.config.level_to_vocab_size['phonemes'] != 43:
            raise ValueError('Native processor or phoneme vocabulary changed')
        identity = {'model': MODEL, 'model_revision': MODEL_REVISION, 'model_sha256': MODEL_SHA,
                    'files': hashes, 'native_implementation_sha256': file_sha(inspect.getsourcefile(type(teacher))),
                    'crop_implementation_sha256': file_sha(local_vowel_data.__file__),
                    'feature_implementation_sha256': file_sha(__file__),
                    'reference_bundle_sha256': args.references_sha,
                    'crop_policy': args.crop_policy,
                    'feature_device':actual_device,'execution_scope':args.execution_device,
                    'native_nominal_samples_per_frame': 640, 'max_frame_count_error': 2,
                    'cache_format': 'native_post_adapter_1024_float16_word_v1'}
        write_json(args.output/'readiness.json', {'encoder_identity': identity,
                   'strict_native_weight_load': True, 'device': actual_device, 'dtype': 'float32',
                   'gpu': torch.cuda.get_device_name(0) if actual_device=='cuda' else None,
                   'execution_scope':args.execution_device,'reference_used_for_native_forward': False,
                   'versions': {p: importlib.metadata.version(p) for p in ['torch', 'transformers', 'numpy', 'scipy']},
                   'qualified': False, 'production_changed': False})
        print('LOCAL_VOWEL_READY', actual_device, MODEL_SHA, flush=True)
        manifest = prepare_local_vowel_features(audit, references,
            lambda samples: native_frame_features(samples, processor, teacher, device=actual_device),
            args.cache, args.output, identity, fetch=lambda name: fetch_public(name, budget, deadline),
            device=args.execution_device, deadline=deadline, crop_policy=args.crop_policy)
        source_roles = {r['id']: r['role'] for r in manifest['sources']}
        support = {role: {label: sum(r['available'] and r['target'] == label
                                    and source_roles[r['source_case_id']] == role for r in manifest['cases'])
                          for label in (0, 1)} for role in ('train', 'validation', 'test', 'reserved')}
        write_json(args.output/'eligible-support.json', support)
        for role, good, bad in [('train', 200, 80), ('validation', 50, 8), ('test', 50, 8)]:
            if support[role][0] < good or support[role][1] < bad:
                raise ValueError('Insufficient eligible local vowel supervision after native exclusions')
        del teacher
        if actual_device=='cuda':torch.cuda.empty_cache()
        report = train_local_vowel_features(manifest, args.output, device=args.execution_device, epochs=30, deadline=deadline)
        if verify_native_model(args.encoder, pins) != hashes:
            raise ValueError('Original frozen native model files changed')
        print('LOCAL_VOWEL_COMPLETE', json.dumps({k: report[k] for k in
              ('qualified', 'best_epoch', 'threshold', 'metrics')}), flush=True)
    except Exception as error:
        write_json(args.output/'failure.json', {'status': 'failed', 'qualified': False,
                   'production_changed': False, 'error_type': type(error).__name__, 'message': str(error)})
        raise


if __name__ == '__main__':
    main()
