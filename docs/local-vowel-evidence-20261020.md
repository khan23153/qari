# Word-local vowel-error experiment

Production remains unchanged. This experiment is not a qualified pronunciation
grader and must not turn lexical recognition into a pronunciation verdict.

## Why this experiment exists

The previous frozen Whisper word-error head detected 1 of 15 reserved vowel
errors. An independent frozen Muaalem raw-phone probe showed vowel differences
for 9 of those 15 words, but also false differences for 5 of 70 correct words.
All four erroneous `qul` examples still decoded canonical vowels, sometimes with
very high confidence. Raising a confidence threshold does not resolve this.

The new head learns from human vowel-error locations and actual local encoder
frames. Expected phonemes condition the assessment head only; native acoustic
forward/decode receives no expected text. Exact consonant matches shared by all
minimum-edit alignments locate words. Ambiguous/low-confidence/missing anchors
remain unavailable. A preflight using 34 actual native probe outputs located all
15 labelled vowel-error words and 70 correct words; this is localization coverage,
not detection accuracy.

## Frozen inputs and supervision

- Dataset: `MuazAhmad7/Surah_Ikhlas-Labeled_Dataset`, revision
  `973b5ef1d1532bcbe7e9a5a5b0dce125cc4d0dac`.
- Accepted audio: 1,393 clips from the preceding complete source/PCM audit;
  24 reserved speaker IDs and 19 quarantined duplicate-audio participants retained.
- Known vowel positives before crop eligibility: train 143, validation 12,
  test 11, reserved 22. Correct utterance words are negatives; unlisted or other
  error categories stay unknown. Two ambiguous category/location rows stay unknown.
- Teacher: `obadx/muaalem-model-v3_2`, revision
  `01a1ef9fbe40d144ef845101e89ff924aed3fef5`, model SHA256
  `6b6a2e85303d17ff0f3af5e1fc79ac83daecee409c756ddf27f0ced59393bb41`.
- Original-word phonetic references were generated once using
  `quran-transcript==0.6.1` with original Uthmani character mappings. Phonetic
  whitespace is not a word boundary: `yakun` and `lahu` can assimilate.

Checkpoint selection and threshold calibration use validation only. Training
class weighting uses training only. Held unavailable words remain in recall and
coverage denominators. A text-only reference-prior baseline is also reported.

## Execution and verification

Research branch: `fix/local-vowel-evidence-20261020`; draft PR #39.
Commits: `66ec320` labels/localization, `67dc1a2` generic local head,
`8123101` native extraction, `29ea12b` bounded download deadline repair.

Latest complete recitation/ML/API suite: **1,114 passed, 1 skipped, 2 existing warnings**,
63.29 seconds. Fresh whole-branch review found one important defect: executor
cleanup could wait for unchecked trickling downloads after the job deadline.
Regression tests reproduced it; per-read checks, remaining-time socket bounds
and bounded backoff fixed it. A real alarm/thread-pool cleanup test passes too.
One in-flight socket read can still take at most 25 seconds; the provider's
100-second shutdown reserve covers that bounded cleanup.

Earlier private T4 job: `telethonfool/qari-local-vowel-20261020`, version 3,
submitted 2026-10-20 13:59 UTC and subsequently stopped at eligibility. Provider source was pulled and verified byte for
byte; private/T4 metadata verified. Initial uncompressed 2.03 MB submission
returned HTTP 400 with no kernel created; the identical extracted sources were
compressed to 427,716 bytes and accepted. No exact provider size limit is claimed.

Version 1 stopped before extraction because a new global-uniqueness check rejected
six duplicate filename pairs already excluded by the frozen audit. Commit
`60984bb` revalidates only the accepted cohort while still rejecting accepted
duplicates/missing/changed labels. Three regression tests and an actual pinned
CSV/audit check verified all 1,393 accepted labels and roles.

