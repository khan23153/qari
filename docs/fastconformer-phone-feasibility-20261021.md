# Frozen FastConformer phoneme-head feasibility

Status at 21 October 2026, 17:35 UTC: extraction verified; the completed primary CPU experiment fails its fixed validation gate. All remote runs are terminal. This is an offline research probe. No production model, backend, UI or APK changed, and pronunciation remains unqualified.

The preceding WavLM vowel veto recovered only six of 15 known native misses and introduced 16 correct-vowel false alarms in a reused post-hoc diagnostic. This experiment asks a different question: can Qari's existing, much smaller acoustic encoder support actual-heard phoneme recognition without its RNNT word-prediction network? No expected text, canonical reference, user recording or expert evaluation label is supplied during fitting.

## Exact native extraction

The unchanged deployed encoder is `encoder.int8.onnx`, 172,433,955 bytes, SHA256 `583d152c5bfd7dbfaa573319043fed4f1ef448add3f769d31b3dddf31e4e533f`. Its output is 512-dimensional at an 80 ms stride. The deployed image is `sha256:1c93eb3220a3dd980d3d7269e9eb6fcc9fa9731c0bb260dc0b54c420c7e58d57`.

Checking Python's ONNX Runtime version was insufficient: the production image contains Python ORT 1.17.1, while Sherpa 1.13.8 embeds ORT 1.28.2. Source inspection pins Sherpa commit `11afbd009a7f8c08f4bcf2fc1b265d0df4670fbf` and KNF 1.22.3.

| Probe | Result |
| --- | --- |
| Explicit Python fbank and ORT 1.17.1 | Native token IDs match on the three fixed training fixtures, but some frames differ and maximum selected log-probability difference is 0.619. Fails the frozen 1e-4 bound. |
| Same approximate fbank with Sherpa's exact ORT 1.28.2 | Still fails; one fixture has different token IDs. Runtime version alone does not explain the discrepancy. |
| Observe actual native encoder input through the public ORT API 28 `Run` call | Feature differences from the Python reproduction are small: maximum 5.72e-6, 2.01e-4 and 5.72e-6 across the three fixtures. Their exact numerical source is not isolated. |
| Replay those exact native inputs with the same native runtime | Encoder outputs are identical, all three native token/frame sequences match, and maximum log-probability difference is 7.54e-6. Passes the frozen bound. |

The fixtures are first, median and last **training** sources in the original manifest order; their selection does not depend on recognition outcomes. Failed approximate-front-end results remain recorded. Their tolerances were not widened.

Further isolation reproduced the native Eigen 5.0.1 normalization exactly. All three native feature hashes and encoder-output hashes now match using the independently constructed KNF/Eigen frontend with the same ORT 1.28.2. All three speech fixtures plus silence pass token/frame/probability parity. With those exact same features, Python ORT 1.17.1 still fails, so both normalization arithmetic and runtime identity matter. This establishes frontend identity on the fixed fixtures, not recognition accuracy or broad numerical qualification.

The recorder is a throwaway read-only C-API observer in a separate container. It validates float32/rank/dimensions, creates exclusive fresh files, checks full writes and closes, and terminates on a capture failure. A pre-existing-file negative control exits 86 as required. Review identified the original stale-file risk before fitting; that extraction was stopped and discarded, then restarted with unique attempt directories. No private C++ object layout or production process was modified.

The clean 589-source cache finished in **218.56 seconds**, peak **848,488 KiB RSS**, under a 2 GiB/no-swap/0.75-CPU/no-network container limit with read-only model and source mounts. The host audit verifies every original role, PCM identity, feature array hash, dimensions and source/model/instrumentation pin. Cache SHA256 is `b5f7949a4f86b68beb4acf4f6ec584ec94f619e6c891e6e6b36f442eb5915c3d`.

## Frozen training contract

