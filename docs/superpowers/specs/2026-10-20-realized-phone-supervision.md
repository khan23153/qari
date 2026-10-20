# Human realized-phone adaptation experiment

## Intent and boundaries

Continue fixing intentional harakat/adaegi false acceptance and low-latency Qari
tracking. Existing deployed lexical models, confidence/speech/cursor guards,
Hifz reveals, ayah markers and summary behavior stay unchanged. This is a new
research stage; the previous word-local head was rejected (15/33 held errors).
User authorizes continuous autonomous work, free compute, private processing and
no VPS OOM. No model release or correctness claim without independent qualification.

## Frozen source facts

User personally approved `IqraEval/Iqra_Extra_IS26`; authenticated access is200.
Revision `4e996ef87c6d1da517a4f21bca91e0d577dd8c82`; parquet208493997bytes,
SHA256 `9b0fed74472edd02c1f787839e51a7523df9fd32df7e98c9857d8cc30366b84c`.
Full file and metadata match verified; all1330files are16k mono WAV, no duplicate
PCM. Preserve .006RMS and .25–30s source guards:1327accepted,2quiet/1duration
excluded. Valid duration1.622125–20.233875s;1.91869hours. Source audit peak398.54MiB.
Private raw source/audits: `/tmp/qari-conformer-training-20261009/iqra-extra-audit-20261020/`.

Authors describe `phoneme_mis` as human REALIZED phones; `phoneme_ref` is expected.
Use only realized phones as acoustic targets. Preserve case, emphatics, long
vowels and doubled consonant TOKENS. Never canonical fallback or expected-text
acoustic input.348rows have identical reference/realized targets;27other rows
are final-short-vowel-only contrasts and may be legitimate waqf. Do not turn every
reference difference into a Quran error label. Native phone PER is not tajweed grading.

## Prospective split frozen before any new model scores

`prospective-split-v1.json` records the exact rule and all1330roles:
- Normalize NFKC Arabic letters/space, hamzated alifs->alif, maqsura->ya, no tatweel.
  Union content groups sharing normalized sentence OR identical canonical phones.
- Sort group representatives by SHA256(`qari-real-phone-v1:content:`+minimum
  normalized sentence). First ceil(.15*N) validation, next same test, rest train.
- Count accepted records per numeric ID prefix before `_`. Prefixes with>=40
  accepted records sorted by SHA256(`qari-real-phone-v1:prefix:`+prefix): first2
  validation, next3 test; all others train. These are COLLECTION groups; physical
  speaker identity remains unverified. Never silently label them verified speakers.
- Keep a source only when its prefix/content roles agree. Retain quarantine and
  source-exclusion rows in the manifest. No group/content/PCM overlap.

Observed136content groups:563train/26validation/50test,688cross-group quarantine,
3source exclusions. Do not resample roles based on scores. Research floors>=200
train/>=20validation/>=20test; all release qualification gates remain unchanged.
TestGT/user recordings stay held out; TestGT still403 and is never training data.

## Model and native target convention

Adapt `MostafaMaroof/wav2vec2-arabic-phoneme-asr`, revision
`0a32c641aaaeec6957e41a794add52e024e46b50`,1262135432-byte safetensors SHA256
`582149e3e913a0fc7f29c116530e0b1b6ae7a7ab23eef4efc3fc2acc760e2b75`.
Its old frozen free decoder missed human errors; new supervision is the experiment.
Reuse pinned metadata under
`/home/innocent/qari-training-artifacts/pronunciation-human-data-20261018/arabic-phone-meta/`.
Strict native weight load, no trust_remote_code. Native24layers/hidden1024,
80classes, blank77, delimiter75; no reindex or reset. All57realized tokens fit.
Insert native delimiter75 BETWEEN phone-token IDs, preserving pretrained target
convention; no BOS/EOS/blank in targets. Native convolution kernels
[10,3,3,3,3,2,2], strides[5,2,2,2,2,2,2]. All639assigned clips are CTC-representable.
Greedy collapse is blank-aware; remove delimiter75 only for phone PER. Preserve
other predicted symbols as errors; no repetition collapse/case folding/canonical repair.

Train ONLY final two native encoder layers22/23 and lm_head. Freeze everything
else and verify frozen-state digest before/after. Call the native
`freeze_feature_encoder()` so its internal `_requires_grad` flag is false too;
otherwise frozen convolution parameters can still force a graph through all
encoder layers and waste GPU memory. Disable gradient checkpointing and verify
the first frozen encoder input requires no gradient in tests. Explicit eager attention for
controlled CPU/GPU comparison. Native spec augment .075, layer-normalized feature
extractor and normalized16k frontend preserved. FP32 forward/backward/optimizer;
CTC mean reduction, zero_infinity=false, finite loss/gradient/parameter checks.
AdamW lr1e-5,weight_decay.01,betas(.9,.999),eps1e-8,clipnorm1,seed42.
Effective batch16 via microbatch2, weighting partial groups by actual sample count.
Max20epochs; best validation aggregate phone PER; patience4,min3epochs.
Baseline validation/test and final test reported without test-based selection.
Validation CTCloss can exclude unrepresentable targets; PER retains all accepted
assigned clips. No inference expected phones or target text.

Save delta ONLY (exact allowed state keys) plus immutable base/frontend/vocab/
data/split identities, history and predictions. Never overwrite original model.
Safe delta loader requires exact allowed keys/shapes/base identity and finite tensors.

## Execution, privacy and success evidence

Work in the existing isolated worktree on a separate research branch. Gated
source remains private; upload to own PRIVATE Kaggle input only with original
conditions/other license, never CC0 or public redistribution. Verify provider
privacy and source byte identity before any job. No credentials in packets/logs/git;
HF token stays on VPS, passed privately via stdin only for approved download.
Remote full run CUDA only,7100s whole/7200s provider; RSS12GiB,disk4GiB,GPU2GiB
sampled checks. Context check before unpack/pip/download; source/temp creation only
after checking existing Kaggle working/input. No automatic CPU full training.
Local engine fixtures<=32rows/2epochs/model<=1Mparameters; tests<=1500MiB.
Use transformers4.57.6,numpy2.2.6,soundfile.13.1,duckdb1.4.1; record actual runtime
versions/implementation hashes. No new heavy dependency in production.

One fresh review before remote run. Observe to terminal, inspect failures, download
only delta/small reports/predictions. If justified, compare16fixed held utterances
on original CPU: RAM-only base weights,4GiB hard/3.5GiB soft stop,.75CPU,1200s;
source/PCM/delta hashes exact, eager FP32. Report sequence/PER differences honestly.
Do not run simultaneous heavy local jobs. Live delay remains unmeasured until a
separate streaming/CPU budget test; likely needs a smaller student before release.

Report actual baseline versus adapted PER, group/support/exclusion counts, any
misses/collisions and remaining limits. Always qualified=false/production_changed=false
for this stage. No production integration, new APK, or threshold tuning on held
scores. Better phone transcription alone cannot establish reliable Quran grading.
