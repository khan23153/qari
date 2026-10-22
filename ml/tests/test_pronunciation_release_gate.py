"""Word-recognition accuracy cannot qualify acoustic pronunciation grading."""
import pytest


def labels():
    return [
        {'case_id': 'bad-vowel', 'word_index': 3, 'correct': False, 'kind': 'vowel',
         'speaker_id': 'one', 'surah': 112, 'label_source': 'human'},
        {'case_id': 'clean-vowel', 'word_index': 3, 'correct': True, 'kind': 'vowel',
         'speaker_id': 'two', 'surah': 112, 'label_source': 'human'},
    ]


def test_lexically_correct_error_word_does_not_count_as_assessed_or_detected():
    from ml.evaluation.pronunciation import evaluate_pronunciation
    report = evaluate_pronunciation(labels(), [
        {'case_id': 'bad-vowel', 'word_index': 3, 'is_correct': True},
        {'case_id': 'clean-vowel', 'word_index': 3, 'is_correct': True},
    ])
    assert report['incorrect_words'] == 1
    assert report['detected_errors'] == 0
    assert report['unassessed_words'] == 2
    assert report['false_accepts'] == report['false_alarms'] == 0
    assert report['lexically_matched_error_words'] == 1
    assert report['recall'] == report['coverage'] == 0.0
    assert report['qualified'] is False


def test_canonical_phoneme_equality_can_false_accept_a_human_labelled_error():
    from ml.evaluation.pronunciation import evaluate_pronunciation
    predictions = [dict(case_id=r['case_id'], word_index=r['word_index'],
                        pronunciation_status='correct', evidence_source='acoustic')
                   for r in labels()]
    report = evaluate_pronunciation(labels(), predictions)
    assert report['false_accepts'] == 1
    assert report['true_accepts'] == 1
    assert report['recall'] == 0.0
    assert report['qualified'] is False


def test_abstention_does_not_hide_a_missed_error_from_recall():
    from ml.evaluation.pronunciation import evaluate_pronunciation
    report = evaluate_pronunciation(labels(), [
        {'case_id': 'bad-vowel', 'word_index': 3, 'pronunciation_status': 'unassessed'},
        {'case_id': 'clean-vowel', 'word_index': 3, 'pronunciation_status': 'correct',
         'evidence_source': 'acoustic'},
    ])
    assert report['recall'] == 0.0
    assert report['coverage'] == 0.5
    assert report['unassessed_errors'] == 1
    assert report['qualified'] is False


def test_false_alarm_and_real_error_are_counted_separately():
    from ml.evaluation.pronunciation import evaluate_pronunciation
    predictions = [dict(case_id=r['case_id'], word_index=r['word_index'],
                        pronunciation_status='incorrect', evidence_source='acoustic')
                   for r in labels()]
    report = evaluate_pronunciation(labels(), predictions)
    assert report['detected_errors'] == report['false_alarms'] == 1
    assert report['recall'] == report['false_alarm_rate'] == 1.0
    assert report['precision'] == 0.5
    assert report['qualified'] is False


@pytest.mark.parametrize('kind', ['duplicate_label', 'duplicate_prediction', 'oracle_prediction',
                                  'unknown_case', 'self_labelled', 'non_boolean_label'])
def test_invalid_or_oracle_evidence_cannot_qualify(kind):
    from ml.evaluation.pronunciation import evaluate_pronunciation
    truth = labels()
    predictions = [dict(case_id=r['case_id'], word_index=r['word_index'],
                        pronunciation_status='correct', evidence_source='acoustic') for r in truth]
    if kind == 'duplicate_label':
        truth.append(dict(truth[0]))
    if kind == 'duplicate_prediction':
        predictions.append(dict(predictions[0]))
    if kind == 'oracle_prediction':
        predictions[0]['evidence_source'] = 'expected_text'
    if kind == 'unknown_case':
        predictions[0]['case_id'] = 'unlabelled'
    if kind == 'self_labelled':
        truth[0]['label_source'] = 'model'
    if kind == 'non_boolean_label':
        truth[0]['correct'] = 'false'
    with pytest.raises(ValueError):
        evaluate_pronunciation(truth, predictions)


