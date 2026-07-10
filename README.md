# Qari — Quran Learning App MVP

> **Codename:** "Qari" · **Version:** 1.0 · **Status:** Approved for MVP build

A cross-platform (Android + iOS) mobile app for absolute beginners to:
1. **Learn** Arabic alphabet + foundational Quranic grammar (Module 1)
2. **Read** the Quran with color-coded, word-by-word grammar and meaning (Module 2)
3. **Master** Tajweed via an AI recitation feedback engine — the core USP (Module 3)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mobile (Flutter)                          │
│   Onboarding · Lessons · Quran Reader · Recitation · Flashcards  │
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
  PostgreSQL                   GPU Inference Workers
  (corpus + user)              (Whisper-Quran + Wav2Vec2)
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
└── scripts/               # Dev utilities
```

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

```bash
cd infra
docker-compose up -d postgres redis
cd ../backend/core_api
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
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

Generate the MVP-scope bundle (Al-Fatihah + Juz 30) from a running `core-api`:

```bash
python scripts/build_reference_bundle.py --core-api http://localhost:8000 \
    --out /tmp/qari_reference --scope mvp
# then set QARI_REFERENCE_DATA_DIR=/tmp/qari_reference when starting recitation-api
```

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

## Non-Negotiables

- **No placement test.** Onboarding is two taps: language → starting point.
- **All Quranic text, audio, and grammar data comes from verified sources.** No scraping, no unverified translations.
- **Offline-first for content:** Module 1 lessons and Juz 30 text/audio work offline after first sync.
- **The AI never issues religious rulings.** Pronunciation feedback only.
- **Content review gate:** Every lesson ships only after scholar review board sign-off.

## Attribution

- [Quran.com API](https://quran.com) — Quranic text, translations, audio
- [The Quranic Arabic Corpus](https://corpus.quran.com) by Kais Dukes (GNU license) — morphology, POS tags, roots
- [Tanzil](https://tanzil.net) — Uthmani text
- Qari audio licenses per reciter

## License

MIT — See [LICENSE](LICENSE)

*Legal review of each data source license before launch is a release blocker.*
