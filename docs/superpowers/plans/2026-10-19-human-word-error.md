# Human word-error research implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Test human word-error classification without altering production.
**Architecture:** Speaker-disjoint human binary masks over frozen audio features;
15 learned word queries attend to a small temporal projection. Only validation
selects checkpoint/threshold; test/reserved speakers remain held.
**Tech Stack:** Python3.12/3.13, NumPy, PyTorch FP32, frozen CTranslate2 encoder,
soundfile and scipy polyphase resampling; private KaggleT4.
**Spec:** docs/superpowers/specs/2026-10-19-human-word-error.md

## Global constraints

No production/model/UI changes. Preserve all existing guards and holdouts.
Pinned source, .25–12s16k speech, .006RMS, 3MB/file, 1GB total. Max30epochs,
FP32,7100s whole job, provider7200s, private only. Always qualified=false.

## Review focus

- Dataset label/name/filename conflicts must quarantine, never silently flip.
- Repeated target words and unlisted error-utterance words must stay unknown.
- Source/PCM duplicates across any partitions must stop before optimization.
- Padding peers/tails must not change logits of real acoustic samples.
- Held test/reserved scores must not choose checkpoint or decision threshold.

### Task 1: Conservative human word-label contract

**Files:** Create ml/training/human_word_data.py; tests ml/tests/test_human_word_data.py.
**Interfaces:** parse_label_row(row,reserved_speakers)->dict with speaker/role/15targets,
15mask, source file; raises ValueError for ambiguous provenance/word mapping.
select_threshold(validation_rows)->float uses only explicit validation records.

- [ ] Write failing tests: correct masks, error-only positive masks, reference and
filename conflicts, repeated lam, speaker reservations, stable disjoint roles,
validation-only threshold selection with tied scores/FPR bound.
- [ ] Run focused tests and observe assertions fail from missing implementation.
- [ ] Implement stdlib parsing, deterministic split and threshold selection.
- [ ] Focused tests pass; audit all pinned metadata without downloading audio.
- [ ] Commit contract and audit findings.

### Task 2: Bounded acoustic word classifier

**Files:** Create ml/training/human_word_head.py and ml/tests/test_human_word_head.py.
**Interfaces:** HumanWordHead.forward(features,lengths)->B,15 logits;
train_word_features(manifest,output,device,epochs,deadline)->unqualified report.
Consumes Task1 targets/masks, actual frame files and split identities.

- [ ] Tests RED for padding-peer/poisoned-tail invariance, finite gradients,
masked unknown loss, cross-split duplicate/speaker rejection, validation/test
isolation and bounded CPU smoke optimization with retained finite guard.
- [ ] Implement padding-safe projection/attention and strict manifest checks,
FP32 training, validation-only selection and separate held predictions.
- [ ] Focused tests and complete recitation/ML/API suite pass; commit.

### Task 3: Private extraction, training and actual result

**Files:** Create ml/training/kaggle_human_word_job.py; runner boundary tests.
Private launch/monitor/artifacts live outside repo under P4/human-word-experiment.
Consumes Tasks1/2 and existing verify_encoder/extract_batch/job_budget helpers.

- [ ] RED tests for bounded source/audio extraction, repeated PCM and exclusions.
- [ ] Implement source pin/metadata SHA, safe audio decoding/resampling/hash cache,
reserves/deadline, atomic reports. Reserved waveforms hashed but not trained.
- [ ] Verify tests/full suite; one fresh whole-branch review and one fix pass.
- [ ] Commit/push research branch/draft PR; submit one privateT4 job with verified
source/private settings. Watch actual logs through terminal status; no blind retries.
- [ ] Retrieve small reports/head only, evaluate original CPU portability if
successful, update context with actual success/failure and qualification limits.