def test_perfect_small_single_surah_sample_is_still_not_a_qualified_model():
    from ml.evaluation.pronunciation import evaluate_pronunciation
    predictions = [dict(case_id=r['case_id'], word_index=r['word_index'],
                        pronunciation_status='correct' if r['correct'] else 'incorrect',
                        evidence_source='acoustic') for r in labels()]
    report = evaluate_pronunciation(labels(), predictions)
    assert report['recall'] == report['precision'] == report['coverage'] == 1.0
    assert report['qualified'] is False
    assert report['checks']['held_out_error_support'] is False
    assert report['checks']['speaker_support'] is False
    assert report['checks']['surah_support'] is False


def test_word_tracking_release_requires_acoustic_qualification_when_grading_is_claimed():
    from ml.evaluation.evaluate_phone_live import release_checks
    from ml.tests.test_phone_release_gate import _cases
    cases = _cases()
    cases['phone_fatihah']['pronunciation_available'] = True
    assert release_checks(cases)['pronunciation_evidence_qualified'] is False


def test_rejected_acoustic_candidate_cannot_pass_via_good_word_recall():
    from ml.evaluation.evaluate_phone_live import release_checks
    from ml.tests.test_phone_release_gate import _cases
    checks = release_checks(_cases(), pronunciation_report={'qualified': False})
    assert checks['pronunciation_evidence_qualified'] is False
    assert all(value for name, value in checks.items() if name != 'pronunciation_evidence_qualified')


def _supported_evaluation():
    import hashlib
    from ml.evaluation.pronunciation import evaluate_pronunciation
    truth, predictions = [], []
    for i in range(300):
        correct = i >= 150
        case_id = str(i)
        truth.append({
            'case_id': case_id, 'word_index': 0, 'correct': correct,
            'kind': ('vowel', 'gemination', 'consonant')[i % 3],
            'speaker_id': str(i % 10), 'surah': (1, 36, 112)[i % 3],
            'label_source': 'human', 'split': 'held',
            'pcm_sha256': hashlib.sha256(case_id.encode()).hexdigest(),
        })
        predictions.append({
            'case_id': case_id, 'word_index': 0, 'evidence_source': 'acoustic', 'model_sha256': 'a' * 64,
            'pronunciation_status': 'correct' if correct else 'incorrect',
        })
    return truth, predictions


def test_a_fully_supported_held_out_model_can_qualify():
    from ml.evaluation.pronunciation import evaluate_pronunciation
    truth, predictions = _supported_evaluation()
    report = evaluate_pronunciation(truth, predictions, training_speakers={'training-speaker'},
                                     training_pcm_hashes=set(), model_sha256='a' * 64)
    assert report['qualified'] is True
    assert all(report['checks'].values())


@pytest.mark.parametrize('leak', ['speaker', 'pcm', 'duplicate_pcm', 'metadata', 'invalid_pcm'])
def test_leakage_or_duplicated_audio_never_counts_as_independent_evidence(leak):
    import hashlib
    from ml.evaluation.pronunciation import evaluate_pronunciation
    truth = labels()
    for i, row in enumerate(truth):
        row['pcm_sha256'] = hashlib.sha256(str(i).encode()).hexdigest()
    kwargs = {}
    if leak == 'speaker':
        kwargs['training_speakers'] = {'one'}
    if leak == 'pcm':
        kwargs['training_pcm_hashes'] = {truth[0]['pcm_sha256']}
    if leak == 'duplicate_pcm':
        truth[1]['pcm_sha256'] = truth[0]['pcm_sha256']
    if leak == 'metadata':
        truth[1]['case_id'] = truth[0]['case_id']
        truth[1]['word_index'] = 4
    if leak == 'invalid_pcm':
        truth[0]['pcm_sha256'] = 'invalid'
    with pytest.raises(ValueError):
        evaluate_pronunciation(truth, [], **kwargs)


