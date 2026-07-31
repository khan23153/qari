# Robust ASR phase two: amateur voices, phone audio, and speaker-disjoint evaluation

Use this workflow after a model trained on clean professional reciters performs
well on its random validation split but hallucinates on real phone recordings.
The phase-one model weights are retained, but the phase-two run uses a fresh
optimizer and explicit manifests.

## Why the old metric was misleading

`ml/training/finetune_whisper.py` shuffles individual clips before creating its
validation split. With only five studio reciters, the same voices and recording
conditions can therefore appear in both training and evaluation. That measures
interpolation within the professional domain, not generalization to an unseen
speaker or phone microphone.

Phase two uses:

- professional recordings for clean anchor data;
- correctly-labelled amateur recordings;
- local AMR/M4A/WAV phone recordings;
- speaker-disjoint validation and test sets;
- synthetic background noise, reverberation, bandwidth reduction, compression,
  resampling, gain changes, microphone self-noise, and capture silence;
- untouched evaluation and test audio.

Never pair an incorrect recitation with the correct Quran transcript. That would
teach ASR to output the target verse even when the acoustic evidence differs.

## 1. Locate the repository and existing data

```bash
set -euo pipefail

export QARI_REPO="$(find "$HOME" /teamspace/studios -maxdepth 7 \
  -type f -path '*/scripts/prepare_robust_qari_data.py' \
  -printf '%h\n' 2>/dev/null | sed 's#/scripts$##' | head -n 1)"

test -n "$QARI_REPO"
cd "$QARI_REPO"

export OLD_MANIFEST="$(find "$HOME/qari-lightning/data" /teamspace/studios \
  -type f -path '*/quran_train/manifest.jsonl' -print 2>/dev/null | head -n 1)"
test -s "$OLD_MANIFEST"
```

## 2. Install phase-two dependencies

Preserve Lightning's CUDA-enabled PyTorch installation.

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg unzip wget

python -m pip install \
  'transformers==4.46.3' 'accelerate==1.1.1' \
  'datasets==3.1.0' 'evaluate==0.4.3' 'jiwer==3.0.5' \
  'soundfile>=0.12.1' 'scipy>=1.11' 'tensorboard>=2.16' \
  'faster-whisper>=1.1.0'

python - <<'PY'
import torch
assert torch.cuda.is_available(), "CUDA GPU is unavailable"
print(torch.__version__, torch.cuda.get_device_name(0))
PY
```

## 3. Download real room responses and noises

```bash
export AUG_ROOT="$HOME/qari-lightning/augmentation"
mkdir -p "$AUG_ROOT"
cd "$AUG_ROOT"

wget -c https://www.openslr.org/resources/28/rirs_noises.zip \
  -O rirs_noises.zip
unzip -q -o rirs_noises.zip
```

The script falls back to synthetic noise and room responses when these
directories are omitted, but real recordings are preferable.

## 4. Add local phone recordings

```bash
cd "$QARI_REPO"
mkdir -p "$HOME/qari-lightning/phone_raw"
cp ml/training/phone_metadata.example.jsonl \
  "$HOME/qari-lightning/phone_metadata.jsonl"
```

Edit the copied JSONL. Every line must contain the exact words spoken, a stable
speaker ID, and one split. Keep each person in only one split. For the first
experiment, keep the primary tester's voice in `test`.

Recommended minimum:

- train: 8–20 amateur speakers;
- eval: 3–5 different speakers;
- test: the primary tester plus 3–5 different speakers.

## 5. Build explicit manifests

```bash
export PHASE2_DATA="$HOME/qari-lightning/data/quran_robust_v2"
rm -rf "$PHASE2_DATA"

python scripts/prepare_robust_qari_data.py \
  --professional_manifest "$OLD_MANIFEST" \
  --output_dir "$PHASE2_DATA" \
  --include_retasy \
  --retasy_max_samples 6000 \
  --phone_metadata "$HOME/qari-lightning/phone_metadata.jsonl" \
  --noise_dir "$AUG_ROOT/RIRS_NOISES/pointsource_noises" \
  --rir_dir "$AUG_ROOT/RIRS_NOISES/simulated_rirs" \
  --augment_copies 1 \
  --amateur_eval_fraction 0.15 \
  --amateur_test_fraction 0.15 \
  --min_duration 0.6 \
  --max_duration 30 \
  --seed 42

python -m json.tool "$PHASE2_DATA/dataset_report.json"
wc -l "$PHASE2_DATA"/*_manifest.jsonl
```

Validation and test files are copied/converted to clean 16 kHz WAV and are not
augmented. Professional clips remain training-only because five known studio
reciters are not a meaningful production test cohort.

## 6. Start from phase-one final weights, not its Trainer checkpoint

```bash
export OLD_MODEL="$HOME/qari-lightning/models/qari-whisper-tiny"
export PHASE2_MODEL="$HOME/qari-lightning/models/qari-whisper-tiny-robust-v2"

test -s "$OLD_MODEL/config.json"
rm -rf "$PHASE2_MODEL"

python -m ml.training.finetune_whisper_robust \
  --model_id "$OLD_MODEL" \
  --train_manifest "$PHASE2_DATA/train_manifest.jsonl" \
  --eval_manifest "$PHASE2_DATA/eval_manifest.jsonl" \
  --output_dir "$PHASE2_MODEL" \
  --epochs 2 \
  --batch_size 8 \
  --grad_accum 2 \
  --learning_rate 5e-6 \
  --warmup_ratio 0.05 \
  --weight_decay 0.01 \
  --eval_steps 500 \
  --save_steps 500 \
  --logging_steps 25 \
  --num_workers 4 \
  --early_stopping_patience 3 \
  --fp16 \
  --gradient_checkpointing
```

For GPU out-of-memory errors, use `--batch_size 4 --grad_accum 4`. Do not add
more epochs merely because training loss continues decreasing.

An interrupted phase-two run may resume from a checkpoint inside
`$PHASE2_MODEL`. Do not resume a phase-one checkpoint after changing the data.

## 7. Convert and compare on the untouched test set

```bash
export PHASE2_CT2="$HOME/qari-lightning/models/qari-ct2-tiny-robust-v2"
rm -rf "$PHASE2_CT2"

python scripts/convert_tarteel_model.py \
  --model "$PHASE2_MODEL" \
  --output "$PHASE2_CT2" \
  --quantization int8

python -m ml.evaluation.evaluate_faster_whisper_manifest \
  --model_dir "$PHASE2_CT2" \
  --manifest "$PHASE2_DATA/test_manifest.jsonl" \
  --compute_type int8 \
  --output_jsonl "$PHASE2_DATA/new_model_test.jsonl"
```

Evaluate the old CT2 model on the same manifest. Ship based on phone-test WER,
hallucination behavior, and the existing VPS latency benchmark—not on the old
random professional-reciter validation metric.

## Release gates

1. New model beats the old model on the same untouched speaker-disjoint test.
2. The primary tester's Al-Fatiha and Al-Ikhlas recordings no longer produce
   unrelated Arabic hallucinations.
3. `ml.evaluation.benchmark_latency` stays within the live-service budget on
   the actual VPS.
4. End-to-end WebSocket tracking is tested with real phone PCM, not only file
   upload transcription.
