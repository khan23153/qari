# Raw ASR tashkeel probe — 25 October 2026

Probe executed at 04:53 UTC, using the observed-mistakes deployment from 24 October.

## Runtime inspected

Deployed source: `5eb14335584618f53dd7ec58a4830b8512deb61b`.

- Live recitation API: `QARI_LIVE_ASR_ENGINE=fastconformer_rnnt`, pinned NVIDIA Arabic FastConformer hybrid large PCD v1.0 RNNT INT8 export in `/app/models/qari-fastconformer-pcd-rnnt-int8`.
- Upload worker command: `python -m app.workers.fast_inference_worker`. Its actual decode method is `transcribe_independent_with_timings`, which loads `/app/models/qari-ct2-base`. A `qari-v50-ct2` environment setting exists but that absent prompted model is not the independent worker's loaded decoder.
- There are no tracked audio fixture files in this checkout. Used the real Quran recording `ID3V1T.wav` (Ikhlas 112:1) from the recovered qualification fixtures, already used by the public live/upload regression harnesses. WAV SHA256: recorded in the local raw JSON evidence.
- Ran both native decoders in an isolated container using the deployed image/source and installed read-only weights; network disabled, 2 GiB/no swap/.75 CPU. No production process/configuration was changed.

## Exact native output before application text processing

RNNT: read `stream.result.text` directly, before `decode_result` or matcher normalization:

```text
قل هو الله أحد
```

Fatha, kasra, damma and all inspected Arabic combining marks: **zero** in this output. This live test produces undiacritized text; therefore it cannot establish live short-vowel conflicts from emitted marks in this sample.

Whisper: captured `segment.text` directly before application `.strip()`/word grouping. Unmodified segment strings:

```json
["قُلْ هُوَ اللَّهُ أَحَدٌ", "مَا يَغْفَى", "مَا يَغْفَى", "مَا يَغْفَى", "مَا يَغْفَى"]
```

Exact concatenation, without adding separators or removing characters:

```text
قُلْ هُوَ اللَّهُ أَحَدٌمَا يَغْفَىمَا يَغْفَىمَا يَغْفَىمَا يَغْفَى
```

The raw Whisper result contains **16 fathas, 3 dammas, 0 kasras**, plus sukun, shadda and dammatan. Kasra is not expected in the recited ayah. It **does emit tashkeel**, but the repeated `مَا يَغْفَى` tail is hallucinated. These bytes are not a corrected/display transcript or a pronunciation judgment. The production timestamp/native-gap guards are separate from this intentionally raw capture.

Decode options match the upload worker: Arabic transcription, beam size 1, timestamps on, VAD off, temperature 0, `initial_prompt=None`, `condition_on_previous_text=False`, 64-new-token cap. No target verse text was provided.

## Public Quran Whisper checkpoint

[`tarteel-ai/whisper-base-ar-quran`](https://huggingface.co/tarteel-ai/whisper-base-ar-quran) is publicly available and ungated, checked through the Hugging Face model API. Retrieved revision: `5c3c53fdf9272c4f6ee0bee09a1e5a4a615ee25c`.

The codebase references it as `WHISPER_MODEL_ID` in `ml/inference/asr.py` and as the training default. Those references do not mean the current live RNNT route uses it. The local CT2 base manifest supplies hashes rather than a verifiable upstream repository/revision identity; do not infer exact upstream lineage solely from its local name. Its observed vocalized output is proved by the probe above. The public model card does not establish acoustic mistake-detection qualification.

## Evidence and limits

Local replay script and complete machine-readable output (including native RNNT tokens, unmodified Whisper word strings and Unicode mark positions):

- `/home/ubuntu/qari-task-artifacts/observed-mistakes-20261024/probe_raw_tashkeel.py`
- `/home/ubuntu/qari-task-artifacts/observed-mistakes-20261024/raw-asr-tashkeel.json`

One correct recording is a diagnostic sample, not proof that RNNT never emits a mark or that Whisper accurately follows deliberately changed vowels. Diacritized ASR can canonicalize pronunciation and hallucinate. Acoustic pronunciation/tajweed availability remains false.
