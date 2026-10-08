"""Private Qari V52 phone-ASR pilot. This script is run by Kaggle, not the VPS."""

import json
import hashlib
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path


WORK = Path("/kaggle/working")
INPUT = Path("/kaggle/input")


def stage(name, **details):
    payload = {"stage": name, **details}
    print("QARI_PILOT " + json.dumps(payload), flush=True)
    (WORK / "pilot_status.json").write_text(json.dumps(payload, indent=2))


def unique_parent(filename):
    candidates = list(INPUT.rglob(filename))
    if len(candidates) != 1:
        raise RuntimeError(f"Expected exactly one {filename}; found {len(candidates)}")
    return candidates[0].parent


def run(*args, env=None):
    subprocess.run([sys.executable, *map(str, args)], check=True, env=env)


def convert(hf, target):
    from ctranslate2.converters import TransformersConverter
    from faster_whisper import WhisperModel
    TransformersConverter(str(hf), copy_files=["tokenizer.json", "preprocessor_config.json"]).convert(
        str(target), quantization="int8")
    p = target / "tokenizer.json"
    d = json.loads(p.read_text())
    d["model"]["merges"] = [" ".join(x) if isinstance(x, list) else x
                                for x in d["model"]["merges"]]
    p.write_text(json.dumps(d, ensure_ascii=False))
    model = WhisperModel(str(target), device="cpu", compute_type="int8", cpu_threads=2)
    if not model.model.is_multilingual:
        raise RuntimeError("Export lost Arabic/multilingual vocabulary compatibility")


def manifest_metrics(model, prepared, output, env):
    import jiwer
    run("-m", "ml.evaluation.evaluate_faster_whisper_manifest", "--model_dir", model,
        "--manifest", prepared / "eval_manifest.jsonl", "--output_jsonl", output, env=env)
    rows = [json.loads(line) for line in output.read_text().splitlines() if line.strip()]
    return {"samples": len(rows), "wer": jiwer.wer(
        [r["reference_normalized"] for r in rows],
        [r["prediction_normalized"] for r in rows])}


def main():
    WORK.mkdir(exist_ok=True)
    package = unique_parent("qari-pilot-package.json")
    package_metadata = json.loads((package / "qari-pilot-package.json").read_text())
    source = WORK / "pilot-source"
    source.mkdir()
    for entry in package_metadata["source_files"]:
        target = (source / entry["path"]).resolve()
        if not target.is_relative_to(source.resolve()):
            raise RuntimeError("Invalid source package path")
        payload = (package / entry["file"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            raise RuntimeError("Source package checksum mismatch")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    sys.path.insert(0, str(source))
    env = dict(os.environ, PYTHONPATH=str(source), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    stage("install_training_dependencies", python=sys.version,
          source_revision=package_metadata["source_revision"])
    run("-m", "pip", "install", "--quiet", "-r",
        source / "ml/training/requirements-kaggle-pilot.txt")
    run(source / "backend/recitation_api/fix_execstack.py")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("Kaggle GPU is required; CPU training is disabled")
    stage("dataset_preflight", gpu=torch.cuda.get_device_name(0), torch=torch.__version__)
    from ml.training.kaggle_phone_training import prepare_pilot_data
    data = unique_parent("train_manifest.jsonl")
    prepared = WORK / "prepared"
    audit = prepare_pilot_data(data, prepared, min_eval_speakers=5)
    print(json.dumps(audit), flush=True)
    bases = list(INPUT.rglob("base-hf/model.safetensors"))
    if len(bases) != 1:
        raise RuntimeError("Original tiny-base HF weights must be attached exactly once")
    base = WORK / "original-tiny-base"
    shutil.copytree(bases[0].parent, base)
    tokenizer = base / "tokenizer.json"
    d = json.loads(tokenizer.read_text())
    d["model"]["merges"] = [" ".join(x) if isinstance(x, list) else x for x in d["model"]["merges"]]
    tokenizer.write_text(json.dumps(d, ensure_ascii=False))
    stage("baseline_evaluation")
    base_ct2 = WORK / "original-tiny-base-ct2"
    convert(base, base_ct2)
    baseline = manifest_metrics(base_ct2, prepared, WORK / "baseline_predictions.jsonl", env)
    (WORK / "baseline_metrics.json").write_text(json.dumps(baseline, indent=2))
    stage("smoke_training", train_rows=audit["train_rows"], eval_rows=audit["eval_rows"])
    rows = (prepared / "train_manifest.jsonl").read_text().splitlines()
    smoke_manifest = prepared / "smoke_train.jsonl"
    smoke_manifest.write_text("\n".join(rows[:64]) + "\n")
    common = ["-m", "ml.training.finetune_whisper_robust", "--model_id", base,
              "--eval_manifest", prepared / "eval_manifest.jsonl", "--epochs", "1",
              "--batch_size", "4", "--train_scope", "encoder", "--learning_rate", "2e-6",
              "--no-fp16", "--label_smoothing_factor", "0", "--gradient_checkpointing"]
    smoke = WORK / "smoke-model"
    run(*common, "--train_manifest", smoke_manifest, "--output_dir", smoke,
        "--grad_accum", "2", "--eval_steps", "4", "--save_steps", "4", "--logging_steps", "1", env=env)
    if not math.isfinite(json.loads((smoke / "train_results.json").read_text())["train_loss"]):
        raise RuntimeError("Non-finite smoke training loss")
    stage("pilot_training", epochs=1, train_scope="encoder", **audit)
    candidate = WORK / "qari-v52-phone-encoder"
    run(*common, "--train_manifest", prepared / "train_manifest.jsonl", "--output_dir", candidate,
        "--grad_accum", "4", "--eval_steps", "40", "--save_steps", "40", "--logging_steps", "10", env=env)
    stage("export_and_real_phone_tests")
    ct2 = WORK / "qari-v52-phone-ct2"
    convert(candidate, ct2)
    candidate_metrics = manifest_metrics(ct2, prepared, WORK / "candidate_predictions.jsonl", env)
    (WORK / "candidate_metrics.json").write_text(json.dumps(candidate_metrics, indent=2))
    gate = WORK / "phone_release_gate.json"
    run("-m", "ml.evaluation.evaluate_phone_live", "--model", ct2,
        "--fixtures", package, "--source", source, "--output", gate, env=env)
    result = json.loads(gate.read_text())
    result["checks"]["heldout_known_speaker_wer_improvement"] = candidate_metrics["wer"] <= baseline["wer"] * .9
    result["full_speaker_disjoint_verified"] = audit["full_speaker_disjoint_verified"]
    result["recognition_checks_pass"] = all(result["checks"].values())
    result["pass"] = False  # The real VPS latency benchmark is still mandatory.
    result["automatic_deployment"] = False
    result["production_runtime_verified"] = False
    result["source_revision"] = json.loads((package / "qari-pilot-package.json").read_text())["source_revision"]
    gate.write_text(json.dumps(result, indent=2))
    stage("complete", recognition_checks_pass=result["recognition_checks_pass"],
          release_pass=False, vps_latency_verified=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        stage("failed", error_type=type(exc).__name__, error=str(exc))
        raise
