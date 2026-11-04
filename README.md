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
<div align="center">
  <img src="branding/safha-icon.svg" alt="Safha app icon" width="108" />

  # Safha

  **Quran Hifz, Mushaf Reading & Hadith**

  A free, ad-free Quran learning app built with Flutter, FastAPI, and an evidence-first recitation engine.

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
  [Website](https://aiquranic.com) · [Features](#features) · [Getting started](#getting-started) · [Development status](#development-status) · [License](#license)
</div>

> **Formerly Qari.** The app and branding are now **Safha**; the repository, some internal identifiers, and `QARI_*` configuration variables retain their original names. The Android application ID and iOS bundle ID are `com.aiquranic.safha`.

## About Safha

Safha brings the printed Madinah Mushaf, memorization practice, Quranic Arabic learning, and a source-attributed Islamic Library into one app. Its recitation experience is designed around **evidence-backed progress**: a word is not confirmed simply because a model predicts what the Quranic text should say.

The Quran reader and bundled Library content are available offline. Sign-in, live server-assisted recitation, and some Library updates depend on a running backend.

**Safha is intended to remain free, without ads.** It is under active development; research models and incomplete features are not presented as production-quality pronunciation assessment.

## Features

### Quran reader and Mushaf

- Complete Quran corpus covering **114 surahs**, **6,236 ayahs**, and the **604-page Madinah Mushaf** layout.
- Offline-first Quran reading from `mobile/assets/quran_corpus.json.gz`.
- Paper presets including **Classic Madinah**, **Night**, **Parchment**, and **Minimal**. The Night theme uses Safha's warm charcoal, ivory, and amber palette.
- Word-level interaction, meanings, transliteration, grammar information, and Quranic roots where the underlying data is available.
- Color-coded **tajweed reference annotations** for rules such as ghunnah, ikhfa, idgham, iqlab, qalqalah, and madd. These describe the written reference; they do **not** prove that a user's spoken tajweed was correct.

### Hifz and recitation practice

- A Hifz reading mode that hides words and reveals them as the recitation engine confirms progress in order.
- Ayah markers remain visible even while the words are hidden.
- Live WebSocket recitation and an upload/review path, backed by speech recognition and word alignment.
- Conservative word matching: silence, wrong-surah audio, uncertainty, or a predicted canonical word alone must not count as confirmed recitation.
- Review feedback for **supported lexical mistakes** and **explicitly observed** diacritic conflicts, rather than inventing missing vowel evidence.

**Important accuracy limit:** Safha does **not** currently claim reliable acoustic detection of all incorrect **harakat**, **shadda**, **makhraj**, or **tajweed**. Live recognition uses an independent Arabic FastConformer RNNT; the legacy upload/research path also uses Whisper-based components. Correctly recognizing a word is not equivalent to verifying its pronunciation. Unqualified pronunciation and tajweed scores remain unavailable (`pronunciation_available: false`, `tajweed_available: false`).

### Islamic Library

- Hadith reading with grades **attributed to named scholars**, never generated as new religious rulings by an AI model.
- Source-referenced explanations for weak or fabricated narrations where reviewed source material exists.
- Isnād chains, narrator information based on *Taqrib al-Tahdhib*, and explanations of unfamiliar (*gharīb*) terms.
- Library API under `/v1/library` with a bundled offline fallback at `mobile/assets/library/library_seed.json`.

The bundled Library is a **starter collection**, not a complete hadith database. Entries marked `pending_scholar_review` require scholarly verification; some imported English translation rights are still being checked.

### Learning and supporting tools

- Quranic Arabic learning content, foundational lessons, and word/grammar exploration.
- Android-first app experience with Flutter code for iOS; iOS signing and distribution are not yet complete.
- A static landing website featuring Mushaf previews, a Hifz demonstration, and a Library preview.

## How it works

```text
                           Safha (Flutter)
                 Quran • Mushaf • Hifz • Library
                             │
                 HTTPS REST / WebSocket
                             │
             ┌───────────────┴────────────────┐
             │                                │
      Core API (FastAPI)              Recitation API (FastAPI)
      Auth • Quran content            Live recitation • Review
      Progress • Library                      │
             │                      ML / inference worker
       PostgreSQL + Redis           Independent ASR • Word matching
                                            │
                                   Evidence-backed feedback

                 Bundled Quran + Library assets
                   Offline reader / fallback
```

The deployment also includes Docker Compose infrastructure, a Caddy edge configuration, and optional external routing. See [`infra/README.md`](infra/README.md) for environment variables, authentication, deployment, and upgrade guidance.

### Recitation model policy

Safha separates **word recognition** from **pronunciation evaluation**:

1. **Live lexical recognition:** Independent FastConformer RNNT transcription provides candidate words, timing, and acoustic confidence. The expected Quranic text is used for constrained alignment and progress checks, not to fabricate recognized words.
2. **Word confirmation:** Strict matching and evidence guards determine which words may be marked as heard. Unsupported or unread words remain unconfirmed.
3. **Pronunciation research:** Additional acoustic models are evaluated separately against human-labelled speech. A research detector must not mark user-visible harakat mistakes until it passes the qualification policy in [`ml/evaluation/pronunciation.py`](ml/evaluation/pronunciation.py).
4. **No invented assessments:** Missing acoustic evidence is not a passing pronunciation result. Tajweed reference coloring and spoken tajweed scoring are different capabilities.

The current release policy checks **held-out human labels**, **speaker/surah coverage**, **separate vowel/gemination/consonant results**, **model identity**, and thresholds of at least **98% precision**, **90% error recall**, and no more than **2% false alarms**, alongside coverage requirements. **These are release targets, not achieved accuracy claims.**

The v3 pronunciation-verifier work in [PR #60](https://github.com/khan23153/qari/pull/60) is an **experimental shadow-mode proposal**, not an approved production pronunciation feature. Research metrics must not be confused with word-level release qualification.

## Project structure

```text
qari/
├── backend/
│   ├── core_api/           # Authentication, content, progress, Library
│   ├── recitation_api/     # Audio, WebSocket sessions, feedback
│   └── shared/             # Shared models and utilities
├── branding/               # Safha icon and generated platform assets
├── docs/                   # Architecture, evaluations, research notes
├── etl/                    # Quran content and morphology ingestion
├── infra/                  # Docker Compose, deployment, Caddy edge
├── ml/                     # ASR, alignment, tajweed, evaluation
├── mobile/                 # Flutter Android / iOS app
├── releases/               # Release metadata
├── scripts/                # Corpus, reference, and development utilities
├── website/public/         # Static landing website
├── context.md              # Historical engineering checkpoints and handoffs
└── LICENSE                 # MIT license for project source code
```

> `context.md` is an **engineering history**, not a live deployment-status dashboard. Older training results and server-health snapshots should not be assumed current.

## Getting started

### Requirements

- Flutter SDK compatible with `mobile/pubspec.yaml` (Flutter **3.27+**).
- Docker and Docker Compose for the backend.
- Python 3 for corpus/build utilities.
- Authorized access to any separately obtained, licensed ML model artifacts.

### Run the backend

From the repository root:

```bash
cp infra/.env.example infra/.env
# Fill in the required secrets and service configuration in infra/.env.
cd infra
docker compose config --quiet
docker compose up -d --build
docker compose exec core-api alembic upgrade head
```

**Do not commit** `.env` files, authentication credentials, signing keys, user audio, or proprietary model weights. Production deployments must use unique secure JWT and database credentials. A successful container startup does not guarantee models, external services, or the public website are configured.

### Run the Flutter app

```bash
cd mobile
flutter pub get
flutter run
```

Offline Quran and bundled Library views can work without the server; account and live recitation features require their corresponding APIs.

### Build the Quran assets

The offline corpus is generated by:

```bash
python3 scripts/build_local_corpus.py
```

This tool obtains source content from Quran.com. Review upstream attribution and permissions before redistributing regenerated text, translations, reciter audio, or other assets. After changing bundled assets, rebuild the mobile application.

To build a local full-surah recitation reference bundle from the mobile corpus:

```bash
python3 scripts/build_reference_from_local_corpus.py \
  --corpus mobile/assets/quran_corpus.json.gz \
  --out backend/recitation_api/reference_data
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
### Website

The landing page lives in [`website/public`](website/public). [`infra/Caddyfile.edge`](infra/Caddyfile.edge) can serve it at the site root while forwarding `/v1/*`, `/ws/*`, and `/health`. Its filesystem root can be configured with `QARI_WEBSITE_DIR`; `/download` redirects to `/v1/app/download` when the backend is available.

## Development status

| Area | Status / important limitation |
|---|---|
| Mushaf and offline Quran reader | Implemented in the app; bundled content works offline |
| Hifz word-following | Implemented with conservative word-confirmation rules; live speech requires the backend |
| Islamic Library | Reader, API, and offline seed implemented; content and translation rights still require review |
| Lexical recitation feedback | Implemented; recognition has known limitations and must not be equated with perfect pronunciation verification |
| Accurate spoken harakat / shadda detection | **Research / not qualified for user-visible grading** |
| Acoustic tajweed grading | **Not qualified**; visual tajweed reference annotations are available |
| Android release | Requires verified signing and distribution workflow for `com.aiquranic.safha` |
| iOS release | Flutter platform source exists; signed distribution has not been completed |
| Play Store launch | Requires release signing, privacy documentation, Data safety review, and store preparation |

The rename changed the Android package from `com.qari.app` to `com.aiquranic.safha`. These are **different application IDs**: an existing installation of the old package cannot upgrade in place to the new one, and uninstalling it can remove locally stored data.

## Responsible development

- **No invented Quran recitation verdicts.** Treat low-confidence audio, incomplete speech, and unsupported pronunciation phenomena as unassessed.
- **Source-attributed scholarship.** The app should not generate its own hadith grades or religious rulings. Material pending scholar review is not approved content.
- **User privacy.** Server-assisted recitation transmits voice audio; deployment requires clear privacy information, appropriate access controls, and careful retention handling.
- **Reproducible evaluation.** Acoustic pronunciation claims require independent, human-labelled validation across speakers and surahs; software unit tests alone are not accuracy evidence.
- **No ads.** The product's stated direction is free access without advertising.

## Data sources and attribution

Safha integrates and/or references sources whose **content licenses are separate from the MIT-licensed project code**:

- [Quran.com](https://quran.com/) — Quran text, translations, word-level data, and selected audio references; individual data and media permissions must be checked.
- [Quranic Arabic Corpus](https://corpus.quran.com/) by Kais Dukes — morphological and linguistic resources; subject to its own licensing terms.
- [Tanzil](https://tanzil.net/) — Quranic text, subject to its applicable terms.
- Hadith and narrator reference datasets — source- and translation-specific rights, attribution, and scholarly review still apply.
- Third-party recitation recordings, pretrained models, and pronunciation datasets — subject to their respective permissions and license restrictions.

**Licensing caution:** Research using IqraEval datasets has non-commercial licensing restrictions (CC BY-NC 4.0, according to the project research notes). An MIT license for Safha's own code does **not** grant commercial rights to such datasets, derived weights, or other third-party content. Commercial model use must be independently cleared with rights holders before distribution. The source of some Library English translations is still marked as unverified.

## License

This project's source code is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

*Note: Any third-party audio streams, recitation datasets, or phonetic corpora used with Qari remain subject to their respective upstream open-data licenses and terms of use.*
