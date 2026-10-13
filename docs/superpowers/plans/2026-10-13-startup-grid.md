# RNNT Startup Grid Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans task by task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Reduce first selected-word reveal delay without changing models, recognition guards or later decode context.
**Architecture:** Before reference progress use .6s new-audio checks. After progress, the pure interval predicate targets the next absolute .9s PCM-sample grid, shared by audio wakeups and transcription eligibility. Keep Whisper/stub and configured first-pass behavior intact.
**Tech Stack:** Python3.12, existing RNNT/Sherpa, pytest, existing Docker infrastructure.
**Spec:** User's autonomous recognition/delay goal; private `original-startup-grid-full-replay-20261013` original-model18 cases:17pass/sole existingoldHu14; newproper15/noRed/firstaudio8.4vs9.0, Fat29, all safety controls retained. Offline eligibility is not public latency proof.

## Global Constraints

- Original models/UI, independent tier2, confidence .55, speech/RMS/timing guards and reference budgets remain unchanged.
- Pure scheduling: repeated queries cannot alter cursor, consume PCM or count as recognition.
- No shorter ASR window or expected text supplied to decoder.
- Older phone Hu remains unresolved; do not claim full goal complete.

## Review Focus

- Irregular PCM chunk sizes and overshooting a grid must never return a zero/negative interval or spin.
- Audio wakeup and actual transcription must share the same predicate.
- Stub/Whisper and explicitly enabled early-first-pass behavior remain unchanged.
- Silence/wrong-surah/incomplete-page inputs must not gain progress.
- Real paced staging must show correct15/29 matches and a measured improvement before deployment.

### Task1: Implement and verify scheduler

**Files:** `backend/recitation_api/app/services/streaming_session.py`, new `backend/recitation_api/tests/test_startup_grid.py`.

- [ ] Write failing tests for .6 startup, .6 remaining after8.4s firstmatch, normal .9 at9.0, irregular samples, purity and real audio-ready threshold; watch RED.
- [ ] Change only RNNT interval branch: integer .9s sample grid, next-grid-minus-last-used samples; before cursor progress return .6. Preserve configured first-pass and fallback engines.
- [ ] Run complete recitation/ML/API suites and original-model full18 replay on frozen source; independent review.

### Task2: Stage and deploy qualified improvement

- [ ] Run local paced WebSocket staging with original models, original runtime dependencies and synthetic staging auth; compare with public c117 recorded timings, include all original QA controls and exact receivedPCM.
- [ ] Inspect recognition events, timings, all markers, wrong-word red/continuation and transcribe errors.
- [ ] Only after all gates pass, commit/push/draft PR and deploy via existing config with preserved dependencies; verify running source/model/config and public paced results.

Ruling: proceed inline under existing autonomous authorization; no repeated approval request. Keep all source/model qualifications and the original broader goal intact.

## Verified implementation evidence (2026-10-13)

- Startup/grid RED: six failures before implementation. Review regressions RED: actual audio wake fired at 1000 instead of 1001 residual samples; actual native-loop failure slept62.5µs. Shared RNNT rounded sample threshold now feeds all four consumers; independent failure retry floor .9s. Legacy integer conversion preserved.
- Complete suites:196 recitation API +312 ML/API =508 passed. Existing source-contract assertion updated to the shared sample helper; behavioral boundary/loop tests cover the changes.
- Frozen source main b5316f3ab5c15426a12e9506524db104da073f4306ebb8ff99f0a94294403690 and SS32ef665804665954179a760e2b14e05a4da2131f3a665d0e3962be91e2a420c5. Original model18-case replay:17passed, sole existing older-phone Ikhlas Hu14/15; zero native errors, untimed results or prompted calls. Proper M4A15live/15final/no red, first eligibleaudio8.4s.
- Independent review: no remaining blockers; exhaustive14,400 residuals exact; bounded failure retry .9s.
- Paced isolated normal-priority stage (original model/runtime, no competing inference): proper M4A15/15/no red/all15markers/unreached43words hidden/owned PCM exact/pongs responsive; first8.692895s, stop1.244828s. Public c117 baseline samePCM first9.278451s, stop1.165694s. Stage nice19 prior run first8.806335/stop2.996901; preserve as confounded result, not qualified production performance.
- Full six-case paced staging and subsequent production verification remain required before claiming rollout complete. Older-phone Hu omission remains unresolved and cannot be inferred from reference text.
