# Observed mistakes / red UI specification

## Scope

Implement immediate *supported* lexical mistake feedback and conservative observed-ASR diacritic diagnostics, not a claim to reproduce a proprietary service's acoustic model. Independent human pronunciation qualification is still open. Lexical recognition and raw emitted vowel evidence must remain distinct.

## Wire / presentation

- Preserve legacy `match` / `error_skipped` status compatibility.
- Confirmed omitted words behind independently established progress: `error_type=missed`.
- Confident independently observed wrong lexical word: `error_type=substituted`.
- Explicit emitted vocalic conflict at an aligned letter of the same lexical word: `error_type=harakat_mistake`, `evidence_source=asr_diacritic`.
- Confirmed errors use `display_color=#EF4444`; Flutter uses literal opaque `Color(0xFFEF4444)` regardless of Mushaf theme. Future/unreached words remain normal/pending; low confidence remains uncertain, not a confirmed error. Do not paint all missing final-reference suffix words red.
- Maintain source occurrence, cursor/ayah/speech guards, .55 live confidence, .006 RMS and confirmed-only Hifz reveal. Missing words cannot be inferred before subsequent speech establishes the skip. A resumed window must not lose already-proven omissions or borrow vowels from a later repeated occurrence.

## Observed harakat

- Replace dagger alif U+0670 with fatha U+064E and deduplicate identical consecutive harakat.
- Compare vocalic marks by aligned letter position, not flattened vowel strings. Missing or ambiguous canonical/observed marks abstain. If spelling/letter alignment is ambiguous, abstain rather than shift positions.
- Missing final marks are inconclusive. Final sukun at a possible stop (ayah end/current stream end/no following word) is exempt. Explicit conflicting a/i/u/tanwin remains a conflict even at a stop; explicit wasl sukun versus a vowel conflicts. Pausing does not license an explicitly emitted wrong vowel.
- Production decoding must receive no target-ayah text. FastConformer RNNT is already unprompted. The fast production worker uses independent base Whisper with `initial_prompt=None`, `condition_on_previous_text=False`; lock both options in regression tests. Generic research-only prompted decoder methods are not qualified correctness paths.
- No available pronunciation/tajweed metric is introduced. A missing emitted mark or canonicalized ASR output cannot prove correct pronunciation.

## Acceptance

- Tests cover dagger-alif duplicate prevention, الْعَالَمِين / الْعَالَمِينْ stopping, absent/partial tashkeel, explicit أَنْعَمْتُ before عَلَيْهِمْ, missed لِلَّهِ رَبِّ between supported anchors, invalid confidence and unread suffix guards.
- Real backend and Flutter tests, exact red color widget assertions, independent review.
- Run actual saved-audio public live matching and silence/wrong-surah negatives. If emitted marks are absent, label the harakat outcome inconclusive rather than inventing human acoustic results.
- Build/update core, recitation and inference-worker containers, verify packaged/live-mounted source identity, runtime health, production independent decoding and public routes. Preserve rollback code/images. Do not replace a published APK with incompatible signing; Flutter source/test completion is not installed-APK rollout.
- Keep context.md current with real results and pending work; do not erase historical rejected experiments.

## Final source verification — 24 October continuation

- Backend/ML/API complete suite: **1,197 passed, 1 optional skip, 2 dependency warnings**. Core API: **43 passed, 1 warning** with a disposable, network-isolated PostgreSQL instance, then test DB removed/readback verified.
- Flutter: **77 focused tests and all 267 full-suite tests passed** under 2 GiB/no swap/.75 CPU; targeted analysis of 14 changed/new Dart files found no issues. Formatting and git whitespace checks pass.
- Review repaired EOS context after a confidently observed substitution, retained final native hypothesis slots, and preserved proven omissions after window loss and empty final review. Flutter now retains evidence-confirmed token-free omissions even when their numeric confidence is zero, but rejects malformed confidence values. Recorded RED/GREEN regressions accompany these changes.
- Dagger-alif normalization, partial/absent marks, waqf/sukun/fathatan cases, explicit conflicting final vowels and missed لله/رب have passing controlled-evidence regressions. This is not evidence that an acoustic model detects every deliberately changed vowel.
- Live baseline 5-case saved-public-audio checks pass before rollout. Candidate private/public real-audio qualification and deployment are the next gates, not implied by unit/widget counts.
- Source evidence and run logs: `/home/ubuntu/qari-task-artifacts/observed-mistakes-20261024/`. Android SDK and compatible release signing config are absent: no replacement APK has been built or installed.
