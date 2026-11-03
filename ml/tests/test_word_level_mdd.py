from ml.evaluation.word_level_mdd import error_kind, metrics, word_records, wilson


def test_kinds():
    assert error_kind("a", "u") == "vowel"
    assert error_kind("a", None) == "vowel"        # vowel dropped (sukun-like)
    assert error_kind("nn", "n") == "gemination"
    assert error_kind("H", "h") == "consonant"


def test_word_records_put_errors_on_the_right_word():
    rec = {"id": "00003_00001", "ref": ["q", "u", "l", "h", "u", "w", "a"],
           "ann": ["q", "u", "l", "h", "a", "w", "a"], "ours": ["q", "u", "l", "h", "u", "w", "a"],
           "probs": [.1, .1, .1, .2, .9, .1, .1]}
    w = word_records(rec, [3, 4])
    assert [x["kinds"] for x in w] == [[], ["vowel"]]
    assert w[1]["max"] == .9 and w[0]["speaker"] == "00003"


def test_metrics_and_wilson():
    words = [{"id": "a", "speaker": "s", "word": 0, "max": .9, "mean": .9, "pred_kind": "vowel", "uncertain": False, "kinds": ["vowel"]},
             {"id": "a", "speaker": "s", "word": 1, "max": .8, "mean": .8, "pred_kind": "vowel", "uncertain": False, "kinds": []},
             {"id": "a", "speaker": "s", "word": 2, "max": .1, "mean": .1, "pred_kind": "vowel", "uncertain": False, "kinds": ["consonant"]},
             {"id": "a", "speaker": "s", "word": 3, "max": .1, "mean": .1, "pred_kind": "vowel", "uncertain": False, "kinds": []}]
    m = metrics(words, .5)
    assert (m["detected"], m["missed"], m["false_accusations"]) == (1, 1, 1)
    assert m["precision"] == .5 and m["recall"] == .5 and m["false_alarm_rate"] == .5
    assert m["per_kind"]["vowel"]["recall"] == 1.0
    lo, hi = wilson(189, 189)
    assert lo > .98 > wilson(98, 100)[0]


def test_per_kind_precision_uses_attributed_flags():
    rec = {"id": "00001_00002", "ref": ["q", "u", "l", "h", "u", "w", "a"],
           "ann": ["k", "u", "l", "h", "u", "w", "a"], "ours": ["q", "u", "l", "h", "u", "w", "a"],
           "probs": [.9, .1, .1, .1, .1, .1, .8]}
    w = word_records(rec, [3, 4])
    assert w[0]["pred_kind"] == "consonant" and w[0]["kinds"] == ["consonant"]
    assert w[1]["pred_kind"] == "vowel" and w[1]["kinds"] == []
    m = metrics(w, .5)
    assert m["per_kind"]["consonant"]["precision"] == 1.0
    assert m["per_kind"]["vowel"]["precision"] == 0.0
    assert m["per_kind"]["vowel"]["false_alarm_rate"] == 1.0  # 1 flag over 1 correct word


def test_phonemizer_mismatch_marks_word_uncertain():
    rec = {"id": "00001_00003", "ref": ["q", "u", "l", "h", "u", "w", "a"],
           "ann": ["q", "u", "l", "h", "u", "w", "a"], "ours": ["q", "U", "l", "h", "u", "w", "a"],
           "probs": [.1] * 7}
    w = word_records(rec, [3, 4])
    assert [x["uncertain"] for x in w] == [True, False]
