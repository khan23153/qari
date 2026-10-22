# Frozen speech features improve source validation, but the veto is rejected

The frozen intermediate-feature head passes its source-validation gate. Its
intended pronunciation-error veto remains unsuitable for deployment: a separate
descriptive reanalysis recovers six native misses but adds false alarms on eleven
of 110 fully correct recordings. Nine original native misses remain.

The expert run's original numerical verification contract **failed**. The
descriptive results below are explicitly post-hoc and reuse previously inspected
expert recordings. They are neither an original-protocol pass nor independent
final qualification. No production model, backend, UI, APK or recognition guard changed.

## Source-only representation experiment

The failed raw-spectral head achieved 230/275 source-validation accuracy. The new
question replaces that representation with a fixed, frozen speech-trained
representation while preserving source IDs, splits, actual-heard supervision,
native timing, crop eligibility and training/validation rules.

A read-only forward hook captures output zero from WavLM `encoder.layers[5]`,
after six completed transformer layers. Three native frames around the same
emission center are averaged into 1,024 features. The teacher and its original
forward method remain unchanged. These transformer states incorporate broader
utterance context; the 400-sample convolution geometry does not describe their
total receptive field. Layer six was fixed before extraction; no layer sweep or
expert-based threshold selection occurred.

The original Extra split remains 563 training and 26 validation recordings, with
7,414/275 eligible crops. Training/validation contain ten/two disjoint ID-prefix
groups. Physical speaker identity is not independently verified. Only one admitted
training crop contains native canonical retention of a real reference-vowel
substitution, and validation contains none. Source validation therefore cannot
qualify the intended added-error veto.

The 1,024→64→3 head reuses seed42, dropout.1, AdamW lr.001, inverse-square-root
training class weights, train-only normalization, validation-loss selection and
five-epoch patience. The original minimum support and accuracy/recall gates stay
fixed. TestGT and user recordings never enter training or checkpoint selection.

| Source validation | Raw spectra | Frozen speech features |
| --- | ---: | ---: |
| Correct vowel qualities | 230/275 (83.64%) | 263/275 (95.64%) |
| a/A recall | 149/171 | 166/171 |
| i/I recall | 53/63 | 59/63 |
| u/U recall | 28/41 | 38/41 |
| Fixed accuracy≥.90 / every recall≥.75 gate | Failed | Passed |

Private kernel `telethonfool/qari-frozen-ssl-vowel-quality-20261021` v1 completed
in185.32 seconds, peak RSS4,211,336KiB (about4.02GiB), selecting epoch2of7.
Kaggle normalized its title to this actual slug; the receipt and provider-pulled
source are retained. An initial queued log-stream HTTP500 was archived; the same
job was monitored after reconnection, without resubmission.

Four functional tests passed. Independent review verified frozen pins, hook
semantics, source/privacy scope and all embedded hashes. Host replay verifies
all7,689 cached feature hashes, original crop identity, labels, role indices,
train-only statistics and the full validation confusion matrix. Mean pooling
matches exactly; exported NumPy/GPU-head probabilities differ at most1.19e-7.
These checks establish cached-head/pooling parity, not full ARM teacher-feature
parity or live latency. The source-only checkpoint is1,439,196 bytes.

## Frozen expert execution and the primary failure

The head is frozen before one diagnostic on the same278 public audio recordings
used in the earlier native probe:168 single internal-vowel errors and110 exact
correct clips. These recordings were previously inspected and informed research;
they must not be advertised as an untouched final test. No expert labels or
reference text reach the remote model. The class-softmax veto threshold remains
the predeclared.95, without calibration or retuning on these results.

Only label-free native consonant/short-vowel/consonant crops are eligible, with
the unchanged.55 native-confidence, .006 speech-RMS, frame/span and boundary
guards. A head disagreement may propose an error. It cannot clear a native error,
confirm a word, move a cursor or complete a page.

Private kernel `telethonfool/qari-ssl-vowel-expert-20261021` v1 completed278 clips,
mono/stereo helper checks and three research controls:283 encoder passes,
413.51 seconds, peak RSS4,287,664KiB (about4.09GiB), without OOM or runtime error.
Limits are900 seconds in the launcher and960 explicitly requested from the
provider, with the existing memory/disk/GPU reserves. Original teacher hashes and
native file-helper parity passed.

