import hashlib
import io
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf
import torch
from torch import nn

from ml.training.human_word_data import parse_label_row
from ml.training.kaggle_human_word_job import decode_source_audio
from ml.training.kaggle_local_vowel_job import native_frame_features, prepare_local_vowel_features


WORDS = [[21, 33, 23], [26, 33, 27, 32], [23, 23, 32, 29, 29, 26, 33], [1, 32, 6, 32, 8, 38]]
IDENTITY = {'model_sha256': '6'*64, 'crop_implementation_sha256': '7'*64}


def fixtures(amplitude=.1):
    out = io.BytesIO()
    samples = (amplitude*np.sin(2*np.pi*200*np.arange(20480)/16000)).astype(np.float32)
    sf.write(out, samples, 16000, format='WAV', subtype='PCM_16')
    raw = out.getvalue()
    row = parse_label_row(dict(file_name='data/ID45V1T.wav', label='1', label_name='correct',
                              verse_number='1', verse_text='قُلْ هُوَ اللَّهُ أَحَدٌ',
                              error_location='', error_type='', error_explanation=''), set())
    if amplitude:
        actual = decode_source_audio(raw)
    else:
        actual = samples
    row.update(source_sha256=hashlib.sha256(raw).hexdigest(), sample_count=len(actual),
               float_pcm_sha256=hashlib.sha256(actual.astype('<f4').tobytes()).hexdigest())
    audit = {'dataset': 'MuazAhmad7/Surah_Ikhlas-Labeled_Dataset',
             'revision': '973b5ef1d1532bcbe7e9a5a5b0dce125cc4d0dac',
             'cases': [row], 'reserved_speakers': []}
    ids = [t for word in WORDS for t in word]
    owners = [i for i, word in enumerate(WORDS) for _ in word]
    refs = {'ayahs': {'1': {'uthmani': 'قُلْ هُوَ اللَّهُ أَحَدٌ',
                           'reference_ids': ids, 'reference_word_indices': owners,
                           'word_reference_ids': WORDS}}}
    return raw, audit, refs


def encoded(samples):
    # Native-stack fixture only; no model accuracy claim from synthetic features.
    ids = [t for word in WORDS for t in word]
    records = []; frame = 0; previous = None
    for token in ids:
        if token == previous:
            frame += 1
        records.append(dict(id=token, start_frame=frame, end_frame=frame+1, confidence=.99))
        previous = token; frame += 1
    return np.ones((32, 1024), dtype=np.float16), records


class NativeStack(nn.Module):
    def __init__(self):
        super().__init__()
        self.dropout = nn.Identity()
        self.level_to_lm_head = nn.ModuleDict({'phonemes': nn.Linear(1024, 43, bias=False)})
        with torch.no_grad():
            self.level_to_lm_head['phonemes'].weight.zero_()
            self.level_to_lm_head['phonemes'].weight[:, :43] = torch.eye(43)

    def wav2vec2_bert(self, input_features):
        return SimpleNamespace(last_hidden_state=input_features)


def test_native_feature_tap_preserves_ctc_repeats_without_reference_input():
    path = [0, 21, 21, 0, 21, 33, 33, 0]
    features = torch.zeros(1, 8, 1024)
    for i, token in enumerate(path):
        features[0, i, token] = 12
    def frontend(samples, sampling_rate, return_tensors):
        assert len(samples) == 5120 and sampling_rate == 16000 and return_tensors == 'pt'
        return {'input_features': features}
    x, records = native_frame_features(np.ones(5120, np.float32)*.1, frontend, NativeStack(), device='cpu')
    assert x.dtype == np.float16 and x.shape == (8, 1024)
    assert [r['id'] for r in records] == [21, 21, 33]
    assert [(r['start_frame'], r['end_frame']) for r in records] == [(1, 3), (4, 5), (5, 7)]


