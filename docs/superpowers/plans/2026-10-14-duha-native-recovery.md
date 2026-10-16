# Duha native recovery implementation plan

> Execute inline with superpowers:executing-plans. User requested autonomous repair and deployment; existing production checkout stays intact during qualification.

**Goal:** Fix independently evidenced live-word loss and investigate the two genuine ASR substitutions in the complete supplied Ad-Duha audio.

**Architecture:** Preserve native posterior scores, timestamps, speech budgets, known-word identity and two-view revision guards. Prevent a previously consumed native word from being appended again merely because its independently recognized spelling gains the definite article. ASR alternatives remain private diagnostics until independently qualified.

**Tech stack:** Python, Sherpa RNNT, Docker, pytest.

**Spec:** User's live-backend repair request and active Duha goal; private evidence at `/home/innocent/qari-training-artifacts/duha-recorder-20261014`.

**Constraints:** No UI/model asset changes for stitching fix; confidence .55, RMS .006, timing and speech guards unchanged; held audio evaluation only. Never accept faabi as faawa or taqhar as tanhar simply to pass.

**Review focus:** Later genuine repeats stay distinct; weak words cannot confirm a gap; no article stripping for Allah/lillah; ambiguous/shared native frames remain rejected; wrong surah and silence cannot complete a page.

## Task 1: Prevent duplicate article variants from consumed audio

- [x] Add captured Yatim/Al-Yatim stitching regression and repeat/weak/identity controls to `backend/recitation_api/tests/test_timed_overlap.py`.
- [x] Run focused tests and observe expected duplicate-token failure.
- [x] Extend spelling equivalence in `_words_similar` only for the two reviewed Yatim/Al-Yatim and Sail/Al-Sail spelling identities; generic article stripping merges different Quran words. Preserve PCM and confidence conditions in `_stitch_timed_hypothesis`.
- [ ] Run full recitation API plus ML/API suite, then actual native Duha/Baqarah and safety replays.
- [ ] Request independent review, commit/push qualified change. Deploy only after equivalent-resource staged/public checks. Do not claim Duha40/40 while ASR substitutes words.

## Task 2: Resolve independent ASR substitutions and remaining live gap

- [ ] Evaluate predeclared beam4/8, original CTC, original FP32 and already-trained RTA alternatives with no expected text, fixed full/30–42/60–72s windows. Record failures as well as successes.
- [ ] Determine an audio-only decoder/window change from evidence; first write its meaningful failing tests and negative controls.
- [ ] Qualify full Duha40, Baqarah56, Fatiha29, new Ikhlas15 and existing safety controls with actual native recognition, all suites, review, staged then public paced replay.
- [ ] Verify actual deployed source/revision/models/logs; mark goal complete only after real required acceptance passes.

Qualification update: exact shared-frame guard regression observed failing then fixed; complete RecAPI+ML/API suite608 passes and independent review has no remaining blocker. Added two distinct native past-anchor witnesses around one weak token to prevent the second Sail duplication, preserving existing confidence/timing/frame uniqueness guards. Final-source native Duha, Baqarah and17 safety cases are running; no deployment or full40/40 claim yet. Public diagnostic sources: Tarteel acknowledges occasional false flags and asks for recitation evidence, not automatic word acceptance: https://support.tarteel.ai/en/articles/16559266-a-mistake-was-flagged-that-i-didn-t-make .
