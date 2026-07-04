# ML Recitation Engine — Implementation Roadmap

## Phase 0: Data & Model Groundwork (Weeks 1-4)

1. **Models/Datasets** (verify commercial license):
   - `tarteel-ai/whisper-base-ar-quran` — Quran-fine-tuned Whisper
   - `tarteel-ai/everyayah` — recitation dataset
   - `jonatasgrosman/wav2vec2-large-xlsr-53-arabic` — forced alignment
   - QDAT/mispronunciation corpora — Tajweed classifiers

2. **Reference Store**: For every ayah in MVP scope (Juz 30 + Al-Fatihah):
   - Expected phoneme sequence (grapheme-to-phoneme from Uthmani text)
   - Reference qari alignment (word/phoneme timestamps)
   - Tajweed annotation positions

3. **Evaluation Set**: ≥500 real beginner recordings
   - Hinglish-demographic accents (Indian/Pakistani Urdu speakers)
   - Label word errors manually
   - **Gate: ≥90% word-verdict precision before red highlighting ships**

## Phase 1: MVP Pipeline — Batch Analysis (Weeks 3-10)

Record → Upload → Analyze → Results in ≤5s.

1. **Capture** (Flutter): mono 16kHz 16-bit PCM WAV, client-side VAD, 60s max
2. **Transport**: POST multipart upload → 202 {session_id} → poll for results
3. **ASR Pass**: Whisper-Quran → hypothesis tokens → Levenshtein alignment
4. **Forced Alignment**: Wav2Vec2-CTC → per-word timestamps
5. **Scoring**: fluency = correct/expected × 100; overall = 0.7·fluency + 0.3·tajweed
6. **UI**: words tint green/red in place; red word tap → A/B audio comparison

## Phase 2: Tajweed Checks (behind feature flag)

- Ghunnah/Madd: duration rules, DTW on MFCCs
- Qalqalah: burst + release detection (binary classifier)
- Ikhfa/Idgham: noon-sakinah classifier
- Only surface `fail` with confidence ≥ 0.85

## Phase 3: Real-time Streaming (post-MVP)

WebSocket binary frames (100ms Opus chunks) → server-side VAD →
incremental Whisper → per-word verdicts pushed live.
