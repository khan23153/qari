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

## Session 2026-07-13 (v1.0.4+9) — screenshot batch 1000115573-576 triage
Screenshots 1000115573 (MaterialLocalizations null + TextField), 5574 (audio
"0 source error"), 5575 (analysis HTTP 405), 5576 (red UI error box in module
screen). Findings:
1. **Issue 1 (MaterialLocalizations null on TextField)** — NOT a missing
   MaterialApp: root `QariApp` already wraps in `MaterialApp` with
   `localizationsDelegates` (main.dart). All TextFields are descendants of it.
   Hardened the loading + error `MaterialApp`s in main.dart to also provide
   `DefaultMaterialLocalizations`/`DefaultWidgetsLocalizations` delegates so
   early/error states can't hit this class of error.
2. **Issue 2 (red error box, module screen)** — `ErrorWidget.builder`
   (main.dart) already surfaces the real exception + stack. Added a
   `debugPrint` there so the failing child widget is identifiable from
   `flutter logs`/terminal. Could NOT pinpoint the exact widget without the
   device console output (no device here). The lesson/module screens
   (lesson_list_page, lesson_player_page, quiz_widget, grammar_card_widget)
   are null-safe on inspection.
3. **Issue 3 (audio "0 source error")** — ALREADY FIXED in 43849ce: per-ayah
   URL fetched from backend and logged at recitation_page.dart:99 before play.
   No change needed.
4. **Issue 4 (analysis HTTP 405)** — PREMISE WRONG: mobile already sends
   `POST` (api_client.dart `uploadFile` → `_dio.post`). The 405 was INFRA:
   nginx HTTPS :443 block lacked `location /v1/recitations/ { proxy_pass
   http://recitation_api; }`. Fixed in infra/nginx.conf (43849ce) but requires
   **VPS redeploy** (docker compose restart). Do NOT change client to GET/POST
   again — it is already POST.

Next: rebuilt APK v1.0.4+9 (committed locally, NOT pushed — needs GitHub
token). Still need to **redeploy the VPS** for the 405 fix to take effect.

## Session 2026-07-13 (v1.0.5+10) — device logs + actual repro
User pasted real device error text. Key findings:
1. **Issue 2 (module red box) ROOT CAUSED & FIXED** — it was NOT
   MaterialLocalizations. `GrammarCardWidget._UnderlineIndicator` drew a
   single-sided `Border` with `strokeAlign: BorderSide.strokeAlignCenter`,
   which is invalid for non-uniform border colors → throws during PAINT of the
   lesson concept screen. FIXED in grammar_card_widget.dart (removed
   strokeAlignCenter). Reproduced + verified with a widget test that drives
   LessonListPage → lesson → concept → fill-blank quiz.
2. **Issue 1 (MaterialLocalizations null on TextField)** — could NOT reproduce:
   the fill-blank `TextField` builds fine under `MaterialApp` in tests, and
   `appLocaleProvider` is always `Locale('en')` (in supportedLocales), so
   `DefaultMaterialLocalizations` always resolves. Likely a stale device build.
   If it recurs on v1.0.5+10, the new copyable ErrorWidget will show the exact
   cause.
3. **ErrorWidget.builder** updated per user request: now returns
   `Material`+`SafeArea`+`SingleChildScrollView`+`SelectableText` of
   `details.exceptionAsString()` + `details.stack`. Lets them long-press to
   copy the error. (Note: `SelectableText` needs MaterialLocalizations, which
   the root MaterialApp always provides — safe here.)

Open items from device paste:
- **405 STILL shows on device** despite "already in VPS" claim — nginx fix
   likely NOT actually redeployed, or recitation_api container down. Needs
   `docker compose restart` on VPS / verify recitation_api is up.
- **Audio (0) Source error** on "Listen First" — just_audio can't load the
   backend `audio_url`. URL is logged at recitation_page.dart:99; need the
   logged URL to tell if it's a bad/blocked/CORS URL vs format issue.

## Session 2026-07-13 (v1.0.6+11) — MaterialLocalizations crash ROOT CAUSED
User pasted device screenshots: Home (RefreshIndicator) + a TextField screen
both threw `Null check operator used on a null value` from
`MaterialLocalizations.of`. Previous v1.0.5+10 note wrongly concluded this was
a stale build / "locale is always en". It was NOT stale — real root cause:

