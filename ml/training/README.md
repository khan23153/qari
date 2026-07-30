# Training our own live-tracking model (Tarteel-parity plan)

The app now streams live recitation exclusively to **our own backend**
(`/ws/recitation/stream`); the Tarteel client integration has been removed.
This document is the playbook for closing the accuracy gap between our current
engine and Tarteel-level live tracking.

## Where the engine stands today

- **Live path** (`recitation-api` container): `faster-whisper` (CTranslate2,
  INT8, CPU) running the converted `tarteel-ai/whisper-tiny-ar-quran`
  checkpoint with a 6 s sliding window + silence gating
  (`QARI_FASTERWHISPER_MODEL_DIR=/app/models/tarteel-ct2-tiny`). Tiny was
  chosen because base could not keep up with real time on the VPS CPU.
- **Batch path** (`inference-worker` container): PyTorch
  `tarteel-ai/whisper-base-ar-quran` + forced alignment for the
  upload-and-score flow.
- The word tracker (`ml/alignment/streaming_matcher.py`) is already robust to
  ASR noise; **transcription quality of the live (tiny) model is the
  bottleneck**, not the matcher.

## Step 1 — Build the training dataset

Run the builder from the repository checkout, not from the Lightning Studio
workspace root. On Lightning, discover the checkout rather than assuming that
`QARI_REPO` is already set correctly:

```bash
QARI_REPO="$(find "$HOME" /teamspace/studios -maxdepth 5 \
    -type f -path '*/scripts/build_training_dataset.py' \
    -printf '%h\n' 2>/dev/null | sed 's#/scripts$##' | head -n 1)"

test -n "$QARI_REPO" || {
    echo "Qari checkout not found; clone it before building the dataset" >&2
    exit 1
}
test -f "$QARI_REPO/scripts/build_training_dataset.py"
export QARI_REPO
cd "$QARI_REPO"
printf 'Using Qari checkout: %s\n' "$QARI_REPO"
```

If no checkout is found, clone it into persistent storage first:

```bash
mkdir -p "$HOME/qari-lightning"
git clone https://github.com/khan23153/qari.git \
    "$HOME/qari-lightning/qari"
export QARI_REPO="$HOME/qari-lightning/qari"
cd "$QARI_REPO"
```

Confirm that FFmpeg is available before starting downloads:

```bash
command -v ffmpeg || {
    sudo apt-get update
    sudo apt-get install -y ffmpeg
}
ffmpeg -version | head -n 1
```

```bash
python scripts/build_training_dataset.py --out /data/quran_train
```

Downloads per-ayah recitations for the app's 5 reciters from everyayah.com,
converts them to 16 kHz mono WAV, and pairs each clip with the Uthmani text
from the bundled corpus. Output is `manifest.jsonl` + `audio/` in exactly the
format `ml/training/finetune_whisper.py` consumes (~31k clips for the full
run; use `--surahs 1-2 --reciters Alafasy_64kbps` for a smoke test).

After a cloud dataset build, verify that the manifest and WAV counts agree
before spending GPU time:

```bash
QARI_MANIFEST="$(find "$HOME/qari-lightning/data" /teamspace/studios \
    -type f -path '*/quran_train/manifest.jsonl' -print 2>/dev/null | head -n 1)"
test -n "$QARI_MANIFEST" || {
    echo 'Completed quran_train/manifest.jsonl was not found' >&2
    exit 1
}
export QARI_DATA_DIR="$(dirname "$QARI_MANIFEST")"
printf 'Using dataset: %s\n' "$QARI_DATA_DIR"
test -s "$QARI_DATA_DIR/manifest.jsonl"
manifest_rows="$(wc -l < "$QARI_DATA_DIR/manifest.jsonl")"
wav_files="$(find "$QARI_DATA_DIR/audio" -type f -name '*.wav' | wc -l)"
printf 'manifest rows: %s\nWAV files: %s\n' "$manifest_rows" "$wav_files"
test "$manifest_rows" -eq "$wav_files"
if find "$QARI_DATA_DIR" -type f -name '*.mp3' -print -quit | grep -q .; then
    echo 'Unexpected temporary MP3 files remain' >&2
    exit 1
fi
du -sh "$QARI_DATA_DIR"
```

To reach Tarteel-level robustness on *ordinary users* (not just professional
qaris), extend the manifest over time with:

- the Hugging Face `tarteel-ai/everyayah` dataset (crowd-sourced recitations,
  same (audio, text) shape — thousands of amateur voices);
- our own users' uploads: the batch pipeline already stores WAVs + the target
  ayah per session, which is exactly a manifest row. Add rows only from
  sessions the user consented to share.

## Step 2 — Fine-tune

Needs a GPU machine (Colab/Kaggle/rented). CPU training is not practical.

On a managed GPU image such as Lightning, preserve its CUDA-enabled PyTorch
and install only the missing training packages:

```bash
python -m pip install \
    'transformers==4.46.3' 'accelerate==1.1.1' \
    'datasets==3.1.0' 'evaluate==0.4.3' 'jiwer==3.0.5' \
    'soundfile>=0.12.1' 'librosa>=0.10.1' 'tensorboard>=2.16'

python - <<'PY'
import torch
assert torch.cuda.is_available(), "CUDA GPU is not available"
print(torch.__version__, torch.cuda.get_device_name(0))
PY
```

Do a 20-step smoke run before the full run. `--max_samples 300` selects a
deterministic subset directly from the completed dataset, so no temporary
manifest, symlink, or extra `QARI_SMOKE_DATA` variable is needed:

