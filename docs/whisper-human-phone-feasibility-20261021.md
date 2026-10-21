# Frozen Whisper-base human phoneme feasibility — 21 October 2026

**Rejected for deployment.** A distinct actual-heard human-label probe did not meet the predeclared validation gates. This is neither a pronunciation fix nor a new APK/backend release.

## Question and distinction from earlier experiments

Can the existing deployed Whisper-base acoustic encoder support an unprompted full-phone CTC head trained on the original approved human Extra563train/26validation cohort? Earlier Whisper CTC pilots used synthetic Iqra_TTS; the completed PCD experiment used another encoder with80ms states. This probe changes the representation to native Whisper20ms states, without its text decoder. It does not retune the rejected PCD head or train on expert/user recordings.

Production remains revision `0c7562b0ee35cee33f9e1884ac5f8e9a6974a37d`, existing models and confidence/speech/lexical/cursor guards. The broader pronunciation goal is unresolved. Word confidence cannot establish correct harakat, adaegi or tajweed; separate expert evidence already records confident canonical retentions of spoken vowel errors.

## Native extraction and fixed protocol

The existing `/home/innocent/qari/models/qari-ct2-base/model.bin` is76,396,677bytes, SHA256 `b47c0fc7cd202c24ad4c7816e29d06c7d37c3761c1dcc91690796227df01dfa0`. All model/config/tokenizer files were pinned, read only. CTranslate2 4.4.0, faster-whisper1.0.3, int8, CPU one thread, public acoustic `encode` only. No text decoder, expected-text prompt, lexicon, beam or post-decoding reference rewrite.

Native extraction matches the installed first-window path: feature extractor appends a full chunk, subtract its `nb_max_frames` to obtain content frames, slice content and `pad_or_trim` to the chunk length. Preserve the production min15s/max30s/ceil(duration+.5) policy. Keep ceil(content mel frames/2) encoder states. All589 sources1.71–17.97seconds fit a single window with no truncation. States are512D with20ms spacing; bidirectional context means neither qualified phoneme timestamps nor20ms live latency is established.

First/median/last TRAIN fixtures repeat bit-exact, including full-cache replay hashes. Bounded extraction completed all589 sources in525.09seconds, peak962,716KiB RSS, isolated2GiB/no swap/.75CPU/no network; no production process change. Cache audit verifies original roles, PCM/encoded/label identities, every feature hash,143,672train frames, and no CTC-capacity exclusions. Exact encoded/PCM cross-role duplicates are zero; physical speaker identity and broader content independence remain unverified.

The unchanged original human cohort is Extra revision `4e996ef87c6d1da517a4f21bca91e0d577dd8c82`,563train/26validation, actual `phoneme_mis` only. Retain all labels, case, length and geminates. No test/quarantine recovery, resplit, canonical fallback or expert/user fitting. One validation ZZ phone has zero train support and stays in the927-phone denominator. Train audio47.89minutes; validation2.32minutes.

Train-only512D normalization uses float64 accumulation, float32 export, std floor1e-4. Head512→256ReLU/dropout.1→71; one output per native frame, ordinary argmax/CTC collapse. Seed42, AdamWlr.001/wd.001, batch16, gradient norm5, max60epochs, patience10; select minimum validation PER then CTC loss, retaining the first exact tie. Fixed gates: full-phone PER≤15% and each a/i/u family recall≥80%. Exact PER preserves every symbol; the family metric only groups a/A, i/I, u/U during deterministic edit-alignment scoring.

This validation split has already been reused across research hypotheses. Passing its gates would only permit the already-inspected expert278 diagnostic; it would not provide fresh qualification or permission to deploy. There was no result-dependent architecture, split, threshold or gate change.

## Verified completed result

