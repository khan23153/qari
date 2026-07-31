#!/usr/bin/env bash
set -euo pipefail

# Run from any working directory. Resolve the repository from this script
# instead of trusting shell variables that disappear between Lightning shells.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(dirname -- "$REPO_ROOT")"

DATA_DIR="${QARI_DATA_DIR:-$WORKSPACE_ROOT/data/quran_train}"
OUTPUT_DIR="${QARI_SMOKE_OUTPUT:-$WORKSPACE_ROOT/models/qari-whisper-tiny-smoke}"

if [[ ! -s "$DATA_DIR/manifest.jsonl" ]]; then
    printf 'ERROR: manifest not found: %s\n' "$DATA_DIR/manifest.jsonl" >&2
    printf 'Set QARI_DATA_DIR to the completed quran_train directory.\n' >&2
    exit 1
fi

mkdir -p "$(dirname -- "$OUTPUT_DIR")"
rm -rf -- "$OUTPUT_DIR"

printf 'Repository: %s\n' "$REPO_ROOT"
printf 'Dataset:    %s\n' "$DATA_DIR"
printf 'Output:     %s\n' "$OUTPUT_DIR"

cd -- "$REPO_ROOT"
exec python -m ml.training.finetune_whisper \
    --model_id tarteel-ai/whisper-tiny-ar-quran \
    --data_dir "$DATA_DIR" \
    --output_dir "$OUTPUT_DIR" \
    --language ar \
    --epochs 1 \
    --batch_size 4 \
    --learning_rate 1e-5 \
    --warmup_steps 5 \
    --max_steps 20 \
    --max_samples 300 \
    --eval_split 0.10 \
    --use_fp16 \
    --gradient_checkpointing
