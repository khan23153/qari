# Qari API Specification

## Base URL
`https://api.qari.app/v1`

## Authentication
All user endpoints require `Authorization: Bearer <token>` header.
Token is a backend JWT obtained via Firebase Auth → `/users/auth/exchange`.

## Content Endpoints (public, cached)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/surahs` | List all 114 surahs |
| GET | `/surahs/{n}` | Surah metadata + context story |
| GET | `/surahs/{n}/ayahs?from=&to=&lang=&qari=` | Ayahs with embedded word array |
| GET | `/words/{surah}:{ayah}:{pos}?lang=` | Full word detail (morphology, root) |
| GET | `/roots/{root_id}?lang=` | Root meaning + occurrences |
| GET | `/lessons?module=&lang=` | Published lesson manifest |
| GET | `/lessons/{id}?lang=` | Full lesson payload |
| GET | `/content/bundle?scope=juz30&lang=` | Offline bundle manifest |

## User Endpoints (JWT required)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/users/onboarding` | Complete onboarding (language + path) |
| POST | `/users/auth/exchange` | Exchange Firebase token for backend JWT |
| GET | `/me/home` | Aggregated home screen data |
| POST | `/progress/lessons/{id}` | Record lesson completion |
| POST | `/progress/ayahs` | Batch mark ayahs studied |
| GET | `/flashcards/due?limit=20` | Due flashcards |
| POST | `/flashcards/{id}/review` | Submit SM-2 review grade |
| GET | `/recitations/{session_id}` | Recitation result report |

## Recitation API (separate service)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/recitations/upload` | Upload audio (multipart) |
| GET | `/recitations/{session_id}` | Poll for results |
| WS | `/ws/recitation/{session_id}` | WebSocket for real-time results |

## Error Format
RFC 7807 problem+json:
```json
{
  "type": "https://api.qari.app/errors/...",
  "title": "Resource not found",
  "status": 404,
  "detail": "Surah not found",
  "instance": "/v1/surahs/999"
}
```

## Query Parameters
- `lang`: `en` | `ur` | `hi_latn` (default: `hi_latn`)
- `qari`: qari ID (default: 1 = Alafasy)
- `from`/`to`: ayah range (max 20 per request)