| Measure | Actual result | Fixed requirement |
| --- | --- | --- |
| Training phone errors |1,858/23,689 =7.84% | Diagnostic |
| Validation phone errors |270/927 =29.13% |≤15% — fail |
| Validation a-family recall |160/196 =81.63% |≥80% — pass |
| Validation i-family recall |54/73 =73.97% |≥80% — fail |
| Validation u-family recall |35/49 =71.43% |≥80% — fail |
| Selected epoch / stopped epoch |29/39 | Original patience10 |
| Head parameters |149,575 | Encoder frozen |

Private free CPU kernel `telethonfool/qari-whisper-human-head-20261021` v1 is COMPLETE. Source byteidentity, private flag, CPU and sole intended input were verified from provider-pulled metadata/source. It ran197.55seconds, peak1,401,828KiB RSS, Torch2.11.0+cpu/NumPy2.2.6, two threads; explicit960s provider and900s launcher limits. All8 real CTC/frame tests ran before fitting. The original single-frame output regression was observed red with the inherited phase-two helper, then green after using one native frame; existing exhaustive CTC probability/padded-gradient/infinite-loss checks remain intact.

Independent NumPy CPU replay verifies all589 prediction ID sequences and metrics, exact train-only statistics, checkpoint/source/cache/protocol hashes, selected epoch and probability fixtures. Maximum probability difference1.37e-6 is below the predeclared2e-5 bound. Replay10.76seconds, peak903,116KiB RSS, isolated3GiB/no swap/.75CPU/no network, no encoder or teacher loaded. No OOM occurred.

Independent standard-library recount also matches all589 exported sequences: validation errors comprise117deletions,125substitutions and28insertions.

The train/validation gap establishes poor generalization for this head and split. It does not isolate whether data coverage, frozen representation, temporal modeling or another factor dominates. Finer encoder state spacing alone did not solve the problem. No expert evaluation, parameter sweep, model promotion or deployment follows the failed gate.

## Execution records and remaining work

Packaging protected-hardlink permission failed on the root-owned cache. A shell continued to submit README-only private inputv1; no head run used it. Full copies were hash-verified and complete inputv2 was uploaded/listed before the first and only kernel fit. Source/CTC/training did not fail or restart. Initial host python-alias/pin-file setup failures also occurred before extraction. Preserve these records rather than presenting every setup step as successful.

Latest authenticated check for new `IWAN/L2-KSU-Dataset`, pinned revision `ca2331a38af06e3348feb3ffd2376953cdc10ce5`, remains403 at21:26UTC. The agent accepted no conditions and downloaded no new data. The pending user self-review applies to this new repository, independently of already-approved Iqra access. If access becomes available, audit source/actual-label semantics, speaker/content identity, duplicates, permitted use and split before fitting: the card says the original train/test CSVs were identical. More source data alone would not establish a production fix. Broader independent human mistake/correct validation and live timing/WebSocket/negative controls remain necessary.

Packet: `/home/innocent/qari-training-artifacts/whisper-heard-phone-feasibility-20261021/`.

- `native-model-pins.json`, `probe_encoder.py`, `encoder-probe-result.json`, `extract_encoder.py`.
- `native-encoder-features.npz`, `native-encoder-cache-manifest.json`, `native-cache-audit.json`.
- `protocol-design-before-fit.json`, sealed `protocol.json`, `pre-fit-seal.json`, `sourcepack.json`, research tests, training/replay sources.
- `runtime-v1.log`, `provider-verified-v1.json`, `output-v1/ctc-preflight.json`, `output-v1/phone-head-output/`, `CPU-head-verified.json`, `new-data-access-final.json`.

ProtocolSHA `7559f90eece2042b6a0385313c3775fa35dacbb18ae3b1d44205669d26e57ccc`; cacheSHA `6a0b532366b3e336213b56fa256e91476b50880802ed6f0837ddecccbdb9f122`; headSHA `7e985afc492f7f634ae33ea48e7a5846b978c65e621cf4a9385554c2167f740e`. Research sources/weights/audio remain outside Git. This documentation-only snapshot does not claim a fresh product-suite pass; latest prior unchanged product suite was1,166pass/1skip/one known warning. Hifz confirmed-word behavior, visible ayah markers and mistakes/unreached summary remain requirements.