@pytest.mark.parametrize('mode', ['missed_class', 'false_alarms_in_one_class'])
def test_good_aggregate_scores_cannot_hide_a_failing_pronunciation_class(mode):
    from ml.evaluation.pronunciation import evaluate_pronunciation
    truth, predictions = _supported_evaluation()
    changed = 0
    for label, pred in zip(truth, predictions):
        if label['kind'] != 'consonant':
            continue
        if mode == 'missed_class' and not label['correct'] and changed < 6:
            pred['pronunciation_status'] = 'correct'
            changed += 1
        if mode == 'false_alarms_in_one_class' and label['correct'] and changed < 2:
            pred['pronunciation_status'] = 'incorrect'
            changed += 1
    report = evaluate_pronunciation(truth, predictions, training_speakers={'training-speaker'},
                                     training_pcm_hashes=set(), model_sha256='a' * 64)
    assert report['recall'] >= .90
    assert report['precision'] >= .98
    assert report['false_alarm_rate'] <= .02
    assert report['qualified'] is False
    assert report['checks']['error_kind_accuracy'] is False


def test_forged_summary_without_default_policy_or_known_checks_is_rejected():
    from ml.evaluation.evaluate_phone_live import release_checks
    from ml.tests.test_phone_release_gate import _cases
    report = {'qualified': True, 'model_sha256': 'a' * 64, 'checks': {'anything': True}}
    cases = _cases()
    cases['phone_fatihah'].update(pronunciation_available=True, pronunciation_model_sha256='a' * 64)
    assert release_checks(cases, pronunciation_report=report)['pronunciation_evidence_qualified'] is False


def test_qualified_report_for_another_acoustic_model_is_rejected():
    from ml.evaluation.pronunciation import evaluate_pronunciation
    from ml.evaluation.evaluate_phone_live import release_checks
    from ml.tests.test_phone_release_gate import _cases
    truth, predictions = _supported_evaluation()
    model_sha = 'a' * 64
    for pred in predictions:
        pred['model_sha256'] = model_sha
    report = evaluate_pronunciation(truth, predictions, training_speakers={'training-speaker'},
                                     training_pcm_hashes=set(), model_sha256=model_sha)
    assert report['qualified'] is True
    cases = _cases()
    cases['phone_fatihah'].update(pronunciation_available=True, pronunciation_model_sha256='b' * 64)
    assert release_checks(cases, pronunciation_report=report)['pronunciation_evidence_qualified'] is False
    for case in cases.values():
        case['pronunciation_model_sha256'] = model_sha
    assert release_checks(cases, pronunciation_report=report)['pronunciation_evidence_qualified'] is True


def test_small_sample_policy_cannot_be_used_as_a_production_release_policy():
    from ml.evaluation.pronunciation import PronunciationPolicy, evaluate_pronunciation
    from ml.evaluation.evaluate_phone_live import release_checks
    from ml.tests.test_phone_release_gate import _cases
    truth, predictions = _supported_evaluation()
    model_sha = 'a' * 64
    for pred in predictions:
        pred['model_sha256'] = model_sha
    report = evaluate_pronunciation(
        truth, predictions, model_sha256=model_sha, training_speakers={'training-speaker'},
        training_pcm_hashes=set(), policy=PronunciationPolicy(min_speakers=1),
    )
    assert report['qualified'] is True
    cases = _cases()
    for case in cases.values():
        case.update(pronunciation_available=True, pronunciation_model_sha256=model_sha)
    assert release_checks(cases, pronunciation_report=report)['pronunciation_evidence_qualified'] is False


