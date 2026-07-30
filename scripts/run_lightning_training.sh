#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(dirname -- "$REPO_ROOT")"

DATA_DIR="${QARI_DATA_DIR:-$WORKSPACE_ROOT/data/quran_train}"
OUTPUT_DIR="${QARI_OUTPUT_DIR:-$WORKSPACE_ROOT/models/qari-whisper-tiny}"
LOG_DIR="${QARI_LOG_DIR:-$WORKSPACE_ROOT/logs}"

if [[ ! -s "$DATA_DIR/manifest.jsonl" ]]; then
    printf 'ERROR: manifest not found: %s\n' "$DATA_DIR/manifest.jsonl" >&2
    printf 'Set QARI_DATA_DIR to the completed quran_train directory.\n' >&2
    exit 1
fi

resume_args=()
if [[ "${1:-}" == "--resume" ]]; then
    resume_args+=(--resume_from_checkpoint)
elif [[ $# -gt 0 ]]; then
    printf 'Usage: %s [--resume]\n' "$0" >&2
    exit 2
fi

mkdir -p -- "$OUTPUT_DIR" "$LOG_DIR"
printf 'Repository: %s\n' "$REPO_ROOT"
printf 'Dataset:    %s\n' "$DATA_DIR"
printf 'Output:     %s\n' "$OUTPUT_DIR"
printf 'Log:        %s\n' "$LOG_DIR/full-training.log"

cd -- "$REPO_ROOT"
set -o pipefail
python -m ml.training.finetune_whisper \
    --model_id tarteel-ai/whisper-tiny-ar-quran \
    --data_dir "$DATA_DIR" \
    --output_dir "$OUTPUT_DIR" \
    --language ar \
    --epochs 3 \
    --batch_size 8 \
    --learning_rate 1e-5 \
    --warmup_steps 500 \
    --eval_split 0.10 \
    --use_fp16 \
    --gradient_checkpointing \
    "${resume_args[@]}" 2>&1 | tee -a "$LOG_DIR/full-training.log"
