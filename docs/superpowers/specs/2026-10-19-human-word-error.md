# Human word-error research experiment

The user wants deliberate harakat/adaegi errors detected without false green
words, false alarms on correct speech, extra delay or memory crashes. Existing
lexical tracking and UI guards must stay intact. Three phonetic recognizers and
the synthetic-trained head have not qualified. On ten held Ikhlas opening clips,
an alignment-marginalized prefix contrast still preferred canonical pronunciation
on three of five contributor error labels and an inserted vowel on one of five
correct labels. A threshold change is not established as a repair.

## Question and approach

Can a small audio-only, word-conditioned error classifier trained on actual
human binary word labels distinguish errors on speaker-disjoint Ikhlas audio?
The public pinned MuazAhmad7/Surah_Ikhlas-Labeled_Dataset contains 1506 clips,
384 participant IDs, 851 error/655 correct utterances, but only one surah.
Binary word-error supervision does not require inventing realized-phone targets.
This experiment is explicitly a narrow research test, not full Quran grading.

Alternatives considered: another canonical phone-text decoder repeats the
observed failure; broader human phone training still needs gated data access.
Direct word-error classification tests a different hypothesis with public data.

## Data contract

- Pin revision 973b5ef1d1532bcbe7e9a5a5b0dce125cc4d0dac and metadata SHA.
- Accept explicit binary label/name and consistent filename; quarantine conflicts.
- Correct utterances supply negative labels for their words. Error utterances
  supply positive labels only at uniquely mapped listed error locations; every
  other word remains unknown and is masked from training/evaluation.
- Ambiguous locations, mismatched references and missing labels are quarantined.
  Ayah3 bare `lam` cannot distinguish the two occurrences and is ambiguous.
- All24 previously probed participant IDs are reserved, never training or tuning.
  Remaining speakers use the first8hex digits (first32bits) of SHA256(`qari-human-word-v1:`+id), converted to an integer, modulo10:0 validation,
  1 test,2–9 train. Same-speaker clips never cross partitions.
- Fetch public source WAVs only, max3MB each/1GB total. Native mono/stereo PCM
  resampled to16k with fixed scipy polyphase filtering; .25–12s, finite/.006RMS
  speech guard. Check actual source/floatPCM hashes in a full audit before encoding/training.
  Quarantine every participant ID involved in any exact PCM duplicate group,
  including their other unique clips, preserving original role assignments. The
  training validator still rejects any unresolved duplicate. Reserved audio is
  hashed but never used for optimization. Fetch at most4 sources concurrently in
  deterministic order with a shared reservation-protected1GB content-read budget.
- No user audio, canonical phone targets or held test labels enter optimization.
  Contributor labels are not represented as independently adjudicated truth.

## Model and execution

Frozen original Whisper-base encoder and byte-identical original frontend;
actual20ms512D frames only. Small padding-safe128D temporal projection, learned
15 word-position queries, four-head acoustic attention and shared binary head.
This restricts learned word identities to Ikhlas; no generalization claim.
Use FP32, finite loss/gradient guards, seed42, AdamW.001, batch16, at most30epochs,
early stop after6 unimproved validation losses after epoch6. Validation selects
checkpoint and a conservative error threshold (FPR<=.02, maximize recall). Test
and reserved diagnostics run once after selection; never select on their scores.

Remote private TeslaT4 only, existing private frozen encoder dataset; whole-job
7100s budget including bootstrap/provider7200s cap, GPU2GiB and disk4GiB reserves,
resident12GiB guard. No raw cache or large weights downloaded to this VPS.

## Evidence and release boundary

Report split counts/speakers/known words, exclusions and exact hashes, per-ayah
and overall false accepts/alarms/recall, unknown words excluded transparently,
CPU portability and head timing separately from app latency. The head remains
qualified=false and production_changed=false even if this narrow test improves;
one-surah data cannot meet existing multi-surah/vowel/gemination/consonant gates.
No live integration, scoring/API/UI changes, signing or model replacement.

Tests must catch label leakage, filename/reference ambiguity, unknown words
becoming negatives, repeated-word ambiguity, padding contamination, nonfinite
training, and test scores influencing validation-only threshold selection.
