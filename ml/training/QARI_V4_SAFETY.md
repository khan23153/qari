# Qari V4 training safety policy

This workflow replaces the Phase-3 training recipe that over-amplified a small
RetaSy subset and produced decoder repetition collapse on historical and native
HF evaluation.

## Environment

Use the managed CUDA PyTorch already installed by Kaggle/Lightning. Do not
reinstall torch.

```bash
python -m pip install --no-cache-dir -r ml/training/requirements-qari-v4.txt
python - <<'PY'
import torch
import transformers
print('torch=', torch.__version__)
print('cuda=', torch.cuda.is_available())
print('transformers=', transformers.__version__)
assert torch.cuda.is_available()
PY
```

Pinned training stack:

- transformers 4.46.3
- tokenizers 0.20.3
- accelerate 1.1.1
- datasets 3.1.0
- evaluate 0.4.3
- jiwer 3.0.5
- soundfile 0.13.1
- scipy >=1.11,<2

## Required data policy

Before any GPU run:

1. Start from `tarteel-ai/whisper-tiny-ar-quran`, not a failed experimental checkpoint.
2. Cap augmentation by underlying clean audio lineage.
3. Do not use eight augmented copies per RetaSy clean clip. V4 target is at most one augmentation per clean clip unless a later controlled experiment proves otherwise.
4. Apply a per-normalized-transcript cap so short/common ayahs cannot dominate the optimizer.
5. Keep evaluation speaker-disjoint where speaker IDs are known.
6. Do not use the historical 46-test for model selection; it is a regression check only.
7. The final release gate must use a genuinely new phone/amateur speaker-disjoint set.

## Trainer defaults

`ml.training.finetune_whisper_robust` now defaults to:

- FP32 (`--no-fp16` behavior by default)
- encoder-only adaptation (`--train_scope encoder`)
- label smoothing = 0
- explicit audio attention masks
- strict rejection of audio >30 seconds
- strict rejection of labels >448 tokens
- best model selected by normalized Arabic WER
- collapse diagnostics for prediction/reference word ratio, overlong outputs, and repetition loops

The trainer writes `qari_release_gate.json`. A failed collapse gate raises an
error after preserving the best model and metrics for diagnosis. A passing
collapse gate is **not** permission to deploy; the external phone/amateur test
still decides release.

## Smoke command

Use a small balanced manifest first:

```bash
python -m ml.training.finetune_whisper_robust \
  --model_id tarteel-ai/whisper-tiny-ar-quran \
  --train_manifest /data/qari_v4/smoke_train.jsonl \
  --eval_manifest /data/qari_v4/smoke_eval.jsonl \
  --output_dir /models/qari-v4-smoke \
  --epochs 1 \
  --batch_size 4 \
  --grad_accum 2 \
  --learning_rate 2e-6 \
  --eval_steps 4 \
  --save_steps 4 \
  --logging_steps 1 \
  --train_scope encoder \
  --label_smoothing_factor 0 \
  --no-fp16 \
  --gradient_checkpointing
```

Required smoke checks:

- finite gradients throughout
- no attention-mask warning
- no hidden duration/label truncation
- `eval_repetition_loop_rate` near zero
- `eval_overlong_rate` near zero
- `qari_release_gate.json` passes

Only after the smoke passes should a larger V4 run be launched.

## Full-run starting point

Keep the first V4 full experiment conservative:

```bash
python -m ml.training.finetune_whisper_robust \
  --model_id tarteel-ai/whisper-tiny-ar-quran \
  --train_manifest /data/qari_v4/train_manifest.jsonl \
  --eval_manifest /data/qari_v4/eval_manifest.jsonl \
  --output_dir /models/qari-v4 \
  --epochs 2 \
  --batch_size 4 \
  --grad_accum 4 \
  --learning_rate 2e-6 \
  --warmup_ratio 0.05 \
  --weight_decay 0.01 \
  --eval_steps 40 \
  --save_steps 40 \
  --logging_steps 10 \
  --train_scope encoder \
  --label_smoothing_factor 0 \
  --no-fp16 \
  --gradient_checkpointing
```

Do not switch to `--train_scope full`, FP16, more epochs, or heavier RetaSy
oversampling merely to reduce training loss. Each change must be isolated and
benchmarked against the fresh base and the external regression sets.
