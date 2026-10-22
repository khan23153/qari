# Human realized-phone supervision — observed research evidence

This stage is **unqualified** and has changed no production model, UI or APK.
The user goal—reliably flag deliberate pronunciation/harakat errors while
preserving fast lexical tracking—remains open. Phone transcription alone is not
Quran pronunciation grading.

## Why a new stage

The preceding word-local vowel head detected15/33held errors, all on `kufuwan`,
and was rejected. Its CPU/GPU decisions matched, so this was not a portability
bug. New supervision uses human `phoneme_mis` (what was actually spoken), never
canonical expected phones as acoustic targets. Legitimate waqf can also differ
from canonical text; differences are not automatically Quran mistakes.

## Data and native model

The user personally approved the gated `IqraEval/Iqra_Extra_IS26` dataset.
Revision `4e996ef87c6d1da517a4f21bca91e0d577dd8c82`; full parquet208493997bytes,
SHA256 `9b0fed74472edd02c1f787839e51a7523df9fd32df7e98c9857d8cc30366b84c`.
All1330mono16kWAV sources audited;1327accepted,2quiet/1durationexcluded,
no duplicatePCM. Actual source guards remain .006RMS and .25–30s.

Frozen prospective collection-prefix/content split:563train/26validation/50test,
688cross-group quarantined,3source exclusions. Prefixes are **not verified
physical speaker identities**. All639assigned targets are CTC-representable.
Manifest identity `e9f880d0c3b7056b4ca8e87635d5a5aad4a71e1d9f7fc7d2a26176e90f44016f`.
TestGT separately remained403; no TestGT/user recordings used for training.

Base `MostafaMaroof/wav2vec2-arabic-phoneme-asr` revision
`0a32c641aaaeec6957e41a794add52e024e46b50`,1262135432-byte safetensors SHA256
`582149e3e913a0fc7f29c116530e0b1b6ae7a7ab23eef4efc3fc2acc760e2b75`.
Native80classes,blank77,between-phone delimiter75; `$`id0 stays a phone.
Only final2encoderlayers/native head adapt, with frozen-base digest checks,
FP32/eager, native frontend/SpecAugment,AdamW1e-5,seed42,max20epochs,
validation-only PER selection/patience4/min3. Candidate is a strict delta only.

## Engineering and review

Task1 17RED→GREEN and actual1330case prospective replay exact; full1131passed.
Task2 native tiny-model/delta/remote guard tests and full1164passed,1skip.
Fresh independent review found unseeded NumPy native SpecAugment despite Torch42.
Nonzero-mask regression reproduced unequal losses8.57834vs8.55375; fixed by
seeding Python/NumPy/Torch at the experiment boundary. Full1165passed,1skip,
1known Starlette warning65.81s. Reviewer found no Critical/Minor issues.
CUDA/native runtime,provider privacy,Quran grading and latency remain explicit
separate evidence gates. Research head after review fix:22e21d4.

## Private remote execution

Own private input `telethonfool/qari-iqra-extra-private-20261020` was created with
explicit public=False/original conditions, Other license and private-use notice;
provider `isPrivate=true`,ready,all7file names/sizes verified. No HF token uploaded.
Original source is hardlinked for staging, avoiding a second208MBVPS copy.

Kernel actual returned slug `telethonfool/qari-human-realized-phones-20261020`.
Provider normalized the title; no duplicate job was submitted. Version1 private
T4 source pulled and byte-verified against launcher SHA256
`527f15196143cea2d0c73d8b053c07dfc9579153057b9409246fe73820902de6`.
Started21:32UTC; all1330sources/639selected verified at21:33:45UTC.
Version1 **ERROR before any epoch or baseline score** at21:34UTC: lazy
`transformers.Wav2Vec2ForCTC` resolution occurred inside `torch.device('meta')`.
Installed TorchAO imports initialize quantization maps via `.tolist()`, which
cannot copy a meta tensor. The final wrapper ModuleNotFoundError hid this cause.
Public base download/checksum completed; strict native model load did not.