def test_feature_cache_keeps_actual_source_pcm_and_word_frame_identity(tmp_path):
    raw, audit, refs = fixtures()
    identity = {'model_sha256': '6'*64, 'crop_implementation_sha256': '7'*64}
    manifest = prepare_local_vowel_features(audit, refs, encoded, tmp_path/'cache', tmp_path/'out',
                                           identity, fetch=lambda _: raw)
    assert len(manifest['cases']) == 4 and all(r['available'] for r in manifest['cases'])
    assert manifest['sources'][0]['float_pcm_sha256'] == audit['cases'][0]['float_pcm_sha256']
    for row in manifest['cases']:
        with np.load(row['feature_path'], allow_pickle=False) as data:
            assert data['features'].shape == (row['frame_end']-row['frame_start'], 1024)
        assert row['target'] == 0
        assert row['reference_ids'] == WORDS[row['word_index']]


@pytest.mark.parametrize('changed', ['source_sha', 'pcm_sha', 'silence', 'native_timebase'])
def test_wrong_identity_silence_or_native_frame_count_stops_before_cache(tmp_path, changed):
    raw, audit, refs = fixtures(amplitude=0 if changed == 'silence' else .1)
    if changed == 'source_sha': audit['cases'][0]['source_sha256'] = '0'*64
    if changed == 'pcm_sha': audit['cases'][0]['float_pcm_sha256'] = '0'*64
    def encode(samples):
        if changed != 'native_timebase':
            pytest.fail('Invalid source reached native encoder')
        _, records = encoded(samples)
        return np.ones((100, 1024), np.float16), records
    with pytest.raises(ValueError, match='SHA|PCM|speech|frame'):
        prepare_local_vowel_features(audit, refs, encode, tmp_path/'cache', tmp_path/'out',
                                     IDENTITY, fetch=lambda _: raw)
    assert not list((tmp_path/'cache').glob('*.npz'))


def test_missing_native_word_is_retained_as_unassessed_not_discarded(tmp_path):
    raw, audit, refs = fixtures()
    def blank(samples):
        return np.ones((32, 1024), np.float16), []
    manifest = prepare_local_vowel_features(audit, refs, blank, tmp_path/'cache', tmp_path/'out',
                                           IDENTITY, fetch=lambda _: raw)
    assert len(manifest['cases']) == 4
    assert all(r['available'] is False and r['feature_path'] is None for r in manifest['cases'])
    assert [r['target'] for r in manifest['cases']] == [0, 0, 0, 0]


@pytest.mark.parametrize('changed', ['excluded_duplicate', 'accepted_duplicate', 'accepted_label'])
def test_metadata_validation_preserves_prior_exclusions_and_unique_accepted_labels(changed):
    import csv
    from ml.training.kaggle_local_vowel_job import validate_audited_metadata
    _, audit, _ = fixtures()
    row = dict(file_name='data/ID45V1T.wav', label='1', label_name='correct',
               verse_number='1', verse_text='قُلْ هُوَ اللَّهُ أَحَدٌ', error_location='',
               error_type='', error_explanation='')
    excluded = {**row, 'file_name': 'data/ID42V2T.wav', 'verse_number': '2',
                'verse_text': 'اللَّهُ الصَّمَدُ'}
    rows = [row, excluded, dict(excluded)]
    if changed == 'accepted_duplicate': rows.append(dict(row))
    if changed == 'accepted_label': row['label'] = '0'
    text = io.StringIO(); writer = csv.DictWriter(text, fieldnames=list(row)); writer.writeheader()
    writer.writerows(rows)
    if changed == 'excluded_duplicate':
        validate_audited_metadata(text.getvalue().encode(), audit)
    else:
        with pytest.raises(ValueError, match='duplicate|labels|label'):
            validate_audited_metadata(text.getvalue().encode(), audit)


@pytest.mark.parametrize('changed_word', [False, True])
def test_original_uthmani_small_waw_is_recitation_mark_without_erasing_real_word_changes(tmp_path, changed_word):
    raw, audit, refs = fixtures()
    words = [[27,32,23,32,24],[28,32,22,33],[23,23,32,26,33,31,31],
             [22,33,20,33,27,32,25],[1,32,6,32,8,38]]
    refs['ayahs']['4'] = {
        'uthmani': 'وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ' if not changed_word else 'وَلَمْ يَكُن لَّهُۥ كُفُوًا صَمَدٌ',
        'word_reference_ids': words,
        'reference_ids': [t for word in words for t in word],
        'reference_word_indices': [i for i,word in enumerate(words) for _ in word]}
    if changed_word:
        with pytest.raises(ValueError, match='reference mapping'):
            prepare_local_vowel_features(audit, refs, encoded, tmp_path/'cache', tmp_path/'out',
                                         IDENTITY, fetch=lambda _: raw)
    else:
        manifest = prepare_local_vowel_features(audit, refs, encoded, tmp_path/'cache', tmp_path/'out',
                                                IDENTITY, fetch=lambda _: raw)
        # Long-vowel phones remain intact; only lexical-script comparison ignores the mark.
        assert manifest['references']['4'][2] == [23,23,32,26,33,31,31]


