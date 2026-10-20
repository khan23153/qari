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

Complete recitation/ML/API suite: **1,069 passed, 1 skipped, 2 existing warnings**,
58.14 seconds. Fresh whole-branch review found one important defect: executor
cleanup could wait for unchecked trickling downloads after the job deadline.
Regression tests reproduced it; per-read checks, remaining-time socket bounds
and bounded backoff fixed it. A real alarm/thread-pool cleanup test passes too.
One in-flight socket read can still take at most 25 seconds; the provider's
100-second shutdown reserve covers that bounded cleanup.

Actual private T4 job: `telethonfool/qari-local-vowel-20261020`, version 1,
accepted 2026-10-20 09:56 UTC. Provider source was pulled and verified byte for
byte; private/T4 metadata verified. Initial uncompressed 2.03 MB submission
returned HTTP 400 with no kernel created; the identical extracted sources were
compressed to 427,716 bytes and accepted. No exact provider size limit is claimed.

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

Actual extraction, eligibility, training, held detection/false-alarm results and
CPU portability remain pending. The experiment always reports `qualified=false`
and `production_changed=false`. One-surah contributor labels, unknown upstream
training overlap and a full-context encoder cannot establish independent
multi-surah or live-stream reliability. Restricted Iqra datasets still need the
user to review account-information sharing conditions; no consent was submitted
on their behalf. Preserve all live confidence/speech guards and existing Hifz/UI.