The fix resolves the native model class before entering meta construction;
regression uses an actual tiny native model/safetensors roundtrip with the
observed lazy-import CPU-list side effect. Native weights/targets/recipe unchanged.
Weights scratch moves to Kaggle temp so a failed job cannot publish a full base
weight as a working-directory output. Focused regression passed3.11s; full1166passed,1skip,1knownwarning65.57s.
Version2 retry is prepared after the verified terminal failure. No model accuracy exists yet.

## Artifacts and limits

Private source audit `/tmp/qari-conformer-training-20261009/iqra-extra-audit-20261020/`;
packet/observer `/tmp/qari-conformer-training-20261009/realized-phone-20261020/`;
durable tests/manifests `/home/innocent/qari-training-artifacts/iqra-human-phone-20261020/`.
The16held CPU comparison IDs were prospectively frozen before any new model score.
Any CPU check must use RAM-only base weights,4GiBhard/3.5GiBsoft,.75CPU,1200s;
no simultaneous heavy local job. Original315Mmodel may be too slow for live VPS.
No independent multi-surah/error-class qualification or live latency proof exists.

## Version2 terminal outcome

Same private kernel,version2,source byte-verified21:39UTC; implementation7d4d482,
launcherSHA5fccbd6010a3c99a2920b45561304fd5e3af573f5fc5aae5c575657a01c07702.
All1330sources/639selected reverified. Original315520720parameter model strict-loaded
and ready on TeslaT4 at21:40:52UTC; observed loading fix passed actual native runtime.
Version2 **COMPLETE21:46UTC**. Early stopping after5epochs selected epoch1.

| Measure | Baseline | Adapted |
|---|---:|---:|
| Validation phone errors /927 |145(15.6419%)|143(15.4261%)|
| Test phone errors /2190 |284(12.9680%)|279(12.7397%)|
| Exact realized test utterances /50 |2|2|

The gain is only5test phones (0.2283percentage points), not a solved pronunciation
grader. One test collection is unchanged; two improve by3and2phone edits.
Among32test canonical/realized contrasts excluding simple possible final-short-vowel
deletion contrasts, free transcription remains closer to canonical in5cases,
closer to actual realized phones in24,and tied in3: **unchanged from baseline**.
This is an utterance edit-distance diagnostic, never a Quran-error label. Other
legitimate realizations can remain; upstream training overlap/physical speaker
identity are unknown. No threshold or recipe changed from held observations.

Strict delta preflight passed:34allowed tensors,25274448adapted parameters,
101112189bytes,SHA256
`f20704f76cdfb8a031637e29ecd2357694e824c6cacdaa5a062019289d8cea45`.
Frozen before/after state hashes agree. Delta/report files are hardlinked into
durable private artifacts without another101MBdisk copy. No full base downloaded
to VPS disk. Actual remote Torch2.11.0+cu128,Transformers4.57.6,NumPy2.2.6,
SoundFile0.13.1,DuckDB1.4.1,safetensors0.8.0.

The16prospective held CPU check **passed**:90/758phone errors on both CPU/GPU,
zero decoded native-sequence differences,exit0,453.78s,peakRSS2456776KiB
(2.343GiB),no softstop. CPU Torch2.2.2/Transformers4.39.3/NumPy1.26.4 versus
remote2.11/4.57.6/2.2.6 are recorded; no byte-logit parity claim. Its
first attempt stopped before model download on extracted copies ownedroot; only
those16copies were assigned to user1002 and readability preflight added. Original
corpus unchanged. Meta-only shape preflight initially assumed every native param
was meta; Transformers4.39 explicitly allocates the1024-floatmaskedembedding onCPU.
Verified exactly that4096-byteexception; no315Mbase allocated for preflight.

Recovered log-stream ChunkedEncodingErrors did not restart training.
Draft https://github.com/khan23153/qari/pull/40 is stacked on PR39; all4CIchecks
SUCCESS at21:43UTC. No promotion implied; pronunciation goal remains open.

## Tarteel comparison checked against primary documentation

