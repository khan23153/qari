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
scores each word. Measured end to end on QuranMB.v2 (1,642 human-annotated
recordings) at the default threshold 0.5 (`QARI_PRON_VERIFIER_THRESHOLD`):
precision 0.82, recall 0.44, false alarms 0.65% per phoneme.

**It does not run in the live server.** Those numbers are per phoneme on
QuranMB.v2 and do not meet the release gate in `ml/evaluation/pronunciation.py`
(word level, human labels, precision >= 0.98 and recall >= 0.90 per error kind,
at least 5 held-out speakers and 3 surahs). Setting `QARI_PRON_VERIFIER_DIR`
alone does nothing: the server only checks for a qualification bundle (in a
worker thread, never on the event loop) and, without one, never loads the model.

Why not run it hidden next to the live ASR: measured on 2 x86 cores
(`scripts/bench_pronunciation_verifier.py`, synthetic audio) it takes 29 s to
load, **4.2 GB RSS** after load, and 1.9 / 4.5 / 7.7 s to score 5 / 10 / 15 s
of audio; two windows at once take 7.5 s each. That does not fit beside the
recognizer in a 6 GB container. Re-measure on the ARM server before any
qualified rollout.

Research ("shadow") scoring happens on an isolated worker instead:

1. On the server, `QARI_PRON_SHADOW_EXPORT=1` writes `pron_inputs.json` (word
   windows and expected phonemes; no model, no extra RAM) next to each
   session's `audio.wav`.
2. Copy those session folders to a separate machine or Kaggle and run
   `python scripts/pron_shadow_worker.py SESSIONS_DIR MODEL_DIR`. It writes
   `pron_shadow.json` per session (per-word and per-phoneme scores,
   fingerprint, threshold) for human review. Users see nothing.

Licence: the IqraEval datasets v3 was trained on (Iqra_train, Iqra_TTS,
Iqra_Extra_IS26) are CC BY-NC 4.0. Get the organisers' permission before
shipping this model in a product.

User-visible marks need `QARI_PRON_VERIFIER_DIR` plus
`QARI_PRON_VERIFIER_REPORT` pointing to an evaluation bundle written by
`write_evaluation_bundle` (human labels, model predictions, provenance with
training speakers/audio and file hashes, report). The server recomputes the
report from the raw rows with `verify_evaluation_bundle` and checks it against
the pipeline fingerprint (`PronunciationVerifier.fingerprint()`: model files,
threshold, phoneme lexicon, phonemizer and scorer source,
torch/transformers/numpy versions, the session's windowing code). A lone
report JSON is rejected. Marked words come back as
`error_type: "harakat_mistake"` with `evidence_source: "pronunciation_model"`;
it never clears an ASR verdict.

Rebuild the phoneme lexicon after a
corpus change with `python scripts/build_quran_phonemes.py`.
