# GPU phoneme training implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline; a fresh reviewer checks the completed branch. Steps use checkbox syntax.

**Goal:** Scale the existing audio-only phoneme pilot on the user's available Kaggle GPU and qualify its actual outputs.

**Architecture:** Pure split selection and a padding-safe temporal CTC head are separate from the public-data/Kaggle runner. The runner verifies frozen model inputs, extracts actual audio features, trains and records an explicitly unqualified synthetic candidate. A private allowlisted packet is submitted and monitored through completion.

**Tech Stack:** Python, PyTorch, NumPy, faster-whisper1.0.3, CTranslate2 CUDA, public Hugging Face streaming data, Kaggle CLI2.2.4.

**Spec:** docs/superpowers/specs/2026-10-18-gpu-phoneme-training.md

## Global constraints

- Original encoder frozen; no text decoder or expected-phone target fallback.
- Iqra_TTS pinned97d27c2a575739e7aaffee2518d6817d203829c9; at most8192train/512validation.
- Jessica held voice;15% held reference groups;1536clips per training voice maximum.
-20ms/512D actual frames, CTC blank0; unknown validation phones count as errors.
-40epochs/7200seconds maximum, oneT4;4GiB remote disk and2GiB GPU reserves.
- Private encoder input contains only five known model files and hashes; no user audio or credentials.
- No production or APK changes before independent human qualification.

## Review focus

- Reference presentation variants must not leak the same sentence across splits.
- Batch padding and padded encoder frames must not become phone evidence.
- Duplicate PCM and unknown target phones cannot inflate validation results.
- Runtime/frontend mismatch must be recorded, never hidden behind encoder weight identity.
- Saved checkpoints must correspond to the reported best epoch; resource failure must not report success.

## Task1: Split selection and temporal head

Files: ml/training/phoneme_gpu.py; ml/tests/test_phoneme_gpu.py.
Interfaces: reference_group(text), source_role(row), TemporalPhoneHead(vocabulary_size).

- [ ] Write failing grouping, voice/text exclusion, actual-target and padding-invariance tests; observe RED.
- [ ] Implement the minimal split helpers and masked temporal head, finite shape guards and CTC feasibility reuse.
- [ ] Verify focused tests and complete existing suites, then commit.

## Task2: Bounded Kaggle runner

Files: ml/training/kaggle_phoneme_job.py; ml/tests/test_kaggle_phoneme_job.py.
Interfaces: verify_encoder(path), extract_batch(encoder, samples), train_features(manifest, output, epochs).

- [ ] Write failing frozen-input, no-decoder, actual-frame, finite-training and checkpoint-report tests.
- [ ] Implement pinned public streaming selection, source hashes, feature caching and bounded training/reporting.
- [ ] Run real CPU smoke through injected synthetic features, complete suites and a fresh branch review; fix important findings with RED/GREEN.

## Task3: Submit, monitor and evaluate

- [ ] Assemble allowlisted private encoder/data/code packet; verify original hashes before and after.
- [ ] Submit one privateT4 job with7200-second cap using authenticated current CLI.
- [ ] Watch actual logs, stages and resources through terminal status; repair concrete job failures as needed.
- [ ] Retrieve bounded candidate/reports; test original CPU encoder plus held-out audio and negative controls.
- [ ] Update context.md with actual run, results, deployed revision and remaining failures. Never claim full qualification from synthetic PER.
