# Six excluded vowel substitutions: native evidence and guard audit

The focused source-only diagnostic found no additional uniquely mapped canonical
vowel retention among the six excluded strict-CVC substitutions. Five native
outputs contain the actual heard vowel; one target alignment is ambiguous. This
does not repair the pronunciation false acceptance seen on the separate expert
cohort, and does not justify relaxing guards.

## Frozen scope

The original Extra train/validation reference audit identifies74/4 strict
consonant/short-vowel/consonant quality substitutions. The raw-vowel training crop
manifest admits70/2 and excludes4/2. Before inference the new probe fixes exactly
those six excluded positions and their six original source recordings.

Only actual-heard labels and frozen source/hash metadata are embedded remotely;
canonical references stay on the VPS for diagnostic classification. TestGT and
user recordings are not used. No fitting, threshold selection, guard relaxation
or model change occurs. The original CROTTC revision, code, weights, decoding,
confidence .55, RMS .006, frame geometry and crop module remain unchanged.

Private T4 kernel `telethonfool/qari-native-guard-attrition-20261021` v1 completed
with540-second launcher and600-second explicitly requested provider limits,
12GiB RSS,4GiB disk reserve and2GiB GPU reserve. Provider privacy and sole existing
Extra dataset input were verified. Provider-pulled source is byte-identical to
the reviewed launcher despite the provider changing its filename.

## Independently verified result

Execution took105.16 seconds, peak RSS4,210,540KiB (about4.02GiB), without runtime
failure or OOM. Native file-helper acoustic-token parity and unchanged teacher
hashes passed. Host audit verifies source IDs/PCM hashes, vocabulary, finite
confidences, emission/frame geometry, protocol/module/cohort hashes, resource
limits and recomputed crop membership. Every previously admitted crop from these
six sources exactly matches the earlier raw-vowel run's evidence.

| First exclusion in stated diagnostic priority | Train | Validation |
| --- | ---: | ---: |
| Native anchor alignment lacks unique adjacent mapping | 2 | 0 |
| Native triplet spans more than50frames (one second) | 1 | 2 |
| Target has multiple optimal alignment mappings | 1 | 0 |

The audit retains all optimal target/anchor mapping options, full native emission
sequences, confidences, frame ranges and reasons at assessable stages. The feature
boundary rule is included; all seven candidate centers have valid seven-frame
features, including both ambiguous candidates. Padding explains no exclusion. These are
diagnostic-priority reasons derived from evidence, not instrumented branch logs.

The five uniquely mapped targets already match actual heard vowel quality.
The sixth remains unassessed: both candidate positions contain heard /u/,
versus reference /a/, but index/timing is ambiguous. It must not be relabelled
a uniquely assessed target or counted as a detected canonicalization. Strict-CVC crop attrition therefore does not hide
additional uniquely mapped canonicalized training targets in this fixed sample.
Canonicalization support admitted by the earlier head remains one training
target and zero validation targets.

This rules out the narrow proposal that admitting these six crops would supply
the missing demonstrated canonicalization examples. It does not establish exact
acoustic vowel boundaries or explain every failure of the raw-spectral head.
Raw-vowel validation remains failed, and expert false accepts remain unresolved.

## Preserved state and artifacts

Production stays at `0c7562b0ee35cee33f9e1884ac5f8e9a6974a37d`. No backend,
UI, APK, model, confidence/speech guard or cursor behavior changed. Both new
research runs are terminal; none remains running.

Packet: `/home/innocent/qari-training-artifacts/native-guard-attrition-20261021/`.
Evidence includes `protocol.json`, `cohort.json`, `sourcepack.json`,
`provider-verified-v1.json`, `runtime-v1.log`, `output-v1/guard-attrition-output/`,
`audit_output.py` and `guard-attrition-audit.json`. Original source reference
audit is `raw-vowel-quality-20261021/diagnostic-reference-audit.json`.
Labels, source audio and credentials remain outside Git.
