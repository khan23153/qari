# Safha (Qari) — Quran Hifz, Reading and Recitation App

> **Codename:** "Qari" · **App name:** Safha (صفحہ, "page") · **Package:** `com.aiquranic.safha`
> **Status:** Android app released as a signed APK on GitHub Releases; not on Google Play yet.

An Android app (Flutter) for reading, learning and memorising the Quran:
1. **Recite** a surah and follow along word by word, right to left like a printed
   Mushaf. Skipped and wrong words turn red, live (Hifz and Tilawat).
2. **Read** the Quran word by word with translation (English, Urdu), grammar
   and tajweed colours, and reciter audio. Works offline.
3. **Learn**: Arabic foundation, Quranic grammar, 60 vocabulary levels, root
   explorer, tajweed and makhraj practice.
4. **Library**: 7 hadith collections and a forwarded-hadith checker, Qibla,
   Tasbih, Ask a scholar. App languages: English, Urdu, Arabic.

Other recitation features: similar-verse (mutashabihat) detection, a 604-page
Hifz map, and Find a verse (recite a few words, get the surah and ayah).

### What the recitation feedback can and cannot do today

| Check | Status |
|---|---|
| Skipped words, wrong words, wrong ayah | Live, from the word-level recogniser |
| Wrong harakat (fatha/kasra/damma/sukun), shadda, consonant articulation | **Not shown to users.** `pronunciation_available` stays `false` until a model passes the release gate (below). |
| Tajweed rules (ghunna, ikhfa, madd length…) | Not assessed |

The app never issues religious rulings and does not replace a teacher.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mobile (Flutter)                          │
│   Onboarding · Lessons · Quran Reader · Recitation · Library     │
└───────────────┬───────────────────────────┬──────────────────────┘
                │ HTTPS/JSON (REST)          │ Multipart upload
                ▼                           ▼
        ┌──────────────┐          ┌──────────────────┐
        │  core-api    │          │ recitation-api   │
        │  (FastAPI)   │          │ (FastAPI + WS)   │
        └──┬───┬───────┘          └──┬───────────────┘
           │   │                     │
     ┌─────┘   └── Redis ────────────┤
     ▼              (cache/queue)    ▼
  PostgreSQL                   CPU inference (same host)
  (corpus + user)              (FastConformer RNNT live,
                                Whisper witness, final review)
     ▲
     │
  ETL Job ──► Quran.com API v4 + Quranic Arabic Corpus
```

## Repository Structure

```
qari/
├── backend/
│   ├── core_api/          # FastAPI — content, users, progress, flashcards, SRS
│   ├── recitation_api/    # FastAPI — audio upload, WebSocket, inference queue
│   └── shared/            # Shared Pydantic models, constants
├── etl/                   # Quran.com + Quranic Arabic Corpus ETL pipeline
├── ml/                    # ML inference, alignment, tajweed checks, evaluation
├── mobile/                # Flutter app (Android + iOS)
├── infra/                 # Docker Compose, Dockerfiles, nginx, deploy configs
├── docs/                  # Architecture, API spec, ML roadmap
└── scripts/               # Dev utilities (incl. build_local_corpus.py)
```

### Local Quran corpus (offline reader)

The mobile reader loads the full Quran from a bundled asset
(`mobile/assets/quran_corpus.json.gz`) so it works offline and is never blank,
even when `core-api`'s corpus DB is empty. Regenerate it with:

```bash
python3 scripts/build_local_corpus.py
```

This pulls all 114 surahs from the Quran.com API v4 (Uthmani text, EN/UR
translations, word-by-word transliteration + meaning) and, importantly,
fetches `text_uthmani_tajweed` to compute **per-word tajweed spans** (each
letter range tagged with its rule: ghunnah, ikhfa, qalqalah, idgham, iqlab,
madd, etc.). In the reader, toggle **Tajweed** in the settings bar to colour
each letter by its rule (mutually exclusive with Grammar); tap a word to see
its tajweed rule(s) in the detail sheet. The bundle is gzipped into the APK
asset, so **rebuild the APK** after regenerating the corpus.

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile | Flutter 3.x (Dart) |
| Backend API | Python 3.12 + FastAPI |
| ML Serving | FastAPI worker pods + ONNX Runtime / TorchServe |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Object Storage | S3-compatible + CDN |
| Auth | Firebase Auth → backend JWT exchange |

## Quick Start

### Backend (core-api + recitation-api)

Configure `infra/.env` from `infra/.env.example` first. Both APIs require the
same explicit JWT signing key. See [deployment setup and upgrade notes](infra/README.md)
for production configuration and existing-token compatibility.

```bash
cd infra
docker compose config --quiet
docker compose up -d --build
docker compose exec core-api alembic upgrade head
```

### ETL Pipeline

Seeds the corpus mirror in `core-api`'s Postgres from two verified sources:

1. **Quran.com API v4** (`api.quran.com/api/v4`) — surahs, Uthmani + Imlaei
   text, translations, word-by-word transliteration/translation, per-word
   audio, and ayah audio URLs with segment timestamps per qari. Tajweed
   annotations are derived by parsing the `text_uthmani_tajweed` variant.
2. **Quranic Arabic Corpus** (`corpus.quran.com`, Kais Dukes, GNU license) —
   the downloadable, versioned morphology TSV, parsed offline for POS tags,
   segments, features, lemmas, and roots.

```bash
cd etl
pip install -r requirements.txt
# Download the morphology file first (corpus.quran.com) and point to it:
export QURANIC_CORPUS_FILE=/path/to/quranic-corpus-morphology.txt
python -m etl.run_full_pipeline
```

The pipeline validates canonical row counts (114 surahs / 6,236 ayahs /
77,430 words) and **fails loudly** if the Uthmani text differs from the
previous load.

| Env var | Default | Purpose |
|---|---|---|
| `QURANIC_CORPUS_FILE` | `quranic-corpus-morphology.txt` | Path to the morphology TSV (required for roots/POS) |
| `DATABASE_URL` | `postgresql+asyncpg://qari:qari@localhost:5432/qari` | Target Postgres for `core-api` |
| `QURAN_COM_BASE_URL` | `https://api.quran.com/api/v4` | Quran.com API root |
| `ETL_LOAD_CORPUS` | `true` | Parse morphology + extract roots |
| `ETL_LOAD_TAJWEED` | `true` | Parse tajweed annotations |
| `ETL_LOAD_AUDIO` | `true` | Fetch reciter audio + segments |
| `ETL_DB_SCHEMA` | `quran` | Postgres schema for ETL tables |
| `ETL_MAX_CONCURRENT_SURAHS` | `5` | Fetch concurrency |
| `ETL_RATE_LIMIT_DELAY` | `0.2` | Min seconds between API requests |

