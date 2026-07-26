# Qari ML Architecture — Real-time Quran Recitation Tracking & Error Detection

Tarteel-class system: the app streams live microphone audio, the backend
transcribes it incrementally, aligns it against the expected Quranic text,
and pushes word-by-word verdicts (correct / mispronounced / skipped) back to
the phone in real time; a deeper post-session pass adds tajweed analysis.

```
 Phone (Flutter)                    VPS (docker compose)
┌──────────────────┐   PCM16     ┌─────────────────────────────────────────┐
│ native mic 16kHz ├────────────▶│ WS /ws/recitation/stream                │
│ 250ms frames     │  binary WS  │  StreamingRecitationSession             │
│                  │             │   ├─ buffer → 6s sliding window         │
│ live word events │◀────────────┤   ├─ VAD silence gate (ml/inference/vad)│
│ (matched/error/  │  JSON WS    │   ├─ FasterWhisperTranscriber (CT2 int8)│
│  skipped)        │             │   ├─ normalize_arabic                   │
└──────────────────┘             │   └─ StreamingMatcher (+ phonetics)     │
                                 │        └─ diff → word events            │
 upload flow (batch, deeper):    │                                         │
 WAV upload ────────────────────▶│ inference-worker: ml/pipeline.py        │
 full report ◀───────────────────┤  ASR → WordAligner → ForcedAligner      │
 (score + tajweed issues)        │  → TajweedChecker → scoring             │
                                 └─────────────────────────────────────────┘
```

## Feature map (the 6 requirements → code)

### 1. Real-time audio streaming & chunk-by-chunk processing
- **Client**: `mobile/.../streaming_recitation_service.dart` — native
  16 kHz PCM16 capture, buffered and flushed to the WebSocket every 250 ms
  as binary frames.
- **Server**: `backend/recitation_api/app/api/routes/websocket.py`
  (`WS /ws/recitation/stream`) →
  `backend/recitation_api/app/services/streaming_session.py` — accumulates
  PCM, re-transcribes a ~6 s sliding window every ~1.2 s of new audio in a
  worker thread, diffs word states, emits incremental `word` events.
- **Silence gating**: `ml/inference/vad.py` keeps silent windows from
  wasting decode cycles and stops silence from advancing the tracker.

### 2. Custom ASR for Quranic Arabic (fine-tuning scripts)
- **Whisper (transcription)**: `ml/training/finetune_whisper.py` — HF
  seq2seq fine-tuning, WER-validated. Start from
  `tarteel-ai/whisper-tiny-ar-quran` (live) / `-base-` (batch).
- **Wav2Vec2-CTC (alignment)**: `ml/training/finetune_wav2vec2.py` —
  explicit PyTorch loop (AdamW + warmup, AMP, grad-accum, CTC loss),
  dataset-derived char vocab, per-epoch WER/CER validation, best-WER
  checkpointing. This model powers the forced aligner, so better CTC ⇒
  better letter timing ⇒ better tajweed verdicts.
- **Runtime inference**: `ml/inference/asr.py` (PyTorch Whisper, batch) and
  `ml/inference/faster_whisper_transcriber.py` (CTranslate2 int8, live).

### 3. Phonetic text alignment (audio-text ↔ Quranic script)
- **Text level**: `ml/alignment/phonetic.py` — rule-based Arabic
  grapheme→phoneme with articulatory features (place/manner/voicing/
  emphatic) + weighted phoneme edit distance. Absorbs exactly the
  confusions Arabic ASR and accented reciters make (ص/س, ط/ت, ذ/ز, ق/ك)
  while keeping genuinely different words apart (الرحمن vs الرحيم).
  Wired into `StreamingMatcher._is_match` (char similarity OR phonetic
  similarity; disable with `use_phonetic=False`).
- **Audio level**: `ml/alignment/forced_alignment.py` — Wav2Vec2-CTC
  Viterbi alignment of the reference transcript onto the audio →
  per-word `{start_ms, end_ms, score}`. Model overridable via
  `QARI_ALIGNER_MODEL_DIR` (deploy your fine-tuned checkpoint).

### 4. Real-time error spotting
- **Missing / extra / wrong word (live)**:
  `ml/alignment/streaming_matcher.py` — greedy windowed alignment of the
  growing hypothesis vs the reference: `matched`, `error`
  (mispronounced), `skipped` (missed word); insertion detection absorbs
  repeated/hallucinated words. Stateless-per-call, stable across ASR
  revisions; `finalize()` marks unrecited words.
- **Tajweed mistakes**: `ml/tajweed/checks.py` — acoustic rule checks on
  aligned word windows: ghunnah (nasalization energy), qalqalah (burst),
  madd (duration vs expected beats), ikhfa, idgham. Runs in the batch
  pipeline (`ml/pipeline.py`) and on the live session's `finalize()` path —
  same placement as Tarteel (word tracking live; tajweed in the
  post-session "mistake review").
- **Full-session alignment (batch)**: `ml/alignment/word_alignment.py` —
  Needleman-Wunsch global alignment for the upload flow's verdicts.

### 5. Dataset creation, training & validation
- **Dataset**: `scripts/build_training_dataset.py` — everyayah.com
  recitations (the app's 5 reciters × 6236 ayahs) → 16 kHz mono WAV +
  `manifest.jsonl` paired with corpus Uthmani text. Extend with the HF
  `tarteel-ai/everyayah` crowd dataset + consented user uploads (the data
  flywheel — amateur voices are what separate Tarteel-level robustness
  from qari-only training).
- **Training**: the two fine-tuning scripts above, plus
  `ml/training/train_tajweed_classifier.py` for learned tajweed scoring.
- **Validation**: WER/CER splits inside both trainers;
  `ml/evaluation/evaluate.py` + `ml/evaluation/scoring.py` for
  end-to-end scoring; unit tests in `ml/tests/` (matcher, phonetics,
  alignment, tajweed) run without GPU.

### 6. Fast inference & API integration (no real-time delay)
- **Quantized runtime**: `scripts/convert_tarteel_model.py` converts any
  fine-tuned Whisper to CTranslate2 int8; served by
  `FasterWhisperTranscriber` (thread-pinned CPU decode).
- **Bounded work per pass**: sliding 6 s window + `WINDOW_SIZE=15`
  reference-word alignment window + VAD gate ⇒ per-pass cost is constant,
  independent of session length.
- **Transport**: single WebSocket, binary PCM up / small JSON events down;
  nginx WS timeouts raised to 1 h (`infra/nginx.conf`).
- **Latency gate**: `ml/evaluation/benchmark_latency.py` — run on the VPS
  before shipping any new live model; p95 window-decode must stay under
  the 1.2 s re-transcription budget.

## Model lifecycle (train → deploy)

```
build_training_dataset.py ─▶ manifest.jsonl
        │
        ├─▶ finetune_whisper.py  (GPU) ─▶ /models/qari-whisper-tiny
        │        └─▶ convert_tarteel_model.py ─▶ models/qari-ct2-tiny
        │                 └─▶ QARI_FASTERWHISPER_MODEL_DIR (live engine)
        │
        └─▶ finetune_wav2vec2.py (GPU) ─▶ /models/qari-wav2vec2-ctc
                  └─▶ QARI_ALIGNER_MODEL_DIR (forced aligner / tajweed)
```

Ship gate for every new live model:
1. `finetune_*` eval WER improved (amateur-voice split especially);
2. `benchmark_latency.py` p95 ≤ 1.2 s on the VPS;
3. one on-device recitation of Surah 1 tracks correctly end-to-end.

See `ml/training/README.md` for the step-by-step training playbook.
