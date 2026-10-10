# Live word spelling and conservative mistake confirmation

The full phone Voice Recorder take stalled at reference word 7: independent ASR emitted `لعالمين`, while the reference had lost the dagger alef in `ٱلْعَـٰلَمِينَ` and became `العلمين`. The existing ayah clamp then prevented later correctly decoded words from advancing tracking. This was an alignment defect in addition to genuine ASR errors. The older full Qari capture still has poor independent recognition; this patch does not solve that recording.

Normalize dagger alef to ordinary alef before removing Quranic diacritics, derive comparison keys from the original display spelling, and accept the dropped article wasla when the remaining stems are identical. Compose article removal with the existing phonetic threshold only for same-length emphasis-letter substitutions. A different attested Quran word cannot use this new composed-emphasis branch; an explicitly empty vocabulary disables it. Existing fuzzy, full-word phonetic and single-alef policies remain unchanged. No arbitrary alef deletion is added to stripped stems.

Only confidently recognized words from the entire reference corpus may establish new live substitution errors. Garbled strings become unconfirmed skipped states, and later recognized anchors may continue tracking. This corpus vocabulary is never an ASR prompt and never supplies matched words. It includes legacy and dagger-expanded spellings, is immutable and cached by store identity. Final review still scores the authoritative transcript and may report unknown substitutions. A non-Quran word or pronunciation error may therefore remain unconfirmed live; this is a conservative word tracker, not a verified phonetic/tajweed assessor. An incomplete reference corpus cannot confirm all substitutions.

Flutter files, display text and ayah markers are untouched. The independent unprompted CT2 base witness, trained review model, live evidence policy tier2, confidence .55, RMS .006, 7.5-second recognition window, 15-second encoder floor and 64-token cap are retained. This server change does not require a new APK or deploy the rejected Conformer candidate.

## Tarteel comparison

| Publicly documented observation | Application to Qari |
| --- | --- |
| Tarteel found that choosing an ayah did not guarantee the actual transcript matched it; it also reported problems from inconsistent audio formats. | Keep actual independent ASR as evidence; do not use selected-surah text as training truth. Trace PCM format and compare the app capture with the normal recorder. |
| Tarteel allows progression after a mistake when its correction-blocking setting is off, and acknowledges both false flags and missed similar-sounding mistakes. | A confirmed wrong word stays red while the cursor follows later evidence. Uncertain model output stays unconfirmed. |
| Tarteel reported NVIDIA optimization and under-200ms recognition in January 2022. | Treat this as a historical vendor claim, not a measured current phone-to-screen baseline. Qari's CPU decode timings do not establish parity. |
| Tarteel describes buffering/uploading audio every 20 seconds for session data collection. | This is an upload interval, not a published ASR inference window. Qari's live window is unchanged. |
| The public Tarteel Whisper model card leaves training-data details and limitations unspecified. | The public checkpoint does not establish the architecture or policy used by Tarteel's current proprietary app. |

Primary sources checked 2026-10-10: [Tarteel ML journey](https://tarteel.ai/blog/tarteels-ml-journey-part-1-intro-data-collection/), [mistake support guidance](https://support.tarteel.ai/en/articles/16559266-a-mistake-was-flagged-that-i-didn-t-make), [2022 mistake-detection announcement](https://tarteel.ai/blog/introducing-mistake-detection/amp/), [public Whisper model card](https://huggingface.co/tarteel-ai/whisper-base-ar-quran). The matcher module now describes Qari's own dynamic programming implementation instead of attributing an unverified current algorithm to Tarteel.

## Verification

The complete suite passes: **216 ML/API tests + 79 recitation API tests = 295**. Targeted regressions were observed failing before each correction, including confidence, dagger alef, misleading stem/alef combinations, known interior substitutions and empty-vocabulary handling. Independent review used the actual 6,236-ayah store, 16,649-entry service vocabulary and 14,826 canonical reference keys: 2,164 comparisons covering the new matching branches yielded zero new matches for attested words. Cold store loading took .87 seconds and vocabulary construction .28 seconds; cached reuse took approximately 5 microseconds.

Fresh native CPU recognition with the existing production models/policy:

| Audio / selected passage | Confirmed matches | Confirmed red errors | Cursor / words |
| --- | --- | --- | --- |
| Original 36.92-second Qari capture / Fatiha | 5 | 0 | 6 / 29 |
| Full normal phone recorder / Fatiha | 24 | 0 | 28 / 29 |
| Same recorder, opening invocation trimmed / Fatiha | 22 | 0 | 28 / 29 |
| Public reference / Fatiha | 29 | 0 | 29 / 29 |
| Public reference / Ikhlas | 11 | 0 | 11 / 15 |
| Ikhlas / Fatiha | 0 | 0 | 0 / 29 |
| Digital silence / Fatiha | 0 | 0 | 0 / 29 |
| Seeded noise with RMS .06 / Fatiha | 0 | 0 | 0 / 29 |
| Four seconds of reference speech, then 20 seconds silence or noise | 4 | 0 | 4 / 29 |
| Real-audio splice control / Fatiha first ayah | 4 | 0 | 4 / 4 |
| Same splice replacing Allah with Al-Samad | 3 | 0 | 4 / 4 |

Neither silence nor wrong-surah audio reveals/completes the page; prefix tests emit no events after the speech has left the window. The real splice test exposes a remaining recognition failure: independent ASR hears Al-Samad as the non-corpus string `لاصطمد`, with high segment confidence. That position remains unconfirmed, and the following words still reveal. It is not falsely green, but it also does not produce the requested confirmed live red error. Controlled recognized-word tests prove that known substitutions remain red while the cursor progresses; successful real-audio red classification remains unverified by this splice.

Full normal audio still misses reference indices 8, 9, 18, 22 and 28 (the later Rahman/Rahim, al-sirat, an'amta and al-dallin). Trimming also loses indices 13 and 25. Coverage improves from the previous production 7/29 on both normal/trimmed recordings, but whole-recitation recognition is incomplete. Full and trimmed take decode means were 1.62 and 1.52 seconds respectively in this qualification run, with some test-container contention; these are CPU decode timings, not phone-to-screen latency. The earlier deployed encoder-padding fix separately reduced the old capture mean from 2.53 to 1.39 seconds.

One qualification launch accidentally selected a duplicate normal recording under an old-phone fixture name. Its result is preserved as a duplicate and excluded from old-phone conclusions. A separate native run confirms 5/29 matches, cursor 6 and zero confirmed red errors, unchanged from production; it uses the original 36.92-second old Qari capture (SHA256 `5c27b6eb1378bad25c90c0ab73b5ea3d45c6e9604ed0e5f9e1a659a89e0c1211`). Audio and detailed ASR traces remain in the private VPS artifact directory, outside the repository. The original full recording is preserved; the user-requested Fatiha-only copy removes the first 6.10 seconds at the quiet gap and preserves all remaining PCM bytes.
