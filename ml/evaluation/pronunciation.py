"""Evaluate human-labelled word pronunciation independently of lexical matching.

This does not score audio or certify tajweed. A model must supply independent
acoustic predictions. The default engineering gates reject tiny, single-surah,
self-labelled or insufficiently held-out demonstrations even with perfect scores.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PronunciationPolicy:
    min_incorrect_words: int = 100
    min_correct_words: int = 100
    min_speakers: int = 5
    min_surahs: int = 3
    min_errors_per_kind: int = 20
    min_correct_words_per_kind: int = 20
    required_kinds: tuple[str, ...] = ('vowel', 'gemination', 'consonant')
    min_recall: float = .90
    min_precision: float = .98
    max_false_alarm_rate: float = .02
    min_coverage: float = .95


QUALIFICATION_CHECKS = (
    'held_out_error_support', 'held_out_correct_support', 'held_out_labels',
    'training_overlap_verified', 'model_identity_verified', 'speaker_support',
    'surah_support', 'error_kind_support', 'error_kind_accuracy', 'error_recall',
    'error_precision', 'false_alarm_limit', 'assessed_coverage',
)


def _valid_sha(value):
    return (isinstance(value, str) and len(value) == 64
            and all(char in '0123456789abcdef' for char in value))


def _known_speaker(value):
    return (isinstance(value, str) and bool(value.strip())
            and value.casefold().rsplit(':', 1)[-1] not in ('unknown', 'none', 'null'))


def _inventory(values, validator, name):
    if values is None:
        return None
    if not isinstance(values, (list, tuple, set, frozenset)) or not all(validator(value) for value in values):
        raise ValueError(f'{name} must be a collection of valid identifiers')
    return set(values)


def _policy_document(policy):
    document = asdict(policy)
    document['required_kinds'] = list(policy.required_kinds)
    return document


def qualified_for_model(report, model_sha256):
    """Require the default release policy and the actually evaluated model."""
    if not isinstance(report, dict) or not _valid_sha(model_sha256):
        return False
    checks = report.get('checks')
    return (
        report.get('schema_version') == 1
        and report.get('scope') == 'phonemic_pronunciation'
        and report.get('model_sha256') == model_sha256
        and report.get('policy') == _policy_document(PronunciationPolicy())
        and report.get('qualified') is True
        and isinstance(checks, dict) and set(checks) == set(QUALIFICATION_CHECKS)
        and all(value is True for value in checks.values())
    )


def _key(row):
    case, index = row.get('case_id'), row.get('word_index')
    if (not isinstance(case, str) or not case or type(index) is not int or index < 0):
        raise ValueError('Each observation needs a case ID and a nonnegative integer word index')
    return case, index


def evaluate_pronunciation(labels, predictions, *, policy=PronunciationPolicy(),
                           training_speakers=None, training_pcm_hashes=None, model_sha256=None):
    """Count error detection, false acceptance, false alarms and abstention.

    Missing acoustic evidence is unassessed. It is never a true acceptance or
    a detected error. Only held-out labels count toward model qualification;
    training provenance must be supplied and must not intersect evaluation.
    A passing report is limited to its labelled scope, not all Quran/tajweed.
    The model fingerprint must identify the complete immutable acoustic bundle,
    including its frontend, vocabulary and weights. Inventories are declarations;
    unknown upstream pretraining overlap must not be represented as an empty set.
    """
    training_speakers = _inventory(training_speakers, _known_speaker, 'Training speakers')
    training_pcm_hashes = _inventory(training_pcm_hashes, _valid_sha, 'Training PCM hashes')
    truth, outputs, case_metadata, audio_owners = {}, {}, {}, {}
    for row in labels:
        key = _key(row)
        if key in truth:
            raise ValueError('Duplicate labelled word')
        if type(row.get('correct')) is not bool:
            raise ValueError('Correctness labels must be booleans')
        if row.get('label_source') not in ('human', 'dataset_human'):
            raise ValueError('Ground truth must come from human annotations, not model output')
        speaker, surah = row.get('speaker_id'), row.get('surah')
        if not _known_speaker(speaker) or type(surah) is not int or not 1 <= surah <= 114:
            raise ValueError('A known speaker and Quran surah are required')
        if not isinstance(row.get('kind'), str) or not row['kind']:
            raise ValueError('A pronunciation kind is required')
        pcm = row.get('pcm_sha256')
        if pcm is not None:
            if not _valid_sha(pcm):
                raise ValueError('Invalid PCM SHA256')
            owner = audio_owners.setdefault(pcm, key[0])
            if owner != key[0]:
                raise ValueError('The same PCM cannot inflate support through multiple case IDs')
        metadata = (speaker, surah, pcm, row.get('split'))
        if case_metadata.setdefault(key[0], metadata) != metadata:
            raise ValueError('Inconsistent source metadata for one recording')
        truth[key] = row
    for row in predictions:
        key = _key(row)
        if key not in truth or key in outputs:
            raise ValueError('Unknown or duplicate predicted word')
        status = row.get('pronunciation_status', 'unassessed')
        if status not in ('correct', 'incorrect', 'unassessed'):
            raise ValueError('Unknown pronunciation status')
        if status != 'unassessed' and row.get('evidence_source') != 'acoustic':
            raise ValueError('Assessed pronunciation requires independent acoustic evidence')
        outputs[key] = row
    speakers = {r['speaker_id'] for r in truth.values()}
    pcms = {r['pcm_sha256'] for r in truth.values() if r.get('pcm_sha256')}
    if training_speakers is not None and speakers.intersection(training_speakers):
        raise ValueError('Training/evaluation speaker overlap')
    if training_pcm_hashes is not None and pcms.intersection(training_pcm_hashes):
        raise ValueError('Training/evaluation audio overlap')

    counts = Counter()
    per_kind = {}
    for key, label in truth.items():
        pred = outputs.get(key, {})
        status = pred.get('pronunciation_status', 'unassessed')
        correct = label['correct']
        counts['correct_words' if correct else 'incorrect_words'] += 1
        if not correct and pred.get('is_correct') is True:
            counts['lexically_matched_error_words'] += 1
            per_kind.setdefault(label['kind'], Counter())['lexically_matched_error_words'] += 1
        if status == 'unassessed':
            outcome = 'unassessed_correct' if correct else 'unassessed_errors'
            counts['unassessed_words'] += 1
            per_kind.setdefault(label['kind'], Counter())['unassessed_words'] += 1
        elif correct:
            outcome = 'true_accepts' if status == 'correct' else 'false_alarms'
        else:
            outcome = 'detected_errors' if status == 'incorrect' else 'false_accepts'
        counts[outcome] += 1
        per_kind.setdefault(label['kind'], Counter())[outcome] += 1
        per_kind[label['kind']]['correct_words' if correct else 'incorrect_words'] += 1

    def ratio(numerator, denominator):
        return numerator / denominator if denominator else 0.0

    names = ('correct_words', 'incorrect_words', 'detected_errors', 'true_accepts',
             'false_accepts', 'false_alarms', 'unassessed_words', 'unassessed_correct',
             'unassessed_errors', 'lexically_matched_error_words')
    kind_metrics = {}
    for kind, values in per_kind.items():
        correct, incorrect = values['correct_words'], values['incorrect_words']
        kind_metrics[kind] = {
            **{name: values[name] for name in names},
            'recall': ratio(values['detected_errors'], incorrect),
            'precision': ratio(values['detected_errors'], values['detected_errors'] + values['false_alarms']),
            'false_alarm_rate': ratio(values['false_alarms'], correct),
            'coverage': ratio(correct + incorrect - values['unassessed_correct'] - values['unassessed_errors'],
                              correct + incorrect),
        }
    report = {name: counts[name] for name in names}
    report.update(
        schema_version=1, scope='phonemic_pronunciation', model_sha256=model_sha256,
        policy=_policy_document(policy),
        recall=ratio(counts['detected_errors'], counts['incorrect_words']),
        precision=ratio(counts['detected_errors'], counts['detected_errors'] + counts['false_alarms']),
        false_alarm_rate=ratio(counts['false_alarms'], counts['correct_words']),
        false_accept_rate=ratio(counts['false_accepts'], counts['incorrect_words']),
        coverage=ratio(len(truth) - counts['unassessed_words'], len(truth)),
        speakers=len(speakers), surahs=len({r['surah'] for r in truth.values()}),
        per_kind=kind_metrics,
    )
    checks = {
        'held_out_error_support': counts['incorrect_words'] >= policy.min_incorrect_words,
        'held_out_correct_support': counts['correct_words'] >= policy.min_correct_words,
        'held_out_labels': bool(truth) and all(r.get('split') == 'held' for r in truth.values()),
        'training_overlap_verified': training_speakers is not None and training_pcm_hashes is not None
            and all(r.get('pcm_sha256') for r in truth.values()),
        'model_identity_verified': _valid_sha(model_sha256)
            and all(row.get('model_sha256') == model_sha256 for row in outputs.values()
                    if row.get('pronunciation_status', 'unassessed') != 'unassessed'),
        'speaker_support': len(speakers) >= policy.min_speakers,
        'surah_support': report['surahs'] >= policy.min_surahs,
        'error_kind_support': all(
            kind_metrics.get(kind, {}).get('incorrect_words', 0) >= policy.min_errors_per_kind
            and kind_metrics.get(kind, {}).get('correct_words', 0) >= policy.min_correct_words_per_kind
            for kind in policy.required_kinds),
        'error_kind_accuracy': all(
            kind in kind_metrics and kind_metrics[kind]['recall'] >= policy.min_recall
            and kind_metrics[kind]['precision'] >= policy.min_precision
            and kind_metrics[kind]['false_alarm_rate'] <= policy.max_false_alarm_rate
            and kind_metrics[kind]['coverage'] >= policy.min_coverage
            for kind in policy.required_kinds),
        'error_recall': report['recall'] >= policy.min_recall,
        'error_precision': report['precision'] >= policy.min_precision,
        'false_alarm_limit': report['false_alarm_rate'] <= policy.max_false_alarm_rate,
        'assessed_coverage': report['coverage'] >= policy.min_coverage,
    }
    assert set(checks) == set(QUALIFICATION_CHECKS)
    report.update(checks={name: bool(value) for name, value in checks.items()}, qualified=all(checks.values()))
    return report