On Lightning, the safest entry point is the wrapper below. It resolves the
repository from its own file location and defaults to sibling `data/` and
`models/` directories, so it works even when the current directory and old
`QARI_REPO` value are wrong:

```bash
bash scripts/run_lightning_smoke.sh
```

The equivalent manual command is:

```bash
export QARI_SMOKE_OUTPUT="$HOME/qari-lightning/models/qari-whisper-tiny-smoke"
test -s "$QARI_DATA_DIR/manifest.jsonl"
mkdir -p "$(dirname "$QARI_SMOKE_OUTPUT")"
rm -rf "$QARI_SMOKE_OUTPUT"

python -m ml.training.finetune_whisper \
    --model_id tarteel-ai/whisper-tiny-ar-quran \
    --data_dir "$QARI_DATA_DIR" \
    --output_dir "$QARI_SMOKE_OUTPUT" \
    --language ar --epochs 1 --batch_size 4 --learning_rate 1e-5 \
    --warmup_steps 5 --max_steps 20 --max_samples 300 --eval_split 0.10 \
    --use_fp16 --gradient_checkpointing

test -s "$QARI_SMOKE_OUTPUT/train_results.json"
test -s "$QARI_SMOKE_OUTPUT/eval_results.json"
```

Only after that succeeds, start the persistent full run:

```bash
bash scripts/run_lightning_training.sh
```

If Lightning stops after at least one `checkpoint-*` directory was saved,
resume the same output directory with:

```bash
bash scripts/run_lightning_training.sh --resume
```

The equivalent manual command is:

```bash
export QARI_OUTPUT_DIR="$HOME/qari-lightning/models/qari-whisper-tiny"
mkdir -p "$(dirname "$QARI_OUTPUT_DIR")"

python -m ml.training.finetune_whisper \
    --model_id tarteel-ai/whisper-tiny-ar-quran \
    --data_dir "$QARI_DATA_DIR" \
    --output_dir "$QARI_OUTPUT_DIR" \
    --language ar --epochs 3 --batch_size 8 --learning_rate 1e-5 \
    --warmup_steps 500 --eval_split 0.10 \
    --use_fp16 --gradient_checkpointing
```

The current trainer prepares all log-Mel features in system memory before
training. Monitor both RAM and GPU utilization during the first full run; if
system RAM is exhausted, train a smaller manifest view rather than rerunning
the same oversized job.

```bash
pip install -r ml/requirements.txt transformers datasets soundfile torchaudio

# live model (latency-critical -> tiny)
python -m ml.training.finetune_whisper \
    --model_id tarteel-ai/whisper-tiny-ar-quran \
    --data_dir /data/quran_train \
    --output_dir /models/qari-whisper-tiny \
    --epochs 3 --batch_size 16

# batch model (accuracy-critical -> base)
python -m ml.training.finetune_whisper \
    --model_id tarteel-ai/whisper-base-ar-quran \
    --data_dir /data/quran_train \
    --output_dir /models/qari-whisper-base \
    --epochs 3 --batch_size 8
```

The script tracks WER on a held-out split. Judge the live model by WER on
*amateur* voices — that is where tiny currently loses to Tarteel.

Long cloud runs can resume from the newest saved Trainer checkpoint:

```bash
python -m ml.training.finetune_whisper \
    --data_dir /data/quran_train \
    --output_dir /models/qari-whisper-tiny \
    --resume_from_checkpoint
```

The output directory must be on persistent storage. The trainer retains the
checkpoint's Whisper suppression-token configuration so generated evaluation
works with current Transformers versions.

## Step 3 — Convert the live model to CTranslate2

The live engine runs CTranslate2, not PyTorch:

```bash
python scripts/convert_tarteel_model.py \
    --model /models/qari-whisper-tiny \
    --output backend/recitation_api/models/qari-ct2-tiny \
    --quantization int8
```

## Step 4 — Deploy on the VPS

1. Copy `backend/recitation_api/models/qari-ct2-tiny` to the VPS (the models
   dir is bind-mounted into the container).
2. Point the live engine at it in `infra/docker-compose.yml`:
   `QARI_FASTERWHISPER_MODEL_DIR: /app/models/qari-ct2-tiny`
3. `docker compose -f infra/docker-compose.yml up -d recitation-api`
4. For the batch model, replace the model ID/dir used by `inference-worker`
   the same way and restart it.

## Step 5 — Evaluate before shipping

Compare old vs new on the same clips before switching production:

- WER on the held-out split (professional + amateur separately);
- end-to-end: stream a few known recordings through
  `/ws/recitation/stream` and check word events against the expected
  sequence (see `backend/recitation_api/tests/test_streaming.py` for the
  harness pattern);
- latency: the live model must transcribe a 6 s window in well under 1.2 s
  on the VPS CPU (the re-transcription cadence), or tracking lags.

## Roadmap after the first fine-tune

1. **Data flywheel** — keep folding in consented user recordings; retrain
   monthly. This is Tarteel's real moat; volume of amateur voices matters
   more than architecture.
2. **Bigger live model** — if a fine-tuned tiny still mis-hears amateurs,
   try small/base with a GPU on the VPS (or batched CT2 int8 on more CPU
   cores) before giving up the latency budget.
3. **Streaming-specific training** — train on random 2–6 s crops of the
   clips (not only full ayahs) so the model sees partial-phrase windows like
   the ones the sliding-window transcriber actually feeds it.
