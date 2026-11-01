# Deployment configuration

Copy `.env.example` to `.env`, fill in the blank values, and keep `.env` out of
version control. For a new deployment, generate independent JWT and database
secrets with `openssl rand -hex 32`. Put the database password in
`QARI_POSTGRES_PASSWORD` and its percent-encoded form in `QARI_DATABASE_URL`.
Both APIs and the worker receive the same signing key and algorithm from Compose.

`QARI_JWT_ISSUER` must equal the core API's `QARI_APP_NAME`; the default is
`qari-core-api`. Compose sets the core app name from this issuer. Use an explicit
JSON list for `QARI_CORS_ORIGINS` and the externally reachable HTTPS base URL for
`QARI_RECITATION_API_PUBLIC_URL`. Settings reject keys shorter than 32 bytes,
production debug mode, and wildcard production CORS. An omitted CORS list allows
no browser origins. Native mobile requests are unaffected by CORS.

Run these commands from this directory after configuring the values:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose exec core-api alembic upgrade head
```

The production Compose file uses built API code with reload disabled. Code
changes require rebuilding the images. Model/reference data and the shared ML
module stay mounted read-only. For local development, set
`QARI_ENVIRONMENT=development` and an explicit test signing key in each API's
local `.env` before running Uvicorn manually; `--reload` is suitable there.

## Upgrading an existing deployment

Preserve the existing secure signing key, algorithm, and issuer when deploying
this change to keep existing user access tokens valid. A deployment using the
old committed `change-me-in-production` key must generate a new key and ask
users to sign in again. Do not reuse that compromised key. If the core app name
was customized, set `QARI_JWT_ISSUER` to that existing name.

Postgres initialization variables do not change the password of an existing
database volume. Set the values to the existing database credentials for an
initial upgrade. To rotate a weak database password, use `ALTER ROLE` through a
trusted administrative connection, update both environment values, and restart
the core API. Keep the existing database volume; no user-table migration is
needed for recitation authentication.

Upload, result polling, audio playback, and verse identification require
`Authorization: Bearer <backend JWT>`. Batch result WebSockets require that same
upgrade header. Live WebSockets accept the header, or `access_token` in the
first JSON `start` message for browser clients. Query-string tokens are not
accepted. Missing/invalid authentication closes a socket with code `4401`;
unavailable owned results close with `4404`.

New batch and live recitations store the verified user ID in their session
metadata. Ownerless records from older deployments cannot be assigned safely
and return 404; their usual 24-hour Redis expiration remains in place. Clients
should offer a fresh recording. Audio becomes unavailable after the associated
session metadata expires, even if a file remains on disk.

## Optional: pronunciation model (Safha MDD v3)

A second opinion on words the ASR heard as right. It reads the expected phonemes
of the ayah (from `ml/assets/quran_phonemes.json.gz`) and the recorded audio, and
marks a word red only when it is confident. Measured end to end on QuranMB.v2
(1,642 human-annotated recordings) at the default threshold 0.5
(`QARI_PRON_VERIFIER_THRESHOLD`): precision 0.82, recall 0.44, false alarms 0.65%
per phoneme. It never clears an ASR verdict.

1. Copy `models/safha-mdd-v3/` from the `safha-latest` bundle into `QARI_MODELS_DIR`.
2. In `infra/.env`: `QARI_PRON_VERIFIER_DIR=/app/models/safha-mdd-v3`.
3. `docker compose up -d recitation-api`. The model (1.2 GB) loads on the first
   finished session; scoring takes about half the audio length on 2 CPU cores.

Words it marks come back as `error_type: "harakat_mistake"` with
`evidence_source: "pronunciation_model"`. Rebuild the phoneme lexicon after a
corpus change with `python scripts/build_quran_phonemes.py`.