Version 2 loaded every original native model weight successfully, then stopped
before extraction on the Uthmani `لَّهُۥ` reference. The generic metadata normalizer
kept the small waw as a lexical letter. Commit `0390ce0` ignores only the Uthmani
small waw/ya for lexical comparison, preserving their actual phonetic IDs. The
regression test, wrong-real-word rejection and actual four-ayah/15-word reference
bundle validation pass. Neither failed run produced trained accuracy results.

An existing Flutter formatting check also failed on a summary constructor call.
Commit `4d445c4` changes only its line wrapping (2 lines added, 1 removed). All 16
files in the existing CI formatting command pass. UI behavior is preserved.

Limits: 7,100-second whole job including dependency installation, provider
7,200 seconds; 12 GiB resident-memory cap, 4 GiB disk reserve, 2 GiB GPU reserve;
3 MB/source and 1 GB total public downloads. The 2.42 GB teacher stays on Kaggle,
not the VPS. Original frozen model files are checked again after training.

Run packet, observer and eventual outputs:
`/tmp/qari-conformer-training-20261009/local-vowel-20261020/`.
Durable source/probe evidence:
`/home/innocent/qari-training-artifacts/phonetic-evidence-20261020/`.
No credentials or user recordings are included in the packet.

## Remaining gates

Version 3 completed native extraction for all 1,393 accepted clips, then stopped
at the declared supervision floor. Eligible word counts were:

| Split | Correct | Vowel errors |
| --- | ---: | ---: |
| Train | 1,512 | 80 |
| Validation | 212 | 7 |
| Test | 190 | 8 |
| Reserved | 139 | 21 |

Validation requires eight eligible positive words, so training did not start.
There are no learned scores, epochs or new checkpoint to report. CPU checkpoint
portability is consequently unavailable. The floor and confidence guards remain
unchanged. Of the 143 training vowel-positive words, 56 had ambiguous native
anchors and seven low-confidence anchors; all five unavailable validation
positives had ambiguous anchors. The crop policy may be overly restrictive for
some real pronunciation errors, but raw native evidence is needed before any
algorithm change. A separate 18-clip training-only diagnostic (ten failed source
cases and eight correct controls) completed and retained actual phoneme emissions/timings.
No held labels or recordings were used to tune the crop algorithm.

The experiment always reports `qualified=false`
and `production_changed=false`. One-surah contributor labels, unknown upstream
training overlap and a full-context encoder cannot establish independent
multi-surah or live-stream reliability. Restricted Iqra datasets still need the
user to review account-information sharing conditions; no consent was submitted
on their behalf. Preserve all live confidence/speech guards and existing Hifz/UI.

## Current follow-up: substitution crops and guarded CPU execution

An explicit `unique_substitution_v1` assessment-only policy can locate a word
when every minimum-edit path agrees on native consuming anchors, including a
heard substitution. It retains the actual native phone and requires contiguous
anchors, at least two anchors with at least one exact match, and the same .55
confidence. Ambiguity/deletion/all-substitution speech stays unassessed. It never
confirms lexical words or moves the cursor. Exact-only default behavior is
preserved (14,641-pair independent parity check). In the 18 actual training-only
clips, labelled-error crop availability rose 1/13 to 4/13; correct availability
26/30 to 30/30. This measures localization, not pronunciation accuracy.

Private T4 version 4 uses that frozen policy and remained queued after an hour.
Available GPU quota does not guarantee a scheduler start. A separate private CPU
smoke completed real native extraction on 11 public clips / 44 words and three
finite-loss epochs; its held accuracy was not used for selection.

The corrected private full CPU run, version 2, completed native extraction for
all 1,393 clips and stopped at the same unchanged supervision floor as T4 v4.
No optimizer epoch ran; neither run produced a candidate head or learned accuracy.

| Split | Correct words | Eligible vowel errors |
| --- | ---: | ---: |
| Train | 1,559 | 91 |
| Validation | 220 | 7 |
| Test | 200 | 8 |
| Reserved | 143 | 21 |

Validation still falls below the fixed eight-positive minimum. All five unavailable
validation positives remain ambiguous; they are retained as unassessed. Do not
tune an alignment algorithm against their held phone sequences. Training-only
unavailable positives comprise 33 ambiguous and 19 low-confidence words.