Initial submission failed before kernel creation because its1.46MB script
exceeded Kaggle's source limit. Lossless zlib/base85 transport reduced it to806,197
bytes; independent decompression reproduces the exact original checkpoint SHA.
Rejected source and error evidence remain archived. This changed no model or
scoring rule. Provider source identity, private status and sole intended audio
input were checked for the first accepted version.

The primary host audit stops **before expert metric scoring**: six native-phone
confidence differences exceed its frozen2e-5 tolerance, with maximum4.518e-5.
That tolerance was not widened and the original audit was not rewritten to pass.
The cause of the small numerical differences has not been isolated.

## Separate post-hoc descriptive analysis

A new label-free audit, independently reconstructed by the reviewer, finds exact
native IDs and frame boundaries across all278 clips plus controls, no.55 guard
crossings and identical native/pooled eligibility at all2,630 ROIs. Six of8,773
emissions violate only the original confidence-difference criterion.

Before scoring labels, a separate secondary plan and script freeze hashes of the
failed audit, original protocols, both prediction sets and the equivalence proof.
The secondary analysis requires exact native IDs/frames/.55 decisions/ROIs,
preserves the fixed head/.95 rule, retains all168 target outcomes, and separately
counts correct-vowel false alarms, eligibility and unscored proposals. Original
contract failure and post-hoc scope are explicit in its separate output files.

| Descriptive outcome | Count |
| --- | ---: |
| Original native canonical-vowel misses | 15 |
| Added veto with correct heard-vowel diagnosis | 6 |
| Added veto with wrong diagnosis at those15 targets | 0 |
| Original misses without a veto | 9 |
| Added alarms on eligible correct vowels | 16/2,250 |
| Fully correct recordings with an added false alarm | 11/110 |

The16 false alarms comprise11/955 eligible vowels on the110 correct recordings
and5/1,295 other correct vowels on the168 error recordings;16 clips are affected.
The36 total high-confidence disagreements comprise6 recoveries,16 false alarms
and14 proposals outside assessed correct/native-canonical-error targets. Do not
infer a global precision score from the assessed subset.

All168 native target outcomes remain accounted for:109 correct diagnoses,
15 canonical retentions,24 ambiguous and20 wrong deletions before the veto.
Across all168 targets, head outcomes are98 heard,17 canonical and53 unassessed. Ten already-correct native error diagnoses have high-confidence
head outputs in the canonical family. Those native errors were **not cleared**:
the scope explicitly forbids that operation.

Research silence/noise/tone produce8/3/2 native phones and zero eligible head
crops or vetoes. These are offline controls, not live WebSocket/cursor tests or
proof that a phonetic recognizer cannot hallucinate speech.

Independent recount confirms all denominators and all16 false-alarm
classifications. The candidate is rejected for the intended veto use. Raising
the threshold on this inspected cohort, moving held data into training or calling
95.64% source accuracy pronunciation qualification would not repair these
failures.

## Preserved state and remaining work

The remaining problem is reliable human pronunciation assessment across voices,
including avoiding false error reports. Dataset access is resolved. The current
source split lacks admitted native-canonicalization validation examples; broader
independent human error/correct validation is needed before qualification. This
does not justify changing the frozen split, recovering quarantined rows or using
TestGT as training data. Earlier public `Iqra_train` weak-label and native80-model
audits already exist; do not repeat them as new human-error evidence.

Production remains `0c7562b0ee35cee33f9e1884ac5f8e9a6974a37d`, with its existing
models and lexical/confidence/speech/cursor guards. The pronunciation goal stays
open. Both new GPU runs are terminal; no training job remains active.

Durable packets:

- `/home/innocent/qari-training-artifacts/ssl-vowel-quality-20261021/`: frozen
  source protocol, sourcepack, provider proof, logs, checkpoint, compressed pooled
  vectors and `CPU-output-verified.json`.
- `/home/innocent/qari-training-artifacts/ssl-vowel-expert-20261021/`: original
  protocols, provider proof, rejected-source archive, predictions,
  `primary-audit-failure.json`, `native-confidence-divergence.json`,
  `decision-equivalence.json`, frozen `posthoc-plan.json`/`posthoc_reanalysis.py`,
  and separate `posthoc-expert-results.json` plus private case details.

No audio, labels, weights or credentials are committed. These are throwaway
research prototypes, not a retained production subsystem.