def test_async_evaluator_preserves_forced_peak_and_actual_pronunciation_claim(tmp_path, monkeypatch):
    import asyncio
    import struct
    import wave
    from pathlib import Path
    from types import SimpleNamespace
    from ml.evaluation.evaluate_phone_live import evaluate
    monkeypatch.setenv('QARI_JWT_SECRET_KEY', 'private-unit-test-placeholder-no-auth-access')
    monkeypatch.setenv('QARI_ML_USE_STUB', 'true')
    # CI runs ml/tests in a separate process from recitation_api/tests, so its
    # conftest has not added the backend application directory to sys.path.
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / 'backend/recitation_api'))
    from app.services import streaming_session

    for name, value in [('phone_fatihah.wav', 100), ('fatihah.wav', 200), ('ikhlas.wav', 300)]:
        with wave.open(str(tmp_path / name), 'wb') as wav:
            wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            wav.writeframes(struct.pack('<h', value) * 4800)

    class FakeSession:
        def __init__(self, surah, **kwargs):
            self.surah = surah
            self.reference_words = ['word'] * (15 if surah == 112 else 29)
            self._matcher = SimpleNamespace(_cursor=0)
            self.audio = b''

        def load_reference(self):
            pass

        def add_audio(self, pcm):
            self.audio += pcm

        async def maybe_transcribe(self, force=False):
            sample = struct.unpack('<h', self.audio[:2])[0]
            wrong = self.surah == 1 and sample == 300
            if wrong:
                self._matcher._cursor = 29 if force else 2
                return []
            if sample == 0:
                return []
            self._matcher._cursor = len(self.reference_words)
            return [{'status': 'match', 'word_index': i} for i in range(len(self.reference_words))]

        async def finalize(self):
            assert self._write_wav() is None
            await self._persist({'fixture': True}, None)
            self._matcher._cursor = 2
            return {'pronunciation_available': True, 'pronunciation_model_sha256': 'a' * 64}

        def _write_wav(self):
            raise AssertionError('Release evaluation cannot store fixture audio')

        async def _persist(self, *args):
            raise AssertionError('Release evaluation cannot write session records')

    monkeypatch.setattr(streaming_session, 'StreamingRecitationSession', FakeSession)
    # The legacy evaluator configures its private process with os.environ.update.
    # Register these keys so this in-process test restores every touched value.
    import os
    keys = ['QARI_JWT_SECRET_KEY', 'QARI_ENVIRONMENT', 'QARI_ML_USE_STUB',
            'QARI_EVIDENCE_POLICY', 'QARI_FASTERWHISPER_THREADS', 'QARI_FASTERWHISPER_MODEL_DIR',
            'QARI_FASTERWHISPER_VERIFY_MODEL_DIR', 'QARI_REFERENCE_DATA_DIR',
            'HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE']
    for key in keys:
        monkeypatch.setenv(key, os.environ.get(key, ''))
    report = asyncio.run(evaluate(tmp_path, tmp_path, tmp_path))
    assert report['cases']['wrong_surah']['max_cursor'] == 29
    assert report['checks']['wrong_surah_no_completion'] is False
    assert report['cases']['phone_fatihah']['pronunciation_available'] is True
    assert report['checks']['pronunciation_evidence_qualified'] is False
    assert report['pass'] is False


def test_per_kind_abstention_and_lexical_accept_counts_match_aggregate():
    from ml.evaluation.pronunciation import evaluate_pronunciation
    truth = labels()
    report = evaluate_pronunciation(truth, [{'case_id': 'bad-vowel', 'word_index': 3, 'is_correct': True}])
    assert report['per_kind']['vowel']['unassessed_words'] == report['unassessed_words'] == 2
    assert report['per_kind']['vowel']['lexically_matched_error_words'] == 1


@pytest.mark.parametrize('inventory', ['one', b'one', {'one': True}, [1], None])
def test_malformed_training_inventory_cannot_claim_overlap_verification(inventory):
    from ml.evaluation.pronunciation import evaluate_pronunciation
    if inventory is None:
        assert evaluate_pronunciation(labels(), [], training_speakers=None)['checks']['training_overlap_verified'] is False
    else:
        with pytest.raises(ValueError):
            evaluate_pronunciation(labels(), [], training_speakers=inventory)


@pytest.mark.parametrize('inventory', ['a' * 64, b'a' * 64, {'a' * 64: True}, ['invalid'], [1]])
def test_malformed_audio_inventory_is_rejected(inventory):
    from ml.evaluation.pronunciation import evaluate_pronunciation
    with pytest.raises(ValueError):
        evaluate_pronunciation(labels(), [], training_pcm_hashes=inventory)