T4 v4 was ready at 15:45:32 UTC and ERROR at 15:49:08. CPU v2 was ready at
15:28:56 and ERROR at 16:24:16. CPU was the frozen primary from its earlier
readiness/progress before held scores. The unknown exact T4 session ID prevented
safe cancellation, so it later consumed bounded duplicate GPU time. No winner
was selected from accuracy. Both jobs have now terminated; no paid scaling.

All 1,393 CPU/GPU native phone sequences and start/end frame intervals match
exactly, as do availability decisions for all 5,198 word rows and support counts.
Source/PCM/speaker/label identities also agree. This verifies the observed failure
is shared across devices; it does not establish feature-value equality, grading
accuracy, checkpoint portability or qualification.

CPU packet `/tmp/qari-conformer-training-20261009/local-vowel-cpu-full-20261020/`;
version 2 launcher SHA256:
`0c87542b44fa28513b598d96975faa352202939e2436a5290b27d828008d7cc8`.
Provider source was pulled and verified byte-for-byte, private with GPU disabled.
The first CPU attempt rejected a false assumption that scratch `/kaggle/temp`
already existed. A separate actual private diagnostic verified working/input
present and temp absent; regression tests reproduced the false rejection and
`f784df1` permits scratch creation after context validation.

Full CPU mode requires explicit `kaggle_cpu`, Linux/x86_64, existing Kaggle
working/input directories (scratch temp is created after validation) and working output. Checks precede launcher
unpack/install and direct extraction writes/downloads; ordinary CPU remains
limited to 64 words and three epochs. CPU tensors and execution scope are
reported separately. CPU disk/RSS/deadline checks use no CUDA memory APIs.
Bounds are sampled fail-fast checks, not an OS-level memory ceiling.
The fresh review and RED-to-GREEN boundary tests passed; no live model/UI changed.

Choose the primary run from scheduler/native progress before held scores. Prefer
T4 if it starts before CPU readiness; cancel a superseded run only with its exact
verified session ID. The official status/source responses currently expose no
session ID, so do not guess from the kernel ID or version number. This limitation
may leave a queued backup to observe; never pick a winner from held accuracy.

Execution has terminated without a head. Learned word-wise held misses/false
alarms and checkpoint portability are unavailable, not passing. All outputs remain unqualified; Ikhlas-only skewed human labels
cannot establish a general pronunciation or tajweed grader.

## Completed bounded follow-up: invariant endpoints

Commit `82290f3` freezes a separate explicit `stable_endpoints_v1` assessment
policy. Training-only diagnosis found four excluded error words whose first/last
consonants have globally invariant consuming pairs, while internal consonants
are forced deletions. The fallback requires contiguous surviving native anchors,
at least two exact pairs and the unchanged .55 confidence/frame/speech bounds.
It preserves original references and actual native IDs and records deleted
reference consonant indices; it never supplies lexical correctness or cursor evidence.

All old exact/substitution defaults remain unchanged. Independent executor replay
verified 9,600 legacy calls and 198 exhaustive optimal-path fallback cases. Actual
training-only native paths gain four error crops and one correct crop, losing no
old acceptance (train 1,560 correct / 95 errors). This is localization coverage,
not pronunciation accuracy. Seven initial RED unit tests and two RED integration
tests are GREEN; full recitation/ML/API suite **1,114 passed, 1 skipped, 2 existing
warnings in 63.29 s**. A fresh reviewer found no Critical/Important issue and independently checked
15,996 legacy calls, 1,928 preserved accepted words and 260 all-optimal fallback
words including multiword partitions. One nonblocking regression-coverage
suggestion is deferred: keep the external exhaustive fallback oracle in the repo. No new held phone sequences are used to design
the rule, and no new full model job has been submitted.

The single all-role preflight froze commit `82290f3` before reading the outcome:
train 1,560 correct / 95 errors, validation 220 / 9, test 200 / 8, reserved 143 / 21;
all 5,198 rows retained and zero previous accepted crops lost. The unchanged
support floors now pass. This is eligibility only, not learned accuracy.

