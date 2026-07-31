#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(dirname -- "$REPO_ROOT")"
OUTPUT_DIR="${QARI_OUTPUT_DIR:-$WORKSPACE_ROOT/models/qari-whisper-tiny}"

required=(config.json train_results.json eval_results.json)
for filename in "${required[@]}"; do
    if [[ ! -s "$OUTPUT_DIR/$filename" ]]; then
        printf 'ERROR: missing training output: %s\n' "$OUTPUT_DIR/$filename" >&2
        exit 1
    fi
done

weight_file="$(find "$OUTPUT_DIR" -maxdepth 1 -type f \
    \( -name '*.safetensors' -o -name 'pytorch_model*.bin' \) \
    -print -quit)"
if [[ -z "$weight_file" ]]; then
    printf 'ERROR: model weights are missing from %s\n' "$OUTPUT_DIR" >&2
    exit 1
fi

printf 'Training output: %s\n' "$OUTPUT_DIR"
printf 'Model weights:   %s\n' "$weight_file"
du -sh -- "$OUTPUT_DIR"

python - "$OUTPUT_DIR" <<'PY'
from pathlib import Path
import json
import sys

output = Path(sys.argv[1])
train = json.loads((output / "train_results.json").read_text())
evaluation = json.loads((output / "eval_results.json").read_text())

print("train_loss:", train.get("train_loss"))
print("eval_loss:", evaluation.get("eval_loss"))
print("eval_wer:", evaluation.get("eval_wer"))

if "eval_wer" not in evaluation:
    raise SystemExit("ERROR: eval_wer is missing")
PY
