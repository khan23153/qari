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

```bash
python scripts/build_training_dataset.py --out /data/quran_train
```

Downloads per-ayah recitations for the app's 5 reciters from everyayah.com,
converts them to 16 kHz mono WAV, and pairs each clip with the Uthmani text
from the bundled corpus. Output is `manifest.jsonl` + `audio/` in exactly the
format `ml/training/finetune_whisper.py` consumes (~31k clips for the full
run; use `--surahs 1-2 --reciters Alafasy_64kbps` for a smoke test).

To reach Tarteel-level robustness on *ordinary users* (not just professional
qaris), extend the manifest over time with:

- the Hugging Face `tarteel-ai/everyayah` dataset (crowd-sourced recitations,
  same (audio, text) shape — thousands of amateur voices);
- our own users' uploads: the batch pipeline already stores WAVs + the target
  ayah per session, which is exactly a manifest row. Add rows only from
  sessions the user consented to share.

## Step 2 — Fine-tune

Needs a GPU machine (Colab/Kaggle/rented). CPU training is not practical.

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
