def _cases():
    return {
        'phone_fatihah': {'matched': 29, 'confirmed_errors': 0},
        'reference_fatihah': {'matched': 29, 'confirmed_errors': 0},
        'reference_ikhlas': {'matched': 15, 'confirmed_errors': 0},
        'silence': {'events': 0, 'max_cursor': 0},
        'wrong_surah': {'matched': 1, 'cursor': 2, 'max_cursor': 2},
    }


def test_correct_recitation_with_false_red_mistake_fails_release_gate():
    from ml.evaluation.evaluate_phone_live import release_checks
    cases = _cases()
    cases['phone_fatihah']['confirmed_errors'] = 1
    checks = release_checks(cases)
    assert checks['no_false_confirmed_mistakes'] is False


def test_wrong_surah_must_never_complete_even_transiently():
    from ml.evaluation.evaluate_phone_live import release_checks
    cases = _cases()
    cases['wrong_surah']['max_cursor'] = 29
    assert release_checks(cases)['wrong_surah_no_completion'] is False