- Original Extra split: 563 training and 26 validation sources. No 50-source test, quarantine, user audio, TestGT labels or canonical target fallback.
- Targets are full actual-heard `phoneme_mis` sequences using the existing 71-ID phonetic alphabet. Case, long vowels and geminates remain distinct.
- A 512→256→142 MLP gives two ordered 71-way CTC slots per native encoder state. Sixteen training targets do not fit native 80 ms CTC lengths; all 589 fit two slots. This adds output capacity, **not independently observed 40 ms acoustic information or qualified timestamps**.
- Seed 42, ReLU, dropout 0.1, AdamW learning rate 0.001 and weight decay 0.001, batch 16, gradient norm limit 5, maximum 60 epochs, patience 10. Select minimum validation PER, then CTC loss, keeping the first exact tie. Normalization uses training frames only.
- Unprompted frame argmax and ordinary CTC collapse. Blank-separated repeated phones survive. No reference-conditioned beam, lexicon, hotword or rewrite.
- Fixed gate: full-phone validation PER ≤0.15 and each short-vowel-family recall ≥0.80. Family collapse applies only to diagnostic scoring; exact PER preserves all symbols. Deterministic edit-path scoring is not a unique-localization guarantee.
- Validation contains one `ZZ` phone with no training support. It stays in the full **927-phone** denominator. No examples are dropped or resplit to obtain a pass.

Five behavioral helper tests went RED→GREEN. Independent review found no Critical or Important training blocker. A separate NumPy verifier, frozen before output retrieval, replayed all 589 predictions, training-only statistics, selected epoch and fixed probability fixtures. Passing the source gate would permit only another **reused exploratory** expert diagnostic; it would not permit deployment.

## Execution and artifacts

Private input: `telethonfool/qari-pcd-native-features-private-20261021`. Private T4 kernel: `telethonfool/qari-pcd-phone-head-20261021` v1, 900-second launcher alarm and explicit 960-second provider limit. Provider-pulled source is byte-identical, privacy and sole intended input verified. The queued log-stream endpoint returned HTTP 500; the failed stream is archived. After approximately 20 minutes queued, a deliberate private **remote CPU** fallback was declared primary **before any fitting output**, rather than selecting whichever device later produced better metrics. Data, architecture, optimization, stopping/selection and gates remained fixed. CPU/GPU dropout RNG streams differ; identical training trajectories are not claimed.

Both initial GPU v1 and CPU v1 stopped at their first CTC call. The script had supplied targets and input lengths in the wrong positional order to `nn.CTCLoss`. This implementation bug was missed by the initial helper tests and review; it is neither a model accuracy result nor an OOM. Neither initial run produced a gradient update, epoch or learned checkpoint. Original sources and structured failures are preserved.

CPU v2 uses a shared keyword-bound CTC objective in fitting and evaluation. Two actual Torch regressions first reproduced the failure, then passed against exhaustive path probabilities, zero gradients on padded frames and an infinite loss for impossible repeated targets. All seven local research tests pass. The launcher also ran the two real CTC tests on the remote Torch runtime **before fitting** and exported their result. Independent repair review passed. The private kernel is `telethonfool/qari-pcd-phone-head-cpu-20261021`, accepted version 2; source/privacy/CPU/sole-input identity verified. The live log stream was followed through completion.

## Primary result: rejected

CPU v2 completed 40 epochs, selecting epoch 30 under the original rule, in **92.66 seconds** with peak **529,916 KiB RSS**. The head has 167,822 parameters; the encoder stayed frozen. Runtime: Torch 2.11.0+cpu, NumPy 2.2.6, two threads.

| Measure | Verified result | Fixed gate |
| --- | --- | --- |
| Training phone error | 408 / 23,689 = 1.72% | Diagnostic only |
| Validation phone error | 216 / 927 = 23.30% | ≤15%; **fails** |
| Validation /a/ family recall | 152 / 196 = 77.55% | ≥80%; **fails** |
| Validation /i/ family recall | 54 / 73 = 73.97% | ≥80%; **fails** |
| Validation /u/ family recall | 31 / 49 = 63.27% | ≥80%; **fails** |

The independent NumPy host replay verifies all 589 source prediction-ID sequences, all metrics, exact training-only normalization statistics, selected history entry, checkpoint/input hashes and the three fixed probability fixtures. Maximum probability difference is **1.46e-6**, below the unchanged 2e-5 bound. Replay took 7.19 seconds, peak 258,172 KiB RSS. The single validation `ZZ` without training support remains in the denominator.

