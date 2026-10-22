# Acoustic phoneme pilot implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan inline. Steps use checkbox syntax.

**Goal:** Test whether a separate CTC phoneme head over the existing frozen audio encoder learns altered-speech targets without canonical text decoding.

**Architecture:** A bounded data-preflight/training utility consumes hashed synthetic PCM plus actual `phoneme_mis`. The existing independent encoder supplies512-dimensional20ms frames. An experimental frame classifier emits phonemes; production remains unchanged until human qualification.

**Tech Stack:** Python, NumPy, existing faster-whisper/CTranslate2, PyTorch CPU.

**Spec:** docs/superpowers/specs/2026-10-18-acoustic-phoneme-pilot.md

## Global constraints

- At most128 clips; original held-out user recordings never train.
- No canonical reference target fallback or text-decoder calls.
- Frozen existing models; experimental weights outside repository and production paths.
-3500MiB totalmemory,2CPUthreads/lowpriority,512MiB disk reserve.
- Human phoneme labels and pronunciation release gates required before rollout.

## Review focus

- Missing altered-phone labels must fail rather than use the canonical answer.
- Same reference sentence across voices must not leak into validation.
- Repeated phones require sufficient CTC frames.
-30-second encoder padding must not become real short-clip frames.
- Unknown validation phones count as errors rather than being silently dropped.

## Task1: Bounded pilot utility

Files: ml/training/phoneme_ctc_pilot.py; ml/tests/test_phoneme_ctc_pilot.py.

- [x] Write failing target-selection, disjoint-split, CTC-length, encoder-crop and greedy-decode tests.
- [x] Run focused tests and observe meaningful failures.
- [x] Implement pure preflight functions and lazy optional ML imports; add bounded feature extraction/training CLI.
- [x] Prepare pinned public synthetic fixtures outside git; retain SHA256, voice and original-reference grouping.
- [x] Run the CPU pilot with live log/resource monitoring; save all metrics and rejection/next-step decision.
- [x] Run appropriate suites and independent review. Commit tested utility and update context.md. Do not promote the experimental model.
