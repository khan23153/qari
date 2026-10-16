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
- [x] Upload only the explicit private training package/fixtures, then launch the private GPU notebook.
- [ ] Verify notebook status and training startup; record its URL and input/source revisions.
- [x] Run required repository checks, commit/push reviewed changes, and build the updated APK.
- [ ] Report training status separately from recognition accuracy; retain current production weights until the candidate qualifies.

Review: low-confidence recognition gaps remain neutral via explicit evidence confirmation; only a bounded, high-confidence spoken substitution is red. RED→GREEN and full suites verified.

Ruling: keep existing TLOG rows training-only while reporting their unknown speaker identities; do not claim full speaker-disjointness. Known RetaSy evaluation speakers remain separate. Cost if wrong: unknown sources could overlap evaluation speakers, so fresh phone tests and the VPS benchmark are still mandatory and automatic model promotion is disabled.

Private pilot submitted on 2026-10-08: https://www.kaggle.com/code/telethonfool/qari-v52-phone-encoder-pilot-2026-10-08 (version 1, initially queued). Kaggle derived the notebook slug from its title; metadata now uses the actual ID for subsequent updates.

Private source/fixture input: `telethonfool/qari-phone-pilot-code-20261008`, created from source revision `5b89508d6644cac8b1166855924bdbf4ae940061`. Source hashes are recorded in the private package metadata. Offline Al-Fatihah and Al-Ikhlas references were generated from the bundled Quran corpus at that revision, using the existing reference-generation script (29 and 15 words respectively). Private phone audio is a release fixture, excluded from gradient training. No tokens are included in the dataset, notebook, or repository.

Backend source revision `5b89508d6644cac8b1166855924bdbf4ae940061` rebuilt and deployed through existing Docker Compose configuration; running source hashes match. Public authenticated WebSocket returned 29 reference words and emitted no word events for silence. Existing model paths and tier2 policy retained. Fresh isolated checks: recitation API 76 passed; ML plus legacy API 176 passed. Full Flutter suite: 172 passed.

Updated APK build: https://github.com/khan23153/qari/actions/runs/37816960278 succeeded; version `1.0.49+74`, release commit `2900902`. Published through the existing core API release mount at https://aiquranic.com/v1/app/download. Release metadata and future release scripts now use the deployed domain.

Deployed real-audio replay with unchanged models: reference Al-Fatihah 29/29, cursor 29; silence 0 events, cursor 0; Al-Ikhlas against Al-Fatihah 1/29, cursor 2; proper Al-Ikhlas 11/15, cursor 11; private phone Al-Fatihah 5/29, cursor 6. No falsely confirmed red errors in these positive recordings. Phone PCM remains 16 kHz mono, 36.92 seconds, RMS 0.23714; ASR text is incorrect/incomplete before matching. Mean phone decode was 2.469 seconds across 30 passes in an unpaced replay, not a phone-to-screen latency measurement. No transcribe-failure exceptions were found. Phone recognition remains inadequate; new weights have not been promoted.

Kaggle confirmed the notebook is private, GPU enabled (`NvidiaTeslaT4`), with the intended two datasets and original-base kernel output attached. Uploaded notebook bytes match submitted source. Job remained queued during deployment verification; GPU/training startup is still pending.