The fixed gate fails. **No expert TestGT evaluation is run for this head, no threshold/hyperparameter retuning follows and no model is promoted.** The large train/validation gap establishes poor generalization for this head and split; it does not isolate whether supervision coverage, frozen representation or temporal geometry dominates. Successful source fitting and exact deployment-frontend reproduction do not establish a pronunciation fix.

Extraction/GPU packet: `/home/innocent/qari-training-artifacts/fastconformer-phonetic-feasibility-20261021/`. Important files include `protocol.json`, `sourcepack.json`, `native-cache-audit.json`, `native-encoder-cache-manifest.json`, `frontend-parity-*-result.json`, `runtime-investigation.json` and `eigen-normalization-audit.json`.

Primary CPU packet: `/home/innocent/qari-training-artifacts/fastconformer-phonetic-cpu-20261021/`, including `pre-fit-CPU-fallback-decision.json`, `archive-v1/`, `output-v1/failure.json`, `ctc-order-repair-record.json`, `provider-verified-v2.json`, `runtime-v2.log`, `output-v2/ctc-preflight.json`, `output-v2/phone-head-output/`, `verify_head_output.py`, `host-verifier-pre-output-pin-v2.json` and `CPU-head-verified.json`. The host verifier's output path was repinned from v1 to v2 before retrieval; its numerical checks were unchanged. Captures, data, checkpoints and case predictions remain private on the VPS/provider; they are not committed.

## Separate configuration question

A bounded 1 MiB HTTP 206 read fetched a prefix of the original NVIDIA `.nemo` archive; only its configuration was extracted. No complete model-weight file was downloaded, extracted or loaded. Revision `2221b640a2d03bfd540d28ab92b20d3cd9bc0d35`, configuration SHA256 `c67180984ad0da0267e1f051794c05b407418fdadfed77826cfacc2409d2015b`, declares NeMo 2.0.0rc1 and a Hann window; the current Sherpa path uses its Povey default.

A separate frozen Hann-only probe decoded the complete original Ad-Duha, different-speaker Ad-Duha and newer Ikhlas recordings with exact native normalization/runtime and unchanged decoding/scoring. The decoded word sequences are identical between windows on all three recordings. Original Ad-Duha still decodes `فآبي` instead of `فآوى` and `تقهر` instead of `تنهر`; Hann alone does not repair these cases. Some scores cross .55 in each direction, which is not evidence of improved correctness. Ikhlas retains all 19 words including basmalah in both decodes. These whole-clip probes do not reproduce the production streaming windows and cannot establish live 40/40 or cursor safety.

The six decodes finished in 34.66 seconds, with peak 1,529,236 KiB RSS close to the 1,536 MiB container limit. There was no OOM, but full Ya-Sin or longer clips must not be run through this whole-clip path; subsequent work must use bounded streaming windows. `window-probe-protocol.json`, `window-probe-output.json` and `window-probe-audit.json` retain audio hashes and all native evidence. The Hann difference is not a proven production cause, and no frontend change is deployed or mixed into the frozen-head experiment.

## Next data prerequisite

The [L2-KSU paper](https://doi.org/10.1007/s10791-024-09489-8) describes human native/non-native pronunciation data. Its old GitHub link is unavailable; the [publisher's HF card](https://huggingface.co/datasets/IWAN/L2-KSU-Dataset) lists 4,094 WAV files, phone-level TextGrids and 818 actual-versus-canonical annotation rows. Revision `ca2331a38af06e3348feb3ffd2376953cdc10ce5` is pinned for an audit, not yet used. Authenticated access still returns 403 at 17:34 UTC. The user has been asked to review this **new** repository's account-sharing conditions; the agent accepted nothing and no new token is requested.

The card says its original train/test CSV files were identical and supplies no official split. Before any fitting, audit actual label semantics, speaker/content identities, duplicate audio, existing evaluation overlap, allowed use and split provenance. No archive/annotation CSV has been downloaded and no improvement is promised. The previously approved Iqra datasets remain accessible. The pronunciation goal remains open.
