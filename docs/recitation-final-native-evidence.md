# Retaining native evidence in final review

A final recording decode can recognize the correct word with lower confidence
than the last two live decodes of the same audio. Previously, final review lost
those earlier witnesses when the live cursor had not reached that word.

The captured Baqarah 1–20 recording demonstrates this at word index 228, `شيء`.
The independent full-recording decode scores its normalized token `شي` at about
0.483. Two consecutive original live windows score it at 0.907 and 0.577. Both
identify the same original occurrence between `كل` and `قدير`.

Final review now retains the previous and current bounded native views. It may
confirm an otherwise absent final verdict only when:

- The independent final decode contains that same token below the existing
  confidence threshold, between two already confirmed final anchors.
- All three identities occur exactly once in both the selected reference and
  the independent final transcript. The final tokens remain adjacent.
- The existing two-view proof validates native confidence, mature frames,
  increasing endpoints, original anchor occurrences and agreement in time.
- The current view ends at the received PCM endpoint, and its middle span also
  agrees with the original independent final token's span.
- The speech budget permits the position, and the frames are not owned by any
  other confirmed live/final word or earlier native repair.

Supported errors and matches are preserved. Empty, failed or untimed primary
recognition breaks the retained pair. Stub, injected and other recognition
policies do not use this path. No additional model call is made; live cursors,
UI, models, confidence thresholds and bounded recording review remain unchanged.

This repairs evidence retention, not general model accuracy. The Baqarah
recording still contains many ASR mismatches and uncertain words. A decoder's
disagreement is not proof that the speaker made a recitation mistake.