def test_explicit_substitution_policy_binds_cache_identity_and_retains_native_trace(tmp_path):
    raw,audit,refs=fixtures()
    def substitute(samples):
        features,emissions=encoded(samples);emissions[0]['id']=22
        return features,emissions
    old=prepare_local_vowel_features(audit,refs,substitute,tmp_path/'old',tmp_path/'oldout',
                                     IDENTITY,fetch=lambda _:raw)
    assert not old['cases'][0]['available']
    identity={**IDENTITY,'crop_policy':'unique_substitution_v1'}
    new=prepare_local_vowel_features(audit,refs,substitute,tmp_path/'new',tmp_path/'newout',
                                     identity,fetch=lambda _:raw,crop_policy='unique_substitution_v1')
    assert new['crop_policy']=='unique_substitution_v1'
    assert new['cases'][0]['available']
    assert new['cases'][0]['native_consonant_ids']==[22,23]
    assert new['cases'][0]['native_anchor_types']==['substitution','exact']
    assert new['sources'][0]['native_emissions'][0]['id']==22
    assert new['sources'][0]['source_sha256']==audit['cases'][0]['source_sha256']
    assert new['encoder_identity']['crop_policy']=='unique_substitution_v1'


@pytest.mark.parametrize('identity_policy,selected',[
    (None,'unique_substitution_v1'),('exact_only_v1','unique_substitution_v1'),
    ('unique_substitution_v1','exact_only_v1'),('accept_all','accept_all')])
def test_feature_extraction_refuses_missing_mixed_or_unknown_policy_before_audio(tmp_path,identity_policy,selected):
    _,audit,refs=fixtures();identity=dict(IDENTITY)
    if identity_policy is not None:identity['crop_policy']=identity_policy
    with pytest.raises(ValueError,match='policy'):
        prepare_local_vowel_features(audit,refs,encoded,tmp_path/'cache',tmp_path/'out',identity,
             fetch=lambda _:pytest.fail('Invalid policy reached download'),crop_policy=selected)


@pytest.mark.parametrize('scope,cuda_available,expected',[
    ('kaggle_cpu',False,'cpu'),('cuda',True,'cuda'),('cuda',False,None),('cpu',False,None)])
def test_full_execution_scope_requires_explicit_remote_cpu_or_actual_cuda(tmp_path,monkeypatch,scope,cuda_available,expected):
    from ml.training import kaggle_local_vowel_job as job
    called=[]
    monkeypatch.setattr(job,'_require_kaggle_cpu',lambda output:called.append(output),raising=False)
    monkeypatch.setattr(torch.cuda,'is_available',lambda:cuda_available)
    if expected is None:
        with pytest.raises((ValueError,RuntimeError)):
            job.execution_device(scope,tmp_path)
    else:
        assert job.execution_device(scope,tmp_path)==expected
        assert called==([tmp_path] if scope=='kaggle_cpu' else [])


def test_rejected_remote_cpu_cli_cannot_create_output_before_context_check(tmp_path,monkeypatch):
    import sys,time
    from ml.training.kaggle_local_vowel_job import main
    output=tmp_path/'outside-kaggle'
    monkeypatch.setattr(sys,'argv',['local-vowel','--encoder','missing','--model-pins','missing',
        '--audit','missing','--audit-sha','0'*64,'--references','missing','--references-sha','0'*64,
        '--execution-device','kaggle_cpu','--output',str(output)])
    with pytest.raises(RuntimeError,match='Kaggle'):
        main(deadline=time.monotonic()+5)
    assert not output.exists()
