# Expert vowel-error evaluation after dataset approval

The user approved the separate TestGT dataset. Authenticated access changed from
HTTP403 to HTTP206 on 21 October 2026 at 11:20 UTC. This resolves the previous
access blocker. It does not repair or qualify a pronunciation model.

## Source identity and coverage

- Expert labels: `IqraEval/IqraEval_Test_GT`, revision
  `cd27009525365f911ddd773c0b3b70cac82f2f0b`, `labels_test.csv`, 250,819 bytes,
  SHA256 `834bc1f1e410549b1962d1d7445b0e7730b65168d67f82fb35507adaa5e6b8d7`.
- Audio: `IqraEval/QuranMB.v2`, revision
  `75afc3391e47ca005af286b2518d8a2edf98da5d`, test parquet, 220,472,046 bytes,
  SHA256 `332b3e4b99a35456f7eeea2f85d9d651d9d9ceb3ff57d41e59ca668d1cba62b9`.
  Its train-named parquet is the identical blob and was not downloaded twice.
- All 1,642 unique audio IDs match the label IDs. There are 18 ID prefix groups;
  Qari has not independently verified physical speaker identity.
- Reference and annotation differ in 1,532 rows; 110 are identical. Exactly 168
  rows contain a single internal short-vowel-quality substitution, covering
  `a→u`59, `u→a`29, `i→u`27, `A→U`16, `i→a`6, `a→i`20, `u→i`11.
  Native case and double-phone symbols are preserved.

A complete source audit found 1,546 mono and 96 stereo WAVs, all 16kHz. The initial
strict mono assertion stopped the audit; channel metadata explained the stop.
The corrected audit uses the unchanged native helper's SoundFile float32
`always_2d=True` and `mean(axis=1)` handling. Original stereo bytes are retained.
This was an audit assumption, not a production model failure.

Two duplicate PCM groups have identical annotations and lie outside the selected
cohort. No source PCM matches the known Extra training PCM manifest. This does
not establish independence from every public model's training or tuning data.

## Frozen diagnostic probe

Before predictions, the protocol selects all 168 single internal-vowel errors
and all 110 exact-correct clips. These 278 recordings total 1,155.85 seconds,
include eight stereo clips, have maximum duration 13.62 seconds, and all exceed
RMS .006. The remaining corpus is not inferred by this probe.

The existing complete CROTTC-IF bundle, native defaults and weight revision are
unchanged from the earlier screen. No model is trained, no threshold is selected,
and no reference text or gold annotation reaches the model. Gated labels stay on
the VPS; only original public WAVs and a whitelisted audio manifest are uploaded
to a private inference dataset. Provider metadata and all 279 file names/sizes
were checked. Model weights are downloaded only on the remote worker.

The private T4 job is `telethonfool/qari-expert-vowel-probe-20261021` v1. Limits are
1,800 seconds in the launcher and 1,860 explicitly supplied to the provider,
12GiB RSS, 4GiB disk reserve and 2GiB GPU reserve. Native mono and stereo file-helper
parity adds two passes; three research non-speech controls give 283 total passes.
Independent review found no Critical or Important issues and reconstructed all
278 source PCM hashes without model execution.

## Scoring contract

Host scoring requires every fixed ID, source/protocol hashes, native vocabulary
mapping, emission/frame ranges, runtime versions and resource limits. At each of
168 gold targets, canonical retention is a false accept; the heard gold vowel is
correct diagnosis; a different phone or deletion is wrong diagnosis. Ambiguous
optimal alignments and unmapped outputs stay explicitly unassessed. All 168
remain in denominator accounting. Eight functional tests, including an exhaustive
225 sequence-pair optimal-alignment oracle, pass.

Unit-Levenshtein diagnostic results and the unchanged organizer MDD scorer are
reported separately. The latter's original weighted alignment is not silently
replaced; errors/timeouts remain visible. Correct clips also receive phone-error
and exact-utterance counts. These are offline phonetic diagnostics, not live word,
Hifz cursor, all-tajweed or streaming-latency qualification.

## Verified execution result

The run completed all 283 passes in 595.89 seconds, peak remote RSS 4,283,616 KiB
(approximately 4.085GiB). Native mono/stereo helper parity and independent host
output verification passed. The candidate remains rejected for production.

| At the 168 expert vowel-error targets | Acoustic | Joint |
| --- | ---: | ---: |
| Correct diagnosis | 109 | 98 |
| Canonical vowel retained: false accept | 15 | 16 |
| Ambiguous: unassessed | 24 | 34 |
| Vowel deleted: wrong diagnosis | 20 | 20 |

All targets remain accounted for. Acoustic whole-cohort unit-Levenshtein phone
error is 685/8,493 (8.07%); joint is 2,047/8,493 (24.10%). For the 110 correct
recordings, exact utterances are only 13 acoustic and 8 joint. Acoustic correct
clip phone error is 326/3,562 (9.15%). These are recognition diagnostics and must
not be presented as a reliable pronunciation verdict.

All 15 acoustic false accepts concern expected /a/ versus expert-heard /u/:
14 `a→u` and one `A→U`. Their native emitted-phone confidence ranges from .7456
to .9949; all exceed the existing .55 diagnostic guard. No threshold was retuned.

The unchanged organizer MDD scorer completed separately. For this selected
cohort both modes report recall .9167, precision .3548, F1 .5116, FAR .0833 and
FRR .0336 (TA8045, FR280, TR154, FA14, correct diagnosis133, error diagnosis21).
Its weighted alignment convention differs from the conservative unit-edit target
analysis above; neither result replaces the other. Do not advertise its 96.54%
phone-dominated overall accuracy as pronunciation qualification.

The official analysis skips many unmatched predicted insertions: its scores are
identical despite acoustic/joint annotation-to-prediction insertion counts
370/1,732. Raw phone errors and repeated output remain material failures.
Research silence/noise/tone still produce acoustic/joint phone counts 8/28,
3/28 and 2/28. These controls do not exercise live WebSockets or cursors.

## Next hypothesis and data limits

A read-only check of the unchanged Extra training split finds 74 internal
vowel-quality substitutions, including 19 `a→u`, versus four validation examples
(two `a→u`, two `u→a`). There are no training `a→i` error pairs. Actual heard
short-vowel labels cover 8,085 training and 318 validation tokens; all 24,616
training/validation phones are representable in the native vocabulary. No TestGT
labels are used for training, and the quarantined split remains quarantined.

The next bounded offline question is whether local raw acoustic vowel features
can predict heard vowel quality without canonical-word priors. This is a new
hypothesis, not a trained or qualified replacement. Repeating the current ASR,
raising its confidence threshold or counting noisy unique transcripts as correct
would not establish that capability.

No model, backend, UI, confidence/speech guard or APK changed. No remote run
remains active from this experiment.

Durable packet: `/home/innocent/qari-training-artifacts/iqra-expert-eval-20261021/`.
The gated CSV is neither committed nor included in the remote input package.