### Mobile (Flutter)

```bash
cd mobile
flutter pub get
flutter run
```

### Recitation engine (recitation-api)

The recitation worker runs the real ML pipeline (`ml/`: Whisper ASR + Wav2Vec2
forced alignment + scoring). The pipeline needs an **expected-word reference**
per ayah (normalized text + tajweed positions), resolved from:

1. A file bundle directory (`QARI_REFERENCE_DATA_DIR`, files named `{surah}_{ayah}.json`),
   or
2. Lazily from `core-api` (`QARI_CORE_API_BASE_URL`, default `http://localhost:8000`).

Build the reference bundle. Two builders exist:

- `scripts/build_reference_bundle.py` — fetches reference words/tajweed from a
  running `core-api` (`GET /v1/surahs/{n}/ayahs`). Use when the corpus DB is
  populated:
  ```bash
  python scripts/build_reference_bundle.py --core-api http://localhost:8000 \
      --out /tmp/qari_reference --scope mvp
  ```
- `scripts/build_reference_from_local_corpus.py` — builds the **full** bundle
  (all 114 surahs / 6,236 ayahs) directly from the bundled mobile corpus
  (`mobile/assets/quran_corpus.json.gz`). Use this when `core-api`'s corpus is
  empty (the default on a fresh deploy):
  ```bash
  python scripts/build_reference_from_local_corpus.py \
      --corpus mobile/assets/quran_corpus.json.gz \
      --out backend/recitation_api/reference_data
  ```
  Then set `QARI_REFERENCE_DATA_DIR=/app/reference_data` on the worker.

The worker image installs the ML runtime deps from
`backend/recitation_api/requirements.ml.txt` (CPU torch / transformers /
torchaudio / librosa / soundfile). `recitation-api` and `inference-worker`
share the `qari_audio` Docker volume so uploaded audio is visible to the
worker. `QARI_ML_USE_STUB` is `false` in production — the real Whisper-Quran
pipeline runs (no hardcoded scores).

Env overrides (prefix `QARI_`):

| Var | Default | Purpose |
|---|---|---|
| `QARI_ML_USE_STUB` | `false` | Use the deterministic stub (no GPU) instead of the real pipeline |
| `QARI_REFERENCE_DATA_DIR` | `""` | Prebuilt per-ayah reference JSON directory |
| `QARI_CORE_API_BASE_URL` | `http://localhost:8000` | Fallback source for reference words/tajweed |
The backend returns results in the exact shape the Flutter `RecitationResult`
model parses (`{status, result:{overall_score, word_verdicts:[...]}}`). When a
reference/model is unavailable the engine returns a low-confidence result
(no red marks) rather than a false verdict.

### Live recognition

