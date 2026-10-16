# Repairing live recognition gaps from independent native evidence

A complete held-out Ya-Sin recording exposed seven live gaps and two false
substitutions despite correct final review. The original models often recognized
the words correctly in later windows. Three implementation issues blocked them:

- Recovery windows advanced in one-second steps although RNNT emission frames
  advance by80ms. Adjacent one-second origins differ by half an encoder frame.
  A controlled original-audio probe recognized `ومتاعا` at416.00s/416.08s,
  but `ومتاع` at416.04s;417.00s/417.04s showed the reverse pair. Both ordinary
  and recovery windows now retain the recording's original80ms frame origin.
  Recovery remains bounded to at most20.08seconds, within the previous21s ceiling.
- A consumed word's emission end could grow in a later view. Float32 rounding
  or a slightly earlier first frame defeated a1microsecond equality check and
  appended the word again. Same-identity past starts within80ms are consumed;
  genuine later repetitions are retained.
- A missing token has no old hypothesis slot; a provisional low-confidence
  token can also have different emission bounds once context grows. A tracker
  that freezes all consumed evidence cannot reveal those later recognized words.

`ml/alignment/native_evidence.py` compares two consecutive independent native
views. Repair requires an exact three-word identity sequence, both already
matched neighbors, unchanged confidence >=0.55 for all components, complete
mature nonoverlapping frames, agreement within80ms, and unique correspondence
to the original neighbors (maximum400ms first-emission movement). Even weak
competing same-identity anchors make the occurrence ambiguous. Previously owned
matched frames and earlier native repairs cannot be reused for another word.
Close rereading, uncertainty, duplicates, interrupted evidence, or evidence
outside the original occurrence cannot repair an earlier mistake.

The production wrapper enforces the existing measured-speech budget. Repair
changes only an earlier unresolved/error WordState and records its real native
provenance. It neither inserts hypothesis slots nor moves cursors. Missing-slot
or changed-spoken repairs fail the existing fast final-evidence audit and receive
the existing independent bounded recording review. No expected text enters ASR.

Models,0.006RMS silence guard,0.55confidence guard, speech/ayah bounds, UI,30s
long-recording review chunks and6GiB/no-swap production limit remain unchanged.
No training occurred. Full recitation API + ml/tests + api/tests:739passed,
two existing dependency warnings. Captured actual evidence fixtures, real
omitted/spoken-other-word controls, and complete fresh recognition replay are
retained under the task's training-artifacts directory, strictly for testing.
