# Raw-spectral vowel-quality spike: validation failed

The independent raw-audio vowel head did not meet its frozen validation gate.
It is rejected for production. No expert TestGT evaluation was run for this head,
and no backend, model, APK, UI or recognition guard changed.

## Question and fixed procedure

The earlier native CROTTC diagnostic retained canonical vowels at 15 of 168
expert-labelled wrong-vowel targets, all expected /a/ versus heard /u/, despite
native confidences .7456–.9949. This spike asks whether a separate classifier
using raw spectral audio features can recover heard vowel quality without
relying on canonical-word output.

Only the original Extra split is used: 563 training and 26 validation recordings,
with actual heard `phoneme_mis` targets. No TestGT, user test recordings,
quarantined rows or canonical reference labels supervise the head. All source
IDs, roles, encoded/PCM hashes and sample metadata remain frozen.

The pinned, unchanged CROTTC model supplies approximate vowel emission timing.
Eligible crops require a consonant/short-vowel/consonant triplet, unique agreement
across all optimal edit alignments, matching consonants, native confidence at
least .55, valid frame geometry and speech RMS at least .006. Ambiguous or missing
phones are unassessed. Emission centers are approximate acoustic timing; their
accuracy has not been independently established.

Features are seven 10ms-spaced frames of 40-bin log-mel spectra from original
16kHz PCM: 400-sample symmetric Hann window, 512-point FFT, HTK filters50–7600Hz,
RMS normalization .1 and no utterance CMVN. Feature mean/std come from training
only. A 280→64→3 head predicts a/i/u, combining upper/lower-case allophones only
inside this quality head. Native phones remain unchanged; this does not grade
duration, shadda or all tajweed.

Before submission the protocol fixes seed42, AdamW lr.001, dropout.1, maximum20
epochs, validation-loss selection and five-epoch patience. Support floors are
64 training and16 validation crops per class. A later fixed expert diagnostic is
permitted only after validation accuracy≥.90 and every class recall≥.75. Those
limits were neither lowered nor replaced after seeing results.

## Execution and verification

Private T4 kernel `telethonfool/qari-raw-vowel-quality-20261021` v1 completed.
Provider-pulled code matches the reviewed launcher byte for byte, with private
metadata and only the existing private Extra input dataset. Launcher/provider
limits are1,800/1,860 seconds,12GiB RSS,4GiB disk reserve and2GiB GPU reserve.
All heavy inference/training ran remotely; no teacher weights loaded on the VPS.

The run finished in155.66 seconds, peak RSS4,211,196KiB (about4.02GiB), without
an OOM or runtime failure. The teacher was frozen and its original checkpoint
hashes remained unchanged. Native file-helper acoustic-token parity passed.

Ten functional tests passed; the independent reviewer also checked961 exhaustive
small alignment pairs. Host CPU output audit verified source/crop labels,
protocol/cohort/module/checkpoint identities and gate arithmetic. Recomputing an
original training WAV's feature fixture on ARM had maximum difference0; exported
NumPy probabilities differed from GPU Torch by at most1.79e-7.

A further read-only CPU replay verified original PCM hashes for all589 sources
and exact feature hashes for all7,689 crops. It reproduced the full validation
confusion matrix without training, changing thresholds or using TestGT. This
replay took9.49 seconds with387,488KiB peak RSS in the bounded CLI container.

## Actual results

| Heard quality | Training crops | Validation crops | Validation recall |
| --- | ---: | ---: | ---: |
| a/A | 4,692 | 171 | 149/171 =87.13% |
| i/I | 1,541 | 63 | 53/63 =84.13% |
| u/U | 1,181 | 41 | 28/41 =68.29% |

Training stopped after9 epochs; minimum validation loss selected epoch4.
Selected training accuracy was81.63%; validation was230/275 =83.64%.
Both required validation accuracy and minimum class recall failed.

The unchanged native model already agrees with every selected validation crop's
heard quality (275/275). Native/heard quality discrepancies exist in just eight
selected training crops and zero validation crops. On those eight training
crops, the raw head predicts the heard quality three times and retains the native
output quality five times. “Native” does not mean “canonical”: a read-only
all-optimal alignment to the original source reference finds only one of these
eight positions canonicalized; the other seven are native errors away from an
already-correct reference vowel. Training examples are not independent effectiveness
evidence.

At the predeclared, uncalibrated .95 class-softmax cutoff, wrong-quality
predictions number54/7,414 training crops and0/275 validation crops. The latter
does not establish zero false alarms or error detection: these are selected,
correlated crops with no native/heard disagreement examples in validation.
No confidence calibration, streaming cursor test or teacher judgement is implied.

A broader source-only all-optimal-path audit identifies85 training and4 validation
unique heard/reference short-vowel-family substitutions (a different definition
from the earlier narrower74/4 audit). Current crops admit70/2, including just one
native canonical retention in training and none in validation. Fifteen training
and two validation substitution targets are unassessed by this crop policy.
Reference labels are inspected for this diagnostic only; they never train or
select the head. The next question is which native-emission or guard condition
excludes relevant targets, with no guard relaxation. The narrower strict-CVC
subset has74train/4val positions,70/2 admitted and4/2 excluded; the focused
no-training diagnostic uses those six exclusions. The other11 broad exclusions
are outside the strict exact-CVC pattern by construction.

## What remains unresolved

The complete source/feature replay rules out a CPU export mismatch as the
explanation for this candidate's failure. It does not identify whether approximate
CTC crop timing, inadequate spectral representation or limited speaker/contrast
coverage is the dominant cause. Do not claim timing is proven wrong, silently
shift crops or tune on TestGT. The original pronunciation false acceptance remains
unfixed. A new training run needs a specific diagnostic hypothesis rather than
another blind threshold/model change.

The existing expert probe and this spike are terminal; neither leaves a running
remote job. Production remains commit
`0c7562b0ee35cee33f9e1884ac5f8e9a6974a37d`. The research checkpoint is393,171 bytes
and remains an unqualified throwaway artifact outside Git.

Durable packet: `/home/innocent/qari-training-artifacts/raw-vowel-quality-20261021/`.
Relevant files: `protocol.json`, `training-cohort.json`, `sourcepack.json`,
`provider-verified-v1.json`, `runtime-v1.log`, `output-v1/raw-vowel-output/`,
`CPU-output-verified.json`, `crop-quality-coverage.json`, `source-replay-result.json`,
`verify_output.py` and `replay_training_crops.py`. Source data, gated labels and
credentials are not committed.
