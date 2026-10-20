# Human Realized-Phone Adaptation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans; implement inline with one fresh final reviewer before remote execution.

**Goal:** Measure whether actual human spoken-phone supervision reduces canonicalizing errors without changing live Qari.
**Architecture:** Reproduce pinned source/group/content manifests, adapt the final two layers/native CTC head of the existing80-class phone model, then observe private remote execution and bounded original-CPU evidence.
**Tech Stack:** Python,PyTorch,Wav2Vec2ForCTC,Transformers4.57.6,DuckDB1.4.1,Kaggle CLI.
**Spec:** docs/superpowers/specs/2026-10-20-realized-phone-supervision.md

## Global constraints

- All outputs qualified=false/production_changed=false. No root production/model/UI edits.
- Frozen Extra1330source rows/1327accepted; prospective split563train/26val/50test.
- Actual phoneme_mis targets only; native80IDs/blank77/delimiter75, no canonical fallback.
- Prefix groups are not verified physical speakers; no group/content/PCM overlap.
- FP32/finite CTC, only layers22/23+lm_head, max20epochs/patience4/min3,lr1e-5/clip1/seed42.
- Private input/kernel,7100/7200s remote budgets,RSS12GiB/disk4GiB/GPU2GiB; no credentials.
- Local fixtures32rows/2epochs/<=1Mparams; test containers<=1500MiB; no full CPU training.

## Review focus

- Canonical-only/missing/unknown labels must never become acoustic targets; case/geminates/delimiters preserved.
- Content aliases/sparse prefix groups/duplicate PCM cannot leak across roles or claim verified speakers.
- Native blank77/delimiter75 and odd partial accumulation batches must not corrupt CTC.
- Delta missing/extra keys, wrong base identity, mutation of frozen weights and CPU overbounds reject.
- Fresh provider layout, source/decode identity, privacy and negative speech controls do not permit unsafe live grading.

### Task1: Frozen human source/split/target contracts

Files: ml/training/realized_phone_data.py; ml/tests/test_realized_phone_data.py.
Consumes raw metadata, full source PCM audit, native80-token vocabulary.
Produces `realized_targets(row,vocabulary)->list[int]`,
`build_realized_manifest(metadata,audit,vocabulary)->dict` with all roles/exclusions,
and `validate_realized_manifest(manifest)->None` preserving physical-speaker unknown.

- [ ] RED target tests: `u`/`U`, `b`/`bb` remain distinct; literal q,u,l ->[53,75,64,75,45]. Missing phoneme_mis/unknown/[PAD]/empty rejects despite canonical present.
- [ ] RED split tests: alias text/identical expected phones union; prospective hash rule independent of row order; 2val/3test eligible-prefix rule; sparse groups train; no overlap and no false physical-speaker verification. Duplicate IDs/accepted duplicatePCM/mixed source pins reject.
- [ ] Implement stdlib-only parser/split/manifest with exact native conv frame accounting and immutable identity. Source floors retained; incompatible training CTC rows excluded and held PER denominator retained.
- [ ] Focused GREEN and actual pinned audit replay equals prospective artifact563/26/50 and every case role/frame count. No model scores. Expected: all tests pass and exact replay equality.
- [ ] Full recitation/ML/API suite and commit. Expected: green baseline1114 plus new tests.

### Task2: Bounded native FP32 delta training and remote entry point

Files: ml/training/realized_phone_adaptation.py,ml/training/kaggle_realized_phone_job.py; corresponding ml/tests.
Consumes Task1manifest/native IDs plus pinned Wav2Vec2ForCTC and actual waveforms.
Produces native-model delta/report/predictions with base/source/frontend/split identity.

- [ ] RED tiny-native-model tests for exact final2layers/lm_head update whitelist and unchanged frozen digest; finite CPU fixture training/validation PER; native blank-aware repeated phone decoding; source features never receive expected text.
- [ ] RED tests for odd final microbatch sample weighting; caller autocast disabled over forward/backward/optimizer; nonfinite loss/grad fails without saving; original vocab/config preserved.
- [ ] RED delta loader tests missing/extra/shape/nonfinite/wrong-base reject; valid exact whitelist roundtrip reproduces logits. Local >32rows/>2epochs/>1Mparams rejects before output/optimizer.
- [ ] Implement FP32 AdamW exact spec, baseline/final evaluation, min validation PER checkpoint, earlystop4/min3,max20; no held selection. Keep unknown/padding/CTC length behavior explicit. No external dependency beyond existing image/runtime.
- [ ] RED remote CLI tests invalid context/device/source before output/download; full source/PCM bytes and metadata/split exact, original .006RMS/.25–30s guards; CUDA resource/deadline sampling and private provenance.
- [ ] Implement remote native loader(strict80/77/75/config/pins), cache only selected source waveforms, source/PCM revalidation, native frontend, outputs and immutable frozen-state check. Context before heavy work; private input not embedded corpus/token.
- [ ] Focused/full GREEN, sourcepack compile/hash check and commit. One fresh review of Tasks1–2. Address Important findings once with RED->GREEN/full suite; note minors.

### Task3: Private observed full run and original CPU evidence

Files: external packet/observer; report docs/realized-phone-evidence-20261020.md; root context.md.
Consumes frozen code/data/splits/model pins and private provider metadata.
Produces actual terminal result, small delta/report/predictions, optional bounded CPU comparison.

- [ ] Prepare private input dataset (original source conditions/other license). Verify uploaded file metadata/private flag and pinned data identity; no HF token upload. Verify private kernel/source bytes before execution.
- [ ] Submit one private T4 full job7100/7200s; observe actual readiness/epochs, inspect failure logs and diagnose if necessary. Never silently resubmit/choose by test scores.
- [ ] Retrieve only small artifacts. Report baseline/adapted PER and actual failures; no release when unqualified. If delta exists, verify hash/allowed keys then bounded16held CPU comparisons with RAM-only original weights4GiB hard/3.5soft/.75CPU/1200s.
- [ ] Update report/context/stacked draft PR with measured outcomes, physical-speaker/provenance and Quran-waqf/streaming limitations. No UI/deployment/APK changes. Expected: actual outcome, including honest failure if adaptation does not help.
