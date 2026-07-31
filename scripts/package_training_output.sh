#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(dirname -- "$REPO_ROOT")"
OUTPUT_DIR="${QARI_OUTPUT_DIR:-$WORKSPACE_ROOT/models/qari-whisper-tiny}"
ARTIFACT_DIR="${QARI_ARTIFACT_DIR:-$WORKSPACE_ROOT/artifacts}"
ARCHIVE="$ARTIFACT_DIR/qari-whisper-tiny-hf.tar.gz"

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

mkdir -p -- "$ARTIFACT_DIR"
staging="$(mktemp -d)"
trap 'rm -rf -- "$staging"' EXIT
package_dir="$staging/qari-whisper-tiny"
mkdir -p -- "$package_dir"

# The final root files are sufficient to restore/convert the trained model.
# Excluding checkpoint-* and TensorBoard directories keeps the backup compact.
find "$OUTPUT_DIR" -maxdepth 1 -type f -exec cp -p -- {} "$package_dir/" \;

tar -C "$staging" -czf "$ARCHIVE" qari-whisper-tiny
(
    cd -- "$ARTIFACT_DIR"
    sha256sum "$(basename -- "$ARCHIVE")" > "$(basename -- "$ARCHIVE").sha256"
)

printf 'Archive:  %s\n' "$ARCHIVE"
printf 'Checksum: %s\n' "$ARCHIVE.sha256"
du -h -- "$ARCHIVE"
cat -- "$ARCHIVE.sha256"
tar -tzf "$ARCHIVE" | sed -n '1,30p'
