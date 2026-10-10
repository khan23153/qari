# Confirm the selected passage before resolving its words

An opening invocation before Al-Fatihah shares “Allah” with the selected first ayah. The live matcher could align that one shared word to reference index 1, then classify the preceding invocation token as a mistake on “bism” at index 0. It committed that false position before Al-Fatihah began, so the genuine later “bism” could not replace the red event.

At cursor zero, a live alignment now needs either the first reference word or two adjacent confident matches to distinct reference and hypothesis words. The condition stays inside the existing word and ayah bounds. A single shared word or a repeated word cannot establish the initial position. Once tracking starts, existing substitution handling and cursor progression remain unchanged. A genuine wrong first word can still be marked red when two following words establish the passage.

Confidence 0.55, RMS 0.006, models, the 7.5-second audio window, 15-second encoder padding, 64-token decode cap, final review and Flutter/UI are unchanged. This is a matcher start guard; it does not crop stored live audio by a fixed duration.

Verification: six new regressions cover canonical and ASR-spelled invocation prefixes, later recovery, initial substitution, confidence/adjacency and repeated words including fuzzy reference variants. The tests reproduced five failures on the old matcher; a review-found repeated-hypothesis case failed separately before correction. All 23 matcher tests pass. Fresh ML/API 189 and recitation API 76 tests pass (265 total). Independent review/direct checks passed.

Recorded native witnesses from the complete normal-recorder take were replayed with per-window sample-count and RMS checks. Coverage improves from 6/29 plus the false initial red event to 7/29 with no confirmed red event. The older full Qari capture retains 5/29 and zero confirmed red events. This matcher-only replay uses actual captured ASR tokens/confidences; it does not claim fresh ASR execution or latency.

The user-authorized Fatiha-only copy removes 6.10 seconds in the quiet gap before Bismillah, preserves the original and every remaining PCM byte, and lasts 56.3535 seconds. A native replay through the deployed 7.5-second policy matches 7/29 with no confirmed red event. Remaining phone words are still missed or spelled differently; this fix does not qualify complete phone recognition. Private audio and full traces remain outside the repository.

A separate 12-second-context diagnostic improved phone coverage but reduced reference Al-Fatihah to 23/29 with one confirmed red event and Al-Ikhlas to 8/15, so it was withheld. A separate article-liaison probe also introduced two unverified red events and was withheld. Neither experiment changes this patch's audio window or similarity rules.

Native qualification with the unchanged live audio window: reference Al-Fatihah 29/29 and Al-Ikhlas 11/15 with no confirmed red events; wrong-surah, digital silence and seeded noise produce zero events. Four seconds of reference speech plus 20 seconds of silence/noise produces exactly four matches, no late events after the speech leaves the window and no completion.