On2026-10-20, [Tarteel's own support article](https://support.tarteel.ai/en/articles/16559266-a-mistake-was-flagged-that-i-didn-t-make)
describes optional tashkeel mistake detection, distinguishes it from tajweed rules
(which it says are not checked), and acknowledges similar-letter false acceptance.
[Its colour guide](https://support.tarteel.ai/en/articles/12160141-what-do-the-different-text-colours-mean)
identifies yellow vowel-mark errors separately. This supports separate Qari
evaluation for word tracking,tashkeel and articulation/tajweed; it does not prove
Qari has solved any category or reveal Tarteel's private server architecture.
The user's requested vowel/adaegi improvement remains open.

Prior original315MCPU diagnostic under .75CPU measured median full-clip real-time
factor2.2469. Adapted streaming latency remains unmeasured; phone-PER gains cannot
justify putting this large synchronous model into the live word-tracking loop.

## Frozen direct Quran follow-up

Before further prediction, repeat the existing36public human-labelledQuran probe
with original base and this fixed delta in one private GPU session. Original
raw-native-ID grouping has3cross-labelcollision groups involving5error clips.
This directly tests whether that information failure persists beyond generic
phone-PER gains. The36sources predate newcandidate training; no training,
calibration,threshold selection or release. Labels are dataset-contributor
correctness labels, not independently annotated realized phones. Max600swhole/
720sprovider with existing12GiBRSS/4GiBdisk/2GiBGPUreserve guards. No further
heavyCPUjob. Source/PCM/speech guards,private original-condition input and
code/provider identity checks apply. Compare both models under one runtime;
record class collisions without treating arbitrary transcript differences as
proof of correct mistake detection. Actual results follow below.

## Direct Quran result —21October2026

Private probe `telethonfool/qari-native-quran-probe-20261021` version1
**COMPLETE04:55UTC**. All36sources passed unchanged speech/source/PCM guards;
16contributor-labellederror clips and20correct clips,0duplicatePCM or overlap
with the Extra adaptation corpus. Provider verified private input42files and
private code bytes. Source manifest SHA256
`e74cb94ac55de0696c1d1bc7f1bc1234b17a8a2f0212315d38ff5e5956e7329d`;
launcherSHA`708c12d6d106fbc8bfd80ddfe04bb867480ed2ee42ad98ea33cd8f478a65878b`.
Same TeslaT4/Torch2.11/Transformers4.57.6 runtime for both variants; no training.

| Raw native phone-sequence diagnostic | Original | Adapted |
|---|---:|---:|
| Cross-label collision groups within same ayah |3|4|
| Error-labelled clips sharing a sequence with a correct clip |5|7|

Nine of36phone sequences changed. All five prior colliding error cases remain;
the adaptation adds two. Dataset labels identify Qul in ayah1,Samad in ayah2
and kufuwan in ayah4; newly colliding cases are another Qul and kufuwan example.
No human-realized phone GT exists for these36; this is not7/16mistake recall,
nor does every changed output mean better recognition. It demonstrates that
sequence-only separation of labelled correct/error Quran recitation regressed.

**Reject this adapted candidate for live release.** Five fewer generic test phone
edits did not solve the original false-acceptance problem. Checkpoint portability
passed, so the failure is representation/decision quality rather than a corrupt
CPU checkpoint. Existing lexical matching also cannot establish correct vowels.
The source-label ambiguity,coverage,independent phone truth and live latency
gates remain open; no production/UI/model/APK change was made.

Reports are private hardlinks under
`/home/innocent/qari-training-artifacts/iqra-human-phone-20261020/quran-probe-20261021/`.
Probe input/entrypoint/provider-source/logs/receipts are under
`/tmp/qari-conformer-training-20261009/native-quran-probe-20261021/`.
CC-BY-4.0audio attribution and prior deterministic16kderivative notices retained.

The next investigation screens published pronunciation checkpoint formats and
Quran-specific human-error evidence before further expensive training. It must
not reuse a small phone-PER gain as a release criterion.
