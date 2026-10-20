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
