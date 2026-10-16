# Same-audio correction of a live ASR error

User requires independently confirmed live words, genuine substitutions red while the cursor continues, all ayah markers, existing models/confidence/speech guards, and no silence/wrong-speech completion.

Observed on the proper saved Ikhlas with a private .6s cadence: at18.6s Yakun reference11 becomes ERROR from native Yaqul .942, hypothesis slot15 (four Bismillah prefix words), emission17.18–17.42. At19.2 native Yakun .976 covers17.22–17.70 and following matched Lahu starts17.94 versus prior17.98. At19.8 Yakun .958 repeats. Consumed-prefix retention discards the new word; DP cannot revisit resolved errors. Final independent review does correct it. This is separate from old phone Huwa absent in ASR.

Permit only one-way ERROR→MATCHED from two consistent mature native timed views of that same audio occurrence, using distinct PCM endpoints. Require complete recorded hypothesis-slot provenance, overlapping word bounds, starts within one80ms emission frame, and a unique immediate following already-matched anchor whose start is within the same80ms frame. Reject ambiguous/shared-frame alternatives, later re-reading, low/nonfinite/immature scores, and missing anchors. A view contradicting or lacking eligible evidence clears pending confirmation.

Keep confidence .55, existing right context .24s plus80ms frame support, reference/reveal bounds, all cursors, hypothesis length, consumed-audio boundary and speech budgets. Never upgrade SKIPPED/pending, fabricate Huwa, downgrade MATCHED, or supply expected text to ASR. Production cadence stays .9 until complete safety and paced tests prove a .6 improvement. Existing Flutter handles later match updates for a red index; no UI change.
