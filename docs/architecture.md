# Qari — Architecture Overview

## Service Topology

```
Mobile (Flutter)
   │  HTTPS/JSON (REST)                 │  WSS (binary audio frames)
   ▼                                    ▼
API Gateway (rate limit, JWT verify)
   ▼                                    ▼
core-api (FastAPI) ──────────► recitation-api (FastAPI, WebSocket)
   │        │                          │
   │        └── Redis (cache/session)  ├── GPU inference workers
   ▼                                   │      (Redis Streams queue)
PostgreSQL ◄────────────────────────── ┘
   ▲
etl-job (scheduled) ──► Quran.com API v4 + corpus.quran.com
CDN/S3 ◄── qari audio, makhraj videos, word audio
```

## Database

PostgreSQL 16 with three logical groups:
- **Corpus Mirror** (read-only): surahs, ayahs, words, roots, tajweed_annotations, qaris
- **Learning Content** (authored): lessons, quiz_questions, badges
- **User Data**: users, progress, flashcards, stats, recitation results, scholar questions

## Redis

- Content cache (ayahs, words, surahs — 24h TTL)
- Home aggregate (60s TTL)
- Streak lock (48h, idempotency)
- Rate limiting (sliding window)
- Redis Streams: recitation inference job queue

## Offline-First

- Module 1 lessons and Juz 30 text/audio work offline after first sync
- Bundle manifest endpoint provides zipped offline content
- Client-side SQLite (drift) for cached content
