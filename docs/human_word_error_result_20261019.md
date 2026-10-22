# Human word-error experiment: actual result, 19 October 2026

Qari's pronunciation false-acceptance issue remains unresolved. The repaired
training pipeline completed a private GPU experiment, but the resulting head
failed release qualification and was **not deployed**.

## Training failure repaired

Version2 stopped before optimization because pinned public source
`data/ID247V1T.wav` is3,310,754bytes, above the3MB individual-file cap. It raised
the same generic error used for total download exhaustion and aborted the audit.
The pinned tree totals713,449,399bytes; this was not the1GB total limit.

Commit `b7c230ae81c3287232bb8d9b6f5fe0c05d3aef19` introduces a specific
individual-file exception and records a transparent exclusion. Partial reads
have a consumed-byte count and **no invented full-file hash**. The3MB/1GB limits,
network/identity failures, .006RMS speech guard and split/leakage protections
remain in force. A real fetch confirmed stopping at3,000,001bytes and successful
decoding of the following valid pinned source.

Regression: original exception reproduced, then12focused tests passed.
Complete recitation API plus `ml/tests` and `api/tests`: **1029passed,1skipped**,
2existing dependency warnings. All four GitHub CI jobs passed. These software
tests do not establish pronunciation accuracy.

## Observed private GPU execution

Kernel `telethonfool/qari-human-word-errors-20261019`, version3: **COMPLETE**.
Provider source was pulled and verified byte-identical to the tested packet.
TeslaT4, original frozen encoder/frontend, private original-encoder input only,
no user audio uploaded/trained. Provider7200s/whole-job7100s limits retained.
Launcher SHA: `d04f4fa76120d7d7be580e4e1008466f0b7719eebfdaa2f8b440b028f5082ccd`.
Candidate-head SHA: `f396e657f637eb0c886e58c4ab2c2307455211ad5b02ecb7f6192f8f9ce7fd9a`.

Full actual-PCM audit left1393clips: train1055, validation122, test127, reserved89.
13duplicate PCM groups involved19participant IDs; all81clips from those IDs were
quarantined before encoding.19speech-guard exclusions and1oversized source were
excluded too, in addition to12annotation exclusions from metadata.
All24previously probed participant IDs stayed reserved; cohort roles were not
reshuffled. No threshold/checkpoint tuning used test or reserved scores.

10epochs completed; validation chose epoch4 and error threshold0.7857852578163147.
The frozen text-only word-position-prior baseline detected0errors at its own
validation-selected conservative threshold. This is a baseline comparison, not
an accuracy comparison against Qari's live lexical tracker.

| Evaluation cohort | Labelled errors | Detected | Missed | Correct words | False alarms | Error recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Validation | 88 | 68 | 20 | 238 | 3 | 77.27% |
| Held test | 96 | 75 | 21 | 216 | 13 | 78.12% |
| Reserved (all) | 61 | 34 | 27 | 148 | 5 | 55.74% |
| Reserved CPU vowel subset | 15 | 1 | 14 | 70 | 0 | 6.67% |

Unknown words are masked, not counted as negatives:165unknown test words and
123unknown reserved words. Contributor labels have not been independently
adjudicated. The experiment covers Ikhlas full-ayah clips only, with15learned
word-position queries; no other-surah, live partial-word or latency qualification.

## Failure detail

Of21missed test errors,14are in ayah3:7on `يلد` and7on `يولد`.
Ayah3 also accounts for8of13test false alarms. Remaining test misses:
ayah1 `قل`1/`الله`1/`احد`2; ayah2 `الصمد`1; ayah4 `يكن`1/`احد`1.
These are source-word locations; binary annotations do not identify the actual
phone the reciter uttered. The test false-alarm rate is6.02%, above the2% guard;
precision85.23% is below98%, and recall78.125% is below90%.

The smaller previously reserved vowel-error diagnostic is worse. Original VPS
CPU evaluation retained34of35clips; ID165V1F was correctly excluded because it
did not survive the cleaned GPU cohort. Of15contributor-labelled harakat error
words, **1was detected and14missed**, with0false alarms on70correct words.
All34resampled PCM identities matched; CPU and GPU made **0different decisions**
on known words. This supports that the observed misses are not a CPU-conversion
regression. Median head-only CPU forward time:5.51 ms, excluding encoder,
audio buffering, alignment and network; this is not live app latency.

The old one-off CPU evaluation helper incorrectly tagged every mixed binary
label as `vowel`; it was backed up and corrected to an unclassified binary-word
kind before evaluation. The15specific error labels above were then separately
verified to have source category `حركات`. No vowel/gemination/consonant coverage
was fabricated. Encoder/frontend identities and candidate head hash were checked.

## Interpretation and next boundary

The head learns some acoustic error signal, but its overall score hides poor
harakat generalization. Training includes mostly tajweed-labelled errors and
mixed-category utterances; only2training error utterances are pure-harakat,
compared with15in the reserved cohort. This is a distribution/co-occurrence
warning, not proof of a single causal mechanism. Its full-ayah attention may
also use context that does not isolate the erroneous word; that hypothesis
requires a separate experiment.

Do not lower confidence, tune the threshold on the held test/reserved cohort,
force expected words, or call the candidate a pronunciation fix. A next design
needs separate vowel supervision and adequate pure-error/correct human support,
word-local evidence or qualified alignment, and independent speakers/surahs.
Freeze this result; pre-register any new training/validation selection and
retain an untouched final evaluation. Broader Iqra_Extra_IS26/IqraEval_Test_GT
access still returned403 on authenticated checks at20:06UTC. No credentials
are included in this report or the private training packet.

The candidate remains `qualified=false` and `production_changed=false`.
Production recitation revision remains
`0c7562b0ee35cee33f9e1884ac5f8e9a6974a37d`: healthy,0restarts,noOOM at the observed
check. Existing models, confidence/speech guards and confirmed-only Hifz UI
remain unchanged. No APK build or deployment was performed.

## Retained evidence

- Packet, exact source identity, status/log observer and outputs:
  `/tmp/qari-conformer-training-20261009/human-word-20261019/`.
- GPU report/head/audit/predictions: its `output-v3/` subdirectory.
- CPU features and `cpu-reserved-word-results.json`:
  `/home/innocent/qari-training-artifacts/pronunciation-human-data-20261018/human-word-experiment/`.
- Complete suite log: parent `human-oversized-full-suite.log`.
- Research branch `fix/human-word-error-20261019`, draft PR38:
  https://github.com/khan23153/qari/pull/38.
