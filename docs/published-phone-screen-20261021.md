# Published native phoneme screen: still unqualified

The pinned S3PRL HuBERT phone model completed the frozen private inference screen,
but it does not qualify as Qari's pronunciation grader. Five contributor-labelled
incorrect Quran clips share an identical decoded native phone sequence with a
correct clip of the same ayah. Actual-phone test errors are 303/2,190 (13.8356%),
compared with 284/2,190 for the earlier original model and 279/2,190 after its
rejected adaptation. Production remains unchanged at
`0c7562b0ee35cee33f9e1884ac5f8e9a6974a37d`.

## Fixed experiment and implementation

Private Kaggle `telethonfool/qari-native-phone-screen-20261021`, version 1,
completed all 115 inferences: the existing 36 public contributor-labelled Ikhlas
clips (16 incorrect, 20 correct), the unchanged Extra validation/test roles
(26/50 utterances), and three synthetic non-speech controls. No training,
threshold selection, canonical prompt, language model or reference correction
entered the acoustic forward pass.

The native implementation uses the original 68-symbol dictionary plus PAD0,
EOS1 and UNK2, the learned mixture of 13 upstream hidden states, a 768→1,024
projector, and two bidirectional 1,024-unit LSTM layers with native projections.
The downstream head has 51,301,447 parameters. Native decoding collapses adjacent
frame repeats before removing PAD/EOS; it preserves blank-separated repeats,
case, geminated symbols and UNK. Input is native mono 16k PCM without waveform
normalization, as specified by the upstream task configuration.

Model pins:

- `Trikaldarshi/sws_pretrained_models`, revision
  `a85b70af9b797aab4eca8b3a7f1660486f7b4dcd`, `hubert_base.ckpt`,
  615,648,044 bytes, SHA256
  `eb419ff289cc3f503572e22d6c0c050a73c9b78fad381f528a7788c059e0fc66`.
- Separate upstream `s3prl/converted_ckpts`, revision
  `8cad0b370e7e35f8d56951d95d2be036ea85510c`, `hubert_base_ls960.pt`,
  378,864,853 bytes, SHA256
  `efe234bab3e77f0e10277f82094a24ad51fd7e8678b01f36cb0afef5527d3eb9`.
- Native [S3PRL source](https://github.com/s3prl/s3prl/tree/ec8064b5889f81ca460fbe2c094ce576a6f120b7),
  including the upstream expert, featurizer, RNNs and native CTC text encoder.
  Critical installed module hashes match the inspected source.

All 1,330 Extra source byte/PCM audits were repeated; only the fixed 76 held-role
waveforms were retained for inference. Both original provider datasets and the
kernel remained private. The original source conditions were preserved. No gated
corpus, credentials or complete model weights were added to Git or VPS disk.

## Actual measurements

| Check | Measured result |
| --- | --- |
| Native CUDA execution | Tesla T4, Torch 2.11.0+cu128, NumPy 2.2.6 |
| Runtime | 162.51 seconds, including bootstrap/model downloads |
| Remote peak RSS | 2,890,992 KiB, approximately 2.757 GiB |
| Extra validation | 173/927 phone edits, 18.6624%; 0/26 exact utterances |
| Extra test | 303/2,190 phone edits, 13.8356%; 0/50 exact utterances |
| Quran cross-label collisions | 3 groups containing 5 labelled incorrect clips |
| Quran empty/UNK decodes | 0/0 |
| Non-speech raw decodes | Silence: 0 phones; noise: 5; tone: 1 |

The native collision cases are `ID252V1F`, `ID279V1F`, `ID12V4F`, `ID26V4F`
and `ID69V4F`. They concern the contributor's Qul and kufuwan error locations.
These are **information collisions, not a calibrated detection recall**: the
36 clips do not have independent realized-phone transcripts, and model
posteriors could retain differences absent from their greedy sequences.

Compared with the previous model, failures move between recordings. An
exploratory joint grouping of the original and native model sequences leaves one
cross-label collision, `ID252V1F`. This reused-cohort observation is not an
ensemble classifier, independently validated improvement, or permission to select
thresholds from these clips. It also gives no VPS/streaming latency result.

Controls were acoustic diagnostics in a research runner with no live cursor or
WebSocket integration. Its `pronunciation_assessed=false`/`cursor_advanced=false`
fields express that absence of integration; they do not constitute live negative
control tests. Noise/tone emissions reinforce the need to retain speech guards.

## Verification and operational findings

A separate standard-library verifier recomputed the 76 realized targets, frozen
roles, phone edit counts, native ID/string mappings, 36 source PCM identities,
collision groups and control counts. It passed. The native tiny-RNN and literal
blank-separated repeat/EOS/UNK fixtures passed in a disposable container capped
at 1,500 MiB and 0.75 CPU. Independent source review found no Critical/Important
issues; a final resource check was added before output writes.

Actual limits were 900 seconds in the launcher and an explicit 960-second
provider limit, with 12 GiB RSS, 4 GiB free disk and 2 GiB free GPU reserves.
Weights-only loading was enforced; only `argparse.Namespace` was additionally
allowlisted for the legacy downstream checkpoint. Full checkpoint hashes and
strict native state loading passed before inference.

The former `/tmp` worktree, packets and CLI container were missing on resume;
their removal cause is unknown. Committed source and durable results survived.
Source was restored from `dd59107` into
`/home/innocent/qari-research/native-phone-screen-20261021` without modifying the
root production checkout. A separate bounded Python 3.12 CLI container restored
existing private-token authentication. Version-suffixed SSE log requests returned
404; the current owner/slug endpoint worked without restarting the model job.

The latest complete recitation/ML/core suite for unchanged source `7d4d482` was
1,166 passed and 1 skipped; subsequent `dd59107` was documentation only and its
CI passed. This follow-up changes documentation only; it does not claim a new
full-suite execution. Actual checkpoint/CUDA and artifact checks above are the
new verification evidence.

## Unfinished work

Pronunciation/harakat/adaegi detection remains unresolved. A word-match confidence
score cannot establish correct pronunciation. This published native alternative
also loses some required contrasts; do not deploy it or lower live guards.

The approved Extra corpus contains `@` text annotations, exactly associated with
reference/realized phone differences in its 1,330 rows, but marker semantics are
not documented by the inspected generic phonetizer wrapper. Legal waqf remains
ambiguous. Use its explicit realized-phone targets, not invented wrong-word
labels. Separate TestGT access was last observed denied; consent must be reviewed
by the user, never accepted on their behalf.

Next investigate the official error-aware OTTC/CROTTC model's exact native
frontend, inventory and checkpoint loading before another frozen private screen.
Public model/source availability is not release qualification or a blanket model
license. Keep the current models, UI, confidence/speech/cursor guards and free
compute policy.

Durable local evidence:
`/home/innocent/qari-training-artifacts/published-phone-screen-20261021/` contains
the frozen protocol, code-only packet, source/model metadata audit, native fixture,
provider privacy/source checks, review record, terminal logs, four output reports
and independent output verifier. No trained model or APK was released.
