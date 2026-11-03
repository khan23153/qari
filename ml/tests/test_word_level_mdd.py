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
    words = [{"id": "a", "speaker": "s", "word": 0, "max": .9, "mean": .9, "kinds": ["vowel"]},
             {"id": "a", "speaker": "s", "word": 1, "max": .8, "mean": .8, "kinds": []},
             {"id": "a", "speaker": "s", "word": 2, "max": .1, "mean": .1, "kinds": ["consonant"]},
             {"id": "a", "speaker": "s", "word": 3, "max": .1, "mean": .1, "kinds": []}]
    m = metrics(words, .5)
    assert (m["detected"], m["missed"], m["false_accusations"]) == (1, 1, 1)
    assert m["precision"] == .5 and m["recall"] == .5 and m["false_alarm_rate"] == .5
    assert m["per_kind_recall"]["vowel"]["recall"] == 1.0
    lo, hi = wilson(189, 189)
    assert lo > .98 > wilson(98, 100)[0]