- **ROOT CAUSE**: `main.dart` `MaterialApp`s used
  `DefaultMaterialLocalizations.delegate`, which supports **English only**.
  But the app lets the user pick Urdu/Arabic (`locale: locale` in main.dart:236,
  set from stored language in `_checkAuthStatus`). For `ur`/`ar`, Flutter cannot
  resolve `MaterialLocalizations` → `MaterialLocalizations.of` returns null →
  the `!` null-check in `RefreshIndicator` (home tab) and `TextField`
  (surah search / ask-scholar / root-explorer) throws. The Urdu text on the
  screenshots is the giveaway that locale = ur.
- **FIX**: switched all 3 `MaterialApp`s in `main.dart` (loading splash,
  error fallback, and main) to `GlobalMaterialLocalizations.delegate` +
  `GlobalWidgetsLocalizations.delegate` (from `flutter_localizations`, already
  a dependency), which support ur/ar/en. Added `import
  'package:flutter_localizations/flutter_localizations.dart';`.
- Rebuilt APK v1.0.6+11 (version_code 11). Output
  `mobile/build/app/outputs/flutter-apk/app-release.apk` → copied to
  `releases/app-release.apk`. `releases/app_release.json` bumped to 1.0.6/11.
- NOT pushed (needs GitHub token). Does NOT require VPS redeploy (frontend-only).

CORRECTION to earlier note: locale is NOT always `Locale('en')` — it follows
the user's selected language (en/ur/ar), so any widget relying on
`MaterialLocalizations` will crash on non-English locales unless the Global
delegates are used.

## Session 2026-07-13 (v1.0.7+12) — RTL flip regression fixed
After v1.0.6+11 (Global delegates), the whole UI flipped to RTL. ROOT CAUSE:
switching to `GlobalWidgetsLocalizations` made Urdu/Arabic localize correctly,
and those locales are RTL — so the entire app mirrored. This is *correct*
behavior for ur/ar, but the user wants English to stay LTR and RTL only when
ur/ar is explicitly selected.
- FIX in `main.dart`: kept `locale: locale` (dynamic, respects selected
  language) and added a `builder` that wraps the app in `Directionality`:
  LTR for English, RTL only for `ur`/`ar` (helper `_isRtl(Locale)`). Also set
  `locale` + same `Directionality` builder on the loading `MaterialApp`
  (which previously had no `locale`). `AppLanguage.textDirection` is the source
  of truth (en=LTR, ur/ar=RTL).
- Rebuilt APK v1.0.7+12 (version_code 12); copied to `releases/app-release.apk`;
  `releases/app_release.json` bumped to 1.0.7/12.
- Pushed to origin/main with the user-supplied GitHub token (inline, not stored).

## Session 2026-07-13 (v1.0.8+13) — Quran reader blank screen fixed
Symptom: tapping a surah in the Quran tab opened an empty screen (no ayahs).
- ROOT CAUSE: `QuranReaderPage._loadAyahs` set `_isLoadingAyahs=true` and the
  build showed a full-screen `CircularProgressIndicator` until the network call
  resolved. The backend VPS (20.197.40.13) is frequently down/filtered, so the
  Dio request can sit until the ~90s `apiTimeoutSeconds` → the page looked blank
  for a long time. Data shapes (AyahOut/WordBrief) do match AyahModel/WordModel,
  and the error path already falls back to sample ayahs — the blank was purely
  the loading state, not missing data.
- FIX in `quran_reader_page.dart`: seed `_ayahs` with `_generateSampleAyahs`
  in `initState` so the first frame has content; render the `ListView` (with a
  thin `LinearProgressIndicator` at top while loading) instead of a spinner;
  on network failure keep the current ayahs (don't clobber with sample); show a
  friendly "No ayahs found" only if truly empty. Screen is now never blank.
- Rebuilt APK v1.0.8+13 (version_code 13); copied to `releases/app-release.apk`;
  `releases/app_release.json` bumped to 1.0.8/13.
- Pushed to origin/main with the user-supplied GitHub token (inline, not stored).

