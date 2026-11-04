"""Only a bundle of raw human labels + model predictions can qualify a model."""
import json

from ml.evaluation.pronunciation import verify_evaluation_bundle, write_evaluation_bundle

SHA = "a" * 64


def rows(perfect=True):
    labels, preds = [], []
    n = 0
    for kind in ("vowel", "gemination", "consonant"):
        for k in range(80):
            correct = k % 2 == 0
            case = f"rec{n}"
            n += 1
            labels.append({"case_id": case, "word_index": 0, "correct": correct, "label_source": "human",
                           "speaker_id": f"spk{k % 6}", "surah": 1 + k % 4, "kind": kind, "split": "held",
                           "pcm_sha256": f"{n:064x}"})
            heard_wrong = (not correct) if perfect else (k % 3 == 0)
            preds.append({"case_id": case, "word_index": 0, "evidence_source": "acoustic", "model_sha256": SHA,
                          "pronunciation_status": "incorrect" if heard_wrong else "correct"})
    return labels, preds


def write(tmp_path, perfect=True, sha=SHA):
    labels, preds = rows(perfect)
    return write_evaluation_bundle(tmp_path, labels, preds, model_sha256=sha, dataset={"name": "test", "split": "held"},
                                   training_speakers=["train1"], training_pcm_hashes=["b" * 64])


def test_passing_bundle_qualifies(tmp_path):
    assert write(tmp_path)["qualified"] is True
    assert verify_evaluation_bundle(tmp_path, SHA) == (True, "qualified")


def test_other_model_or_weak_model_does_not(tmp_path):
    write(tmp_path)
    assert verify_evaluation_bundle(tmp_path, "c" * 64)[0] is False
    weak = tmp_path / "weak"
    write(weak, perfect=False)
    ok, reason = verify_evaluation_bundle(weak, SHA)
    assert not ok and "not qualified" in reason


def test_edited_predictions_or_report_are_rejected(tmp_path):
    write(tmp_path / "w", perfect=False)
    # flip the stored report to "qualified": recomputation ignores it
    rep = json.loads((tmp_path / "w" / "report.json").read_text())
    rep["qualified"] = True
    rep["checks"] = {k: True for k in rep["checks"]}
    (tmp_path / "w" / "report.json").write_text(json.dumps(rep))
    assert verify_evaluation_bundle(tmp_path / "w", SHA)[0] is False
    # edit a prediction after writing: hash mismatch
    write(tmp_path / "p")
    lines = (tmp_path / "p" / "predictions.jsonl").read_text().splitlines()
    lines[0] = lines[0].replace('"correct"', '"incorrect"')
    (tmp_path / "p" / "predictions.jsonl").write_text("\n".join(lines) + "\n")
    ok, reason = verify_evaluation_bundle(tmp_path / "p", SHA)
    assert not ok and "changed" in reason


def test_a_lone_report_is_not_enough(tmp_path):
    write(tmp_path)
    (tmp_path / "labels.jsonl").unlink()
    ok, reason = verify_evaluation_bundle(tmp_path, SHA)
    assert not ok and "missing" in reason
