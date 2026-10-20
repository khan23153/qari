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

Latest complete recitation/ML/API suite: **1,105 passed, 1 skipped, 2 existing warnings**,
58.76 seconds. Fresh whole-branch review found one important defect: executor
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

At 2026-10-20 15:21 UTC, the explicit full remote CPU fallback
`telethonfool/qari-local-vowel-cpu-full-20261020` version 1 was source-verified,
private with GPU disabled, and RUNNING. Launcher SHA256:
`465c95a9fd86e6d0085e0b4f38d2031b8fe38282916b8b9c7d4332478f52437c`.
The attempt then ERRORed before unpack/model downloads: the preflight assumed all
Kaggle scratch directories already existed. The preceding smoke had created those
directories before checking, so it did not validate fresh-container layout. A
separate tiny private CPU context diagnostic verified Linux/x86_64, existing
working/input and absent scratch temp. The guard now permits creating scratch
only after validating the existing provider context. Regression tests and all
1,105 recitation/ML/API tests pass before the guarded retry. No epochs or learned accuracy exist from CPU v1.

The frozen packet keeps all 1,393 source clips, roles, labels, model/reference pins, numerical
head/training protocol and eligibility floors unchanged. No head or accuracy
result exists at this observation. Packet and logs:
`/tmp/qari-conformer-training-20261009/local-vowel-cpu-full-20261020/`.

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

Completion, word-wise held misses/false alarms and bounded checkpoint portability
remain pending. All outputs remain unqualified; Ikhlas-only skewed human labels
cannot establish a general pronunciation or tajweed grader.