The live session (`backend/recitation_api/app/services/streaming_session.py`)
streams 16 kHz PCM over a WebSocket. Production uses an NVIDIA Arabic
FastConformer RNNT (INT8 ONNX, `QARI_LIVE_ASR_ENGINE=fastconformer_rnnt`) that
is **not** given the expected text, plus a Whisper "witness" model. Words are
accepted only on native evidence from the audio
(`ml/alignment/streaming_matcher.py`, `ml/alignment/native_evidence.py`).
Model files come from the `safha-latest` backup bundle; see
[infra/README.md](infra/README.md).

## Pronunciation and harakat mistake detection (research)

Goal: tell what the reciter actually said from what the Mushaf expects, at the
level of a single haraka, shadda or letter, and show a red mark only when that
is reliable.

**Release gate.** `ml/evaluation/pronunciation.py` decides when a model may
mark words for users. It needs word-level human labels, at least 5 held-out
speakers and 3 surahs, at least 100 wrong and 100 correct words, and at least
20 of each kind (vowel, gemination, consonant). For every kind it needs
precision ≥ 0.98, recall ≥ 0.90, false alarms ≤ 2% and coverage ≥ 0.95. The
live server accepts only an evaluation bundle (raw labels + predictions +
provenance, recomputed on load by `verify_evaluation_bundle`) tied to the
exact pipeline fingerprint. Without one the model is never loaded.

**Where we are** (details and every number with its interval:
[docs/mdd-v3-baseline-and-copying-test-20261104.md](docs/mdd-v3-baseline-and-copying-test-20261104.md)):

| Model | Data / test | Word recall | Word precision | Status |
|---|---|---|---|---|
| v3 (w2v-BERT 2.0 + reference-aware verifier) | QuranMB.v2, threshold 0.5 | 0.61 | 0.86 | Fails the gate. Off in production. |
| v3 + GOP fusion (no retraining) | QuranMB.v2, held-out recording groups | 0.535 (v3: 0.471) | 0.945 | Best so far. Still far from the gate. |
| E3: verifier retrained on targeted planted changes | Same | No gain over v3 | — | Rejected |

Main findings so far:

- Planted test: one haraka, shadda or letter is changed in the expected text,
  and the recording is a correct recitation. Here the verifier barely notices a
  changed vowel (AUC 0.54–0.59). A likelihood score (GOP) from the same
  encoder's CTC head notices it (AUC 0.90–0.92). The sound information is in the
  encoder, but the verifier does not use it.
- On real mistakes, 30–38% of error positions are missed by both signals, with
  the model confident it heard the expected text. These are either label errors
  or a bias toward the canonical text. A blinded human listening review is being
  set up to measure which.

Tools:

- `ml/evaluation/word_level_mdd.py`: per-kind word metrics with Wilson
  intervals, attributed precision and false alarms, and uncertain-word handling.
- `ml/inference/pronunciation_verifier.py`: the v3 scorer and pipeline
  fingerprint.
- `scripts/bench_pronunciation_verifier.py`: load time, memory and latency.
  v3 measures 4.2 GB RSS and 0.4–0.5× real time on 2 cores.
- `scripts/pron_shadow_worker.py`: offline scoring on an isolated worker, fed
  by `QARI_PRON_SHADOW_EXPORT=1`.
- `ml/alignment/quran_g2p.py` and `ml/assets/quran_phonemes.json.gz`: our own
  phonemizer and per-word phoneme lexicon for the whole Quran.

**Data licences.** The IqraEval datasets (Iqra_train, Iqra_TTS,
Iqra_Extra_IS26, QuranMB.v2) are CC BY-NC 4.0. Models trained on them stay
research-only until the organisers grant permission. Tarteel TLOG is CC BY
4.0, but it has no mistake labels or speaker IDs.

## Non-Negotiables

- **No placement test.** Onboarding is two taps: language → starting point.
- **All Quranic text, audio, and grammar data comes from verified sources.** No scraping, no unverified translations.
- **Offline-first for content:** Module 1 lessons and Juz 30 text/audio work offline after first sync.
- **The AI never issues religious rulings.** Pronunciation feedback only, and only from a model that passed the release gate.
- **Content review gate:** Every lesson ships only after scholar review board sign-off.

## Attribution

- [Quran.com API](https://quran.com) — Quranic text, translations, audio
- [The Quranic Arabic Corpus](https://corpus.quran.com) by Kais Dukes (GNU license) — morphology, POS tags, roots
- [Tanzil](https://tanzil.net) — Uthmani text
- [IqraEval](https://huggingface.co/IqraEval) datasets (CC BY-NC 4.0) — research and evaluation only
- [Tarteel AI TLOG / EveryAyah](https://huggingface.co/tarteel-ai) — evaluation clips (TLOG: CC BY 4.0)
- Qari audio licenses per reciter

## License

MIT — See [LICENSE](LICENSE)

*Legal review of each data source license before launch is a release blocker.*
