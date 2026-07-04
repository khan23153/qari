# Contributing to Qari

## Non-Negotiables

Before writing any code, read and internalize these:

1. **No placement test.** Onboarding is two taps: language → starting point.
2. **All Quranic text, audio, and grammar data comes from verified sources.** No scraping, no unverified translations, no user-generated Quranic text. Quranic text is immutable — never editable, never stored per-user, never passed through spellcheck/autocorrect.
3. **Offline-first for content:** Module 1 lessons and Juz 30 text/audio must work offline after first sync.
4. **The AI never issues religious rulings.** It gives pronunciation feedback only. Doubt-clearing routes to human scholars.
5. **Content review gate:** Every lesson, translation choice, and Tajweed rule explanation ships only after scholar review board sign-off.

## Development Setup

```bash
./scripts/dev_setup.sh
```

## Code Style

- **Python**: Black formatting, type hints required, Pydantic for all schemas
- **Dart**: Follow `flutter_lints`, trailing commas required
- **SQL**: snake_case, UUIDv7 PKs for user-data tables, natural composite keys for corpus tables

## Testing

- Backend: `pytest` with pytest-asyncio
- ML: `pytest` for alignment and scoring logic
- Flutter: `flutter test` + integration tests
- Every release: RTL snapshot tests, Arabic text-shaping regression tests

## Content Pipeline

Lesson pipeline: draft → internal review → **scholar_approved** → published

The API serves only `review_status='published'` lessons. This is enforced at the database and API level.

## ML Precision Gate

≥90% word-verdict precision on beginner eval set, measured per accent cohort, before red highlighting is enabled in production (feature-flag `recitation_verdicts_enabled`).

A false "wrong" on Quran recitation destroys user trust faster than a missed error.