A single private T4 full run was submitted and its provider source verified:
`telethonfool/qari-local-vowel-endpoints-20261020`, version 1, launcher SHA256
`06e77326761ae18ee840d098a82d6e89c962c64766882656a87b2d22c40202f7`.
Packet/logs `/tmp/qari-conformer-training-20261009/local-vowel-endpoints-20261020/`.
Same 1,393 sources, roles, original weights, head, seed, loss, guards, floors,
validation-only selection and 7,100/7,200-second limits. No duplicate CPU job.
Native readiness, epochs and held per-word evaluation are still pending.
Broader gated human labels remain 403 in an authenticated check at20:26UTC;
no access-sharing consent was submitted for the user.

## Actual full result: completed, rejected for production

Version 1 terminated COMPLETE at 20:34 UTC after eight finite-loss epochs,
with validation selecting epoch 2 and threshold 0.7165434956550598. Original
teacher/model hashes were preserved. Candidate head SHA256:
`ef2dccf5303e2334095280dc015b98bb5f760b78fc5e9854f0be58a01d4e233a`.

| Held split | Detected / known errors | Assessed missed | Unassessed errors | False alarms / correct |
| --- | ---: | ---: | ---: | ---: |
| Test | 5 / 11 | 3 | 3 | 2 / 216 |
| Reserved speakers | 10 / 22 | 11 | 1 | 0 / 148 |

Both held recalls are 45.45%, below the 90% release requirement. Test precision
is 71.43% and coverage 91.63%, also below the 98% / 95% requirements. Only one
surah and 33 held error words were available; gemination/consonant coverage and
upstream overlap verification are absent. Unknown rows are not negatives and
unassessed errors remain in denominators.

All 15 held detections were `kufuwan`. Reserved `qul` errors were 0/4 detected,
`as-samad` 0/1 and `yalid` 0/1. Test `yakun` was 0/1. `Kufuwan` was 10/16 on
reserved and 5/10 on test, with two false alarms on test correct `kufuwan` words.
Thus improved localization did not solve general vowel-error detection. The
heavy training concentration on `kufuwan` and lack of other-word error examples
remain material limitations; do not tune a new threshold against these results.

The exact head and 32 exported public reserved-word feature arrays were checked
on the original ARM CPU in a networkless 1,200 MiB / 0.5 CPU container. Weight,
feature and encoder identities matched. Maximum CPU/GPU score difference was
8.3819e-9, with zero threshold-decision disagreements. This rules out a large
checkpoint-port regression on that subset, not an encoder/streaming accuracy
claim. A first output attempt used the wrong container UID and could not write
the result; the corrected UID 1002 run passed. No numerical exception or OOM.

Small result files are in the endpoint packet's `output-v1/`, including
`held-word-breakdown.json`. Durable decision:
`/home/innocent/qari-training-artifacts/phonetic-evidence-20261020/endpoint-experiment-decision.json`.
No new model was deployed; production remains healthy and unchanged. All current
PR39 backend/Flutter/native CI checks passed on the research branch.

## Next data source: access granted by the user

The user personally reviewed/approved HF access. Authenticated Iqra Extra access
changed to HTTP 200 at20:38UTC. Pin `IqraEval/Iqra_Extra_IS26` revision
`4e996ef87c6d1da517a4f21bca91e0d577dd8c82`: 1,330 upstream TRAIN rows with
`id`, audio16k, `sentence`, `phoneme_ref`, `phoneme_mis`; parquet208,493,997bytes,
SHA256 `9b0fed74472edd02c1f787839e51a7523df9fd32df7e98c9857d8cc30366b84c`.
No new token or third-party consent was submitted by the agent. Metadata/ID,
speaker-group and target audit is underway before a frozen training recipe.
Actual realized-phone targets must remain distinct from canonical phones;
legal waqf and phonetic conventions must not automatically become Quran errors.
Keep test ground truth/user recordings held out and research private; dataset
license metadata is currently empty. This is new data access, not model success.
