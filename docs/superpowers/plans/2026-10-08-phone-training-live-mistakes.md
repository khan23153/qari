# Phone ASR training and live confirmed mistakes implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline execution. Steps use checkbox tracking.

**Goal:** Start a private Kaggle training pilot and make confirmed live mistakes red without stopping recitation.

**Architecture:** Reuse the existing independent ASR and guarded matcher. Add a validated Kaggle run wrapper around the robust encoder-only trainer; update Hifz rendering for confirmed mistakes behind the cursor.

**Tech Stack:** Python, existing Whisper/CT2 models, Kaggle CLI, Flutter/Dart.

**Spec:** docs/superpowers/specs/2026-10-08-phone-training-live-mistakes.md

- [x] Inspect and validate existing Kaggle manifests, original tiny-base model, and runtime pins.
- [x] Add a failing widget regression for a wrong word in red followed by correct words, with future words hidden and all markers visible.
- [x] Make the minimal renderer change; verify relevant widget, cursor, and review tests.
- [x] Add failing data-preflight tests for label/audio pairing and split leakage.
- [x] Implement the Kaggle pilot wrapper using existing trainer and guards; validate the package locally.
- [ ] Upload only the explicit private training package/fixtures, then launch the private GPU notebook.
- [ ] Verify notebook status and training startup; record its URL and input/source revisions.
- [ ] Run required repository checks, commit/push reviewed changes, and build the updated APK.
- [ ] Report training status separately from recognition accuracy; retain current production weights until the candidate qualifies.

Review: low-confidence recognition gaps remain neutral via explicit evidence confirmation; only a bounded, high-confidence spoken substitution is red. RED→GREEN and full suites verified.

Ruling: keep existing TLOG rows training-only while reporting their unknown speaker identities; do not claim full speaker-disjointness. Known RetaSy evaluation speakers remain separate. Cost if wrong: unknown sources could overlap evaluation speakers, so fresh phone tests and the VPS benchmark are still mandatory and automatic model promotion is disabled.
