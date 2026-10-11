# Optional Arabic FastConformer RNNT adapter

`ml.inference.fastconformer_transcriber` supplies independent speech evidence
with NVIDIA's Arabic FastConformer **PCD** model, using its exported RNNT
branch and Sherpa-ONNX greedy decoding. No reference text, prompt, hotwords,
language model or vocabulary hints enter recognition. Existing Whisper models
are separate and remain available.

Install `backend/recitation_api/requirements-fastconformer.txt` alongside the
API requirements and existing NumPy runtime. It pins both `sherpa-onnx` and
`sherpa-onnx-core` to 1.13.8. Set `QARI_FASTCONFORMER_MODEL_DIR` to the directory
containing the four assets below, or use the default
`/app/models/qari-fastconformer-pcd-rnnt-int8`. The adapter does not download
models. Readiness calls `get_transcriber().load()`; loading is lazy, serialized,
and checks all asset hashes once before constructing the recognizer.

Input is 16 kHz mono float PCM in `[-1, 1]`; invalid rates, dimensions, values,
or incomplete decoder evidence raise. The adapter does not resample, amplify,
pad, or normalize Arabic text. BPE `▁` and spaces delimit raw words; diacritics
remain available to the caller's existing normalizer.

`transcribe(audio, sample_rate=16000)` returns frozen `TimedTranscript` with
`words`, `confidences`, and `timings`. Legacy two-value unpacking still yields
words and confidences. A word's confidence is exactly the geometric mean of
its native token probabilities: `exp(sum(token_log_probs) / token_count)`.
Low scores and genuine zero underflow are retained. Missing or invalid scores
never acquire a synthetic confidence.

Each timing is `(minimum_token_timestamp, maximum_token_timestamp)` in seconds
relative to that decode's audio window. These are native RNNT **emission**
bounds, with 0.08-second frame resolution for this export. A single-token word
has equal start and end times; no additional trailing frame is added. They are
not acoustic or phoneme alignments and cannot by themselves support tajweed
judgments. Token, score, and timestamp arrays must have identical lengths;
nonfinite, negative or decreasing timestamps fail closed.

## Model provenance and attribution

Original model: [NVIDIA STT Ar FastConformer Hybrid Transducer-CTC Large (PCD)
v1.0](https://huggingface.co/nvidia/stt_ar_fastconformer_hybrid_large_pcd_v1.0).
Copyright NVIDIA. The upstream model license is
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The RNNT branch was exported into Sherpa's `nemo_transducer` format and
dynamically quantized to INT8 by the **fuKhushu project**, distributed by
Synthesium. Credit NVIDIA for the model and fuKhushu for export/quantization.
The [export model card](https://huggingface.co/Synthesium/quran-recitation-v2-onnx/blob/a57907844f7c72969b40bc526a57e9c9dbc8bf3f/README.md)
identifies this folder as CC BY 4.0; other models in that repository have
different licenses and are not used by this adapter. Qari adds an evidence
adapter and makes no weight modifications.

All four assets come from
`Synthesium/quran-recitation-v2-onnx`, revision
`a57907844f7c72969b40bc526a57e9c9dbc8bf3f`, folder
`fastconformer-ar-transducer/`. Use this pinned revision when provisioning:

| Asset | Bytes | SHA256 |
| --- | ---: | --- |
| [encoder.int8.onnx](https://huggingface.co/Synthesium/quran-recitation-v2-onnx/resolve/a57907844f7c72969b40bc526a57e9c9dbc8bf3f/fastconformer-ar-transducer/encoder.int8.onnx) | 172433955 | `583d152c5bfd7dbfaa573319043fed4f1ef448add3f769d31b3dddf31e4e533f` |
| [decoder.int8.onnx](https://huggingface.co/Synthesium/quran-recitation-v2-onnx/resolve/a57907844f7c72969b40bc526a57e9c9dbc8bf3f/fastconformer-ar-transducer/decoder.int8.onnx) | 15753636 | `9ee2286747a5bd5cfeb1808af7eca42a763cd057e1ebb78cb3cb93a48e559a90` |
| [joiner.int8.onnx](https://huggingface.co/Synthesium/quran-recitation-v2-onnx/resolve/a57907844f7c72969b40bc526a57e9c9dbc8bf3f/fastconformer-ar-transducer/joiner.int8.onnx) | 1419720 | `5015e28f1ea3b8b56d25212a69629d7e49d750ce2a56d181dbd53a23b3b5dec2` |
| [tokens.txt](https://huggingface.co/Synthesium/quran-recitation-v2-onnx/resolve/a57907844f7c72969b40bc526a57e9c9dbc8bf3f/fastconformer-ar-transducer/tokens.txt) | 12858 | `9b938381a19a69bb279cdcfc299419f25a049ea1de192e0d10317274a0f20074` |

The three ONNX hashes were verified against the pinned repository's LFS
SHA256s; the token file was downloaded from the same revision and hashed.
Inspection of these exact encoder bytes recorded the following model metadata:

```text
url=https://huggingface.co/nvidia/stt_ar_fastconformer_hybrid_large_pcd_v1.0
model_type=EncDecHybridRNNTCTCBPEModel
model_author=NeMo
vocab_size=1024
subsampling_factor=8
comment=Only the transducer branch is exported. CC-BY-4.0.
```

Runtime hash checks enforce this inspected PCD identity without requiring an
ONNX parsing dependency. A different model or changed export fails readiness.
Sherpa's [NeMo transducer documentation](https://k2-fsa.github.io/sherpa/onnx/pretrained_models/offline-transducer/nemo-transducer-models.html)
describes the runtime format. This adapter's unit tests exercise evidence and
readiness contracts with external inference replaced; actual model quality and
runtime performance require separate qualification with the pinned assets.
