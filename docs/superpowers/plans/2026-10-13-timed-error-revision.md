# Timed ASR Error Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Accept independently supported corrections of existing live errors without replaying consumed speech or inventing progress.

**Architecture:** Record ref-index→hypothesis-slot provenance in the live aligner. The session checks two recent native views against the same past word and following matched audio anchor, then revises that error and prefix slot in place before normal timed stitching. The conservative wrapper enforces its existing budget.

**Tech Stack:** Python3.12, existing RNNT/Sherpa, pytest, existing Docker Compose.

**Spec:** `docs/superpowers/specs/2026-10-13-timed-error-revision.md`

## Global Constraints

- Keep original model assets/UI unchanged; no ASR reference prompts.
- Keep confidence .55, frame80ms, existing .24s right context and all speech guards.
- Revise ERROR only after two consistent distinct PCM endpoints and a unique following matched anchor.
- Preserve both cursors, hypothesis length, consumed-audio boundary and reveal budget.

## Review Focus

- Later re-reading must not clear an earlier mistake.
- Ambiguous/repeated/shared-frame words must fail closed.
- Duplicate endpoints and contradictory views must not satisfy two-view confirmation.
- Low/nonfinite/immature evidence and absent provenance/anchor must fail closed.
- Skipped Huwa, genuine substitutions and unrecited page suffix must remain unconfirmed/unchanged.

### Task1: Controlled regression and provenance

**Files:** modify `ml/alignment/streaming_matcher.py`, `backend/recitation_api/app/main.py`; test `ml/tests/test_streaming_matcher.py`, new `backend/recitation_api/tests/test_streaming_asr_error_revision.py`.

**Interfaces:** live matcher stores `_live_hyp_indices: dict[int,int]` for supported matched/error states; `revise_live_error(index, spoken, confidence) -> bool` performs one-way validation/mutation. Conservative wrapper checks existing reference/budget and delegates.

- [ ] Reproduce ERROR11 at hypothesis15 with captured timings and native views19.2/19.8; expect one later match11 with no rewind, extra state or budget.
- [ ] Run targeted pytest; verify RED from missing revision/provenance rather than harness errors.
- [ ] Record exact DP hypothesis slot when committing MATCHED/ERROR, never infer it from reference indices or spoken-token search.
- [ ] Implement explicit ERROR-only mutation retaining resolved-index membership/cursors; test no changes for skipped/pending/matched, low/nonfinite evidence or beyond-budget index.

### Task2: Timed session eligibility

**Files:** modify `backend/recitation_api/app/services/streaming_session.py`; same new recitation regression file.

**Interfaces:** `_revise_supported_timed_errors(window_words, window_confs, window_times, *, window_start, window_seconds, right_context_seconds, endpoint_samples) -> None` checks and updates only existing supported timed errors, prefix slot and state; session retains pending distinct-view evidence keyed by reference index.

- [ ] Add negative regressions from all five review conditions and genuine close/Samad substitutions.
- [ ] Validate normalized independent words, complete finite timing/scores, old/new word span overlap and start tolerance .08+1e-6, unique following matched anchor occurrence, unchanged future-context gate.
- [ ] Require two consistent eligible views at distinct PCM endpoints; clear pending evidence on absent/contradictory eligible evidence, never count repeated decode of one endpoint twice.
- [ ] Apply eligible correction before consumed timed stitching, updating exact prefix word/confidence/time and existing error state. Do not rewind/re-evaluate earlier DP alignment.
- [ ] Verify `_diff_events` emits one additive match for the former red index; other states and progress remain unchanged.

### Task3: Qualification and deployment

- [ ] Run complete `ml/tests api/tests backend/recitation_api/tests` using existing image and worktree; inspect outputs.
- [ ] Request independent review of final code and safety negatives; resolve findings.
- [ ] Replay original pinned model on all18 private cases, including proper15/Fatihah29, oldHu sentinel still14 if ASR absent, silence/noise/wrong-surah/prefix controls and genuine substitutions. Report existing ASR limitation explicitly.
- [ ] Only after revision is safe, test .6 cadence with the full cases and paced isolated WebSocket replay. Require newproper15LIVE/15FINAL with no false red, stable real substitutions and measured latency improvement. Keep .9 if any regression.
- [ ] Commit/push isolated branch/draft PR and deploy only qualified backend improvement through existing configuration; verify running source/model hashes/policy and public paced tests. Do not mark the complete user goal achieved while old Huwa or delay remains unresolved.

Execution ledger: isolated from43a; controlled revision RED→GREEN, ML312 and Rec181 passed. Review added real maybe_transcribe unusable-view regression; all4 interruptions reproduced RED. Empty/timeless/invalid paths fixed, then exact native-exception branch fixed after the complete suite caught it. Decoded endpoint uses start+len(audio), allowing received PCM to advance during decode; race regression RED→GREEN. Test harness seed declares loaded reference metadata and earned prior speech budget; original startup/reveal guards were preserved.

Review complete: pending reset gap reproduced through actual decode path (4RED), fixed and full312ML/API+185Rec=497PASS. Frozenv2 originalmodel full18:17pass, onlyexistingoldHu14/15. No nativeerrors/untimed/prompted; finalsourcebyteidentity verified. Tasks1–2 complete; commit/deploy source-only correction qualified. Cadence remains .9; startup-grid private full18 also17pass/newfirst8.4 versus9.0 andzero false red, staging/public latency gates still pending.
