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

```bash
cd etl
pip install -r requirements.txt
python -m etl.run_full_pipeline
```

### Mobile (Flutter)

```bash
cd mobile
flutter pub get
flutter run
```

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
