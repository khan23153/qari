# Qari — Project Memory

> Persistent notes so opencode can resume after a VPS restart / new session.
> Read this file first at the start of every session. Update it whenever
> meaningful work is done. Keep it concise.

## Project
- **Qari**: AI-powered Quran learning app (Flutter mobile + Python/FastAPI backend).
- Repo: https://github.com/khan23153/qari
- Mobile app lives in `mobile/`, backend in repo root (core_api, infra, etl, etc).
- Current app version: **1.0.1+6** (versionCode 6).
- Flutter SDK location (not in PATH by default): `/home/Innocent/flutter/bin/flutter`
  - Build APK: `cd mobile && flutter pub get && flutter build apk --release`
  - Output: `mobile/build/app/outputs/flutter-apk/app-release.apk` → copy to `releases/app-release.apk`

## Deployment / Infra
- VPS IP: **20.197.40.13** (HTTPS). Backend + OTA served here.
- OTA app download endpoint: `https://20.197.40.13/v1/app/download`
- Direct APK in repo: https://github.com/khan23153/qari/raw/main/releases/app-release.apk
- Release metadata: `releases/app_release.json` (bump `version_code` + `version` on each release).
- NOTE: VPS sometimes auto-shuts off → work/session lost. Re-read this file on restart.

## Last session (2026-07-13, commit b70e27d)
Fixed 7 reported mobile bugs:
1. Signup/Login: clear cached progress + fetch live home data (killed silent 409-on-retry).
2. Home: wire Continue card & learning-path nodes to LessonPlayerPage.
3. Quran reader: fetch ayahs from API w/ fallback + dark-theme contrast.
4. Qibla: real GPS + magnetometer compass (geolocator + flutter_compass).
5. Recitation: record WAV 16kHz to match backend; raised API/upload timeouts.
6. Tasbih: added header settings (gear) icon.
7. Onboarding: persist isOnboarded immediately.

## Session 2026-07-13 (commit dd3cdb9)
- Rebuilt APK v1.0.1+6, committed + pushed to origin/main.
- Known issues:
  - APK (65.7MB) > GitHub 50MB warning → consider Git LFS.
  - Some plugins (haptic_feedback, package_info_plus, share_plus) still use Kotlin
    Gradle Plugin; future Flutter versions may fail to build. Plan to migrate.
  - Push needs a GitHub token (no credential helper configured).

## Session 2026-07-13 (commit <TBD>) — 5 bug fixes
Built APK v1.0.2+7 (version_code 7). Fixed:
1. **Profile/Home progress mismatch** — `profile_page.dart` hardcoded
   `_totalXp=1240`, `_currentStreak=7` etc. Now fetches real `/me` + `/me/stats`
   from backend (defaults to 0 for new users). This was the "old cache" bug.
   NOTE: signup/login already call `clearProgressCache()`; root cause was the
   hardcoded values, not storage.
2. **Start Journey button dead** — `home_page._openLesson` returned early when
   the server sent no path nodes. Now always navigates (falls back to
   `LessonListPage` when no lesson/node is available).
3. **Ayat blank screen** — backend returns a JSON array of `AyahOut` (keys
   match `AyahModel`/`WordModel`). Made `corpus_repository.getAyahs` tolerant of
   wrapped shapes (`ayahs`/`data`/`items`) so the reader never gets an empty list.
4. **Recitation no-sound / analysis-failed** — audio play errors were swallowed
   (`catch (_)`); now surfaces a SnackBar. Analysis failures now show the real
   HTTP status code + error_code from `ApiException` for debugging.
5. **Qibla wrong (reported 261°, showed 280°)** — formula is CORRECT: 280.07°
   is the true-north bearing for Mumbai (verified with haversine calc). Kept the
   formula; improved GPS to `LocationAccuracy.best`. Do NOT change 280→261.

## Open tasks / TODO
- Push needs a GitHub token (no credential helper configured).
- Consider Git LFS for the large APK.
- Verify backend is reachable (VPS auto-shuts off) before testing network calls.

## Session 2026-07-13 (commit <TBD>) — 3 more bug fixes (v1.0.3+8)
From screenshots 1000115565/66/67:
1. **Quran screen completely grey** — In release builds a widget that throws
   during build shows the framework's BLANK GREY ErrorWidget. Added a global
   `ErrorWidget.builder` in `main.dart` that renders the exception + stack
   visibly (no more silent grey). Need the actual stack trace (or re-test) to
   pinpoint the exact throw in the reader; layout itself (Expanded/Stack) is
   correct.
2. **Recitation analysis HTTP 405** — ROOT CAUSE was INFRA, not frontend: the
   `recitation_api` service is separate from `core_api`. nginx's HTTPS (:443)
   block was missing `location /v1/recitations/ { proxy_pass http://recitation_api; }`
   (the HTTP :80 block had it). So `POST /v1/recitations/upload` hit `core_api`
   (which only has `GET /{session_id}`) → 405. FIXED in `infra/nginx.conf`
   (both server blocks). The mobile already uses POST correctly. NOTE: nginx
   change requires **redeploying the VPS** (docker compose restart).
3. **Audio "0 source error"** — `audioCdnUrl='https://audio.qari.app'` does not
   resolve. The backend returns a real per-ayah `audio_url` (quran.com CDN).
   Recitation "Listen First" now fetches that via `CorpusRepository.getAyah`
   and plays it; also logs the URL in `AudioService._playUrl`. Reader already
   preferred `ayah.audioUrl`.
