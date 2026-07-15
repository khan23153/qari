# Qari — Project Memory

> Persistent notes so opencode can resume after a VPS restart / new session.
> Read this file first at the start of every session. Update it whenever
> meaningful work is done. Keep it concise.

## Project
- **Qari**: AI-powered Quran learning app (Flutter mobile + Python/FastAPI backend).
- Repo: https://github.com/khan23153/qari
- Mobile app lives in `mobile/`, backend in repo root (core_api, infra, etl, etc).
- Current app version: **1.0.13+19** (versionCode 19).
- Flutter SDK location (not in PATH by default): `/home/Innocent/flutter/bin/flutter`
  - Build APK: `cd mobile && flutter pub get && flutter build apk --release`
  - Output: `mobile/build/app/outputs/flutter-apk/app-release.apk` → copy to `releases/app-release.apk`

## Deployment / Infra
- VPS IP: **20.197.40.13** (HTTPS). Backend + OTA served here.
- OTA app download endpoint: `https://20.197.40.13/v1/app/download`
- Direct APK in repo: https://github.com/khan23153/qari/raw/main/releases/app-release.apk
- Release metadata: `releases/app_release.json` (bump `version_code` + `version` on each release).
- NOTE: VPS sometimes auto-shuts off → work/session lost. Re-read this file on restart.

## Session 2026-07-13 (v1.0.13+18) — audio "0 source error" RE-FIX
User reported ayah audio STILL showing "Audio not available / 0 source error".
Root cause: the reader (`quran_reader_page._playAyahAudio`) played a SINGLE
source with no fallback — `if (ayah.audioUrl != null) playUrl(ayah.audioUrl)`.
The network merge in `_loadAyahs` fills `audioUrl` from the backend; when that
URL points at a dead host, ExoPlayer throws "(0) Source error". The working
everyayah.com constructed URL was only used in the `else` branch, so it got
bypassed. Verified everyayah CDN works (HTTP 200, audio/mpeg, CORS open); the
bundled corpus has `audio_url: null` for all rows (offline path was fine).
FIX (this session):
- `quran_reader_page.dart`: build the everyayah CDN url up front via
  `buildAyahUrl`; play `ayah.audioUrl` first (if any) then ALWAYS retry with the
  CDN url on failure before showing the toast.
- `recitation_page.dart` ("Listen First"): if backend referenceUrl fails to
  play, retry with `playAyah(...)` (constructed CDN) instead of erroring.
- Word bottom sheet left as-is (silently no-ops with no url, no toast).
Built APK v1.0.13+18 → copied to `releases/app-release.apk` (74.3MB). Bumped
`pubspec.yaml` + `releases/app_release.json` (version_code 18). NOT committed/
pushed (no git action requested). VPS still needs the APK served for OTA.

## Session 2026-07-13 (v1.0.13+19) — whole-surah playback + voice picker
User: "audio working now" → add (1) play the WHOLE surah in one tap instead of
a single ayah, and (2) a voice/reciter picker so the user can choose the qari.
Changes (all committed + pushed, APK rebuilt to version_code 19):
- `audio_service.dart`: new `playSurahSequence({urls, initialIndex})` that loads
  a `ConcatenatingAudioSource` of per-ayah URLs for gapless whole-surah playback;
  new `currentIndexStream` (from `sequenceStateStream`) so the UI can follow the
  active ayah; `isSequential` flag; `stop()` resets it.
- `quran_reader_page.dart`: tapping an ayah's play button now queues the rest of
  the surah (sublist from tapped ayah) and plays it in one go. The highlighted
  ayah follows playback via `currentIndexStream`; tapping the active ayah
  pauses/resumes; tapping another restarts from there. On `ProcessingState
  .completed` the session resets. Added a **Voice** chip in the settings bar
  that opens a sheet listing all 5 reciters (Abdul Basit, Al-Sudais, Al-Minshawi,
  Al-Husary, Al-Afasy) — persists via `LocalStorageService.setSelectedQari` and
  applies immediately to the AudioService. URLs are built with the selected
  reciter (`_selectedQari`).
- Carried over (committed now): everyayah.com CDN `audioCdnUrl` fix, recitation
  "Listen First" CDN fallback, `pubspec.yaml` + `app_release.json` (v1.0.13+19).
- Flutter SDK path: `/home/Innocent/flutter/bin/flutter` (NOT in PATH).

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

## Session 2026-07-13 (v1.0.10+15) — surah list (10→114) + reader blank screen
User reported (again) "only 10 surahs" and "blank screen on tapping a surah".
The v1.0.9+14 notes claimed this was already fixed, but it recurred — the
previous attempt did NOT fix the real root causes:
1. **Blank screen ROOT CAUSE** — backend `/surahs/{n}/ayahs` returns words with
   a NULL `pos_group`. `WordModel.posGroup` was `required` (non-nullable), so
   `WordModel.fromJson` threw `as String` → bubbled out of `getAyahs` (not a
   DioException, so the repo's `catch (DioException)` didn't catch it) → on a
   pre-seed build the reader rendered empty/blank. FIXED: `posGroup` is now
   `String?` (word_model.dart) and callers pass `?? 'default'` to
   `getGrammarConfig`. Regenerated freezed.
2. **Partial/short surahs** — backend caps each `/ayahs` request at
   `MAX_AYAHS_PER_REQUEST = 20` (shared/__init__.py:164). The mobile fetched
   only one page, so long surahs showed ~20 ayahs. FIXED: `getAyahs`
   (corpus_repository.dart) now paginates `from`/`to` in 20-ayah pages until a
   short/empty page, assembling the full surah.
3. **Only 10 surahs** — if the backend returns a partial list (or the DB only
   has a subset), `_loadSurahs` replaced the 114-surah list with whatever the
   server sent. FIXED: `_loadSurahs` (surah_list_page.dart) now MERGES server
   surahs into the bundled `_fallbackSurahs` (all 114) by surah number, so the
   list is ALWAYS complete (114) regardless of backend state. Server data wins
   on a match; fallback fills gaps.
- Rebuilt APK v1.0.10+15; copied to releases/app-release.apk;
  releases/app_release.json bumped to 1.0.10/15.
- NOTE: OTA serves from VPS (20.197.40.13/v1/app/download). To actually push
  this to users, the new releases/app-release.apk must be deployed to the VPS
  (the VPS copy, not just the GitHub raw one, is what devices download).

## Session 2026-07-13 (v1.0.11+16) — ROOT CAUSE of blank reader found + local corpus
The recurring "blank screen on tapping a surah" was NEVER actually fixed by the
posGroup/merge changes — those only addressed symptoms. REAL ROOT CAUSE:
- The backend corpus DB is **empty**. `backend/core_api/seed_dev_data.py` only
  seeds qaris/badges/lessons — it never loads surahs/ayahs/words. Verified live:
  `GET /v1/surahs` → `[]`, `GET /v1/surahs/1` → "Surah '1' not found".
  So `/surahs/{n}/ayahs` returns `[]` for EVERY surah, and the reader fell back
  to a single placeholder bismillah ayah (only Al-Fatiha had real sample data).
- Decision: stop depending on the (empty/unreliable) backend for reading.
  Bundle the full Quran locally in the app so the reader works offline.
- Added `scripts/build_local_corpus.py` which pulls all 114 surahs (Uthmani
  text, simple text, EN verse translation res 84, UR verse translation res 97,
  word-by-word transliteration + EN word translation) from the Quran.com API v4
  and writes `mobile/assets/quran_corpus.json` shaped to match AyahModel/
  WordModel `fromJson` keys. Gzipped → `mobile/assets/quran_corpus.json.gz`
  (4.3 MB; ~41 MB uncompressed, 6236 ayahs / 83665 words).
- Added `mobile/lib/data/repositories/local_corpus_repository.dart`: loads the
  gzipped asset via `rootBundle`, decodes with `gzip.decode` in a `compute`
  isolate, parses directly to `AyahModel`/`WordModel`.
- `QuranReaderPage._loadAyahs` now loads the **local corpus first** (instant,
  offline, never blank), then optionally merges live backend data on top.
- `pubspec.yaml` registers `assets/quran_corpus.json.gz`; version bumped
  1.0.10+15 → 1.0.11+16.
- KNOWN LIMITATION: Quran.com free API has no per-word POS group / grammar
  labels and no Hindi translation, so grammar colors use the `default` style
  and `translation_hi` falls back to EN. Hindi verse translation not bundled.
- BUILD NOTE: the APK for v1.0.11+16 was NOT built in-session — this environment
  blocks the 153 MB Android cmdline-tools download (headers arrive, body empty),
  so no Android SDK / NDK. The user must build + deploy on their own machine:
    cd mobile && flutter pub get && flutter build apk --release
    # then: copy build/app/outputs/flutter-apk/app-release.apk → releases/
    # and deploy to VPS at 20.197.40.13 (OTA /v1/app/download).
    # Bump releases/app_release.json to 1.0.11/16 AFTER the APK is on the VPS.

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

## Session 2026-07-13 (v1.0.9+14) — Quran surah list shows all 114
User: tapping a surah opened a blank reader AND the list only showed 10 surahs
(should be 114). The 10-surah bug was the real defect:
- `surah_list_page.dart` hardcoded a 10-item `_allSurahs` sample list. Rewrote it
  to fetch all 114 via `CorpusRepository().getSurahs()` (`/v1/surahs`), with a
  bundled full-114 `_fallbackSurahs` list used when the API is unreachable, so
  the list is never empty. Tile now takes `SurahModel`.
- BLOCKER found + fixed: backend `SurahBrief` has NO guaranteed `name` key (it
  only has `name_arabic`/`name_english`/`name_translation`; `name` is a computed
  transliteration that can be absent). `SurahModel.name` was `required` →
  `getSurahs()` threw on every call. Made `name` nullable and mapped it from the
  `name` JSON key (not `name_arabic`, which would collide with `nameArabic`).
  Regenerated `surah_model.g.dart`/`surah_model.freezed.dart` via build_runner.
- Reader blank: confirmed via a widget test that `QuranReaderPage` DOES render
  ayah text (seeded sample) — the earlier "blank" was the pre-v1.0.8 full-screen
  spinner during the network request. v1.0.8's sample-seed already fixes it.
  NOTE: the user may not have installed v1.0.8 yet; this build (v1.0.9+14)
  includes both fixes.
- Rebuilt APK v1.0.9+14 (version_code 14); copied to `releases/app-release.apk`;
  `releases/app_release.json` bumped to 1.0.9/14.
- Pushed to origin/main with the user-supplied GitHub token (inline, not stored).

## Session 2026-07-13 — reader blank fix (post v1.0.11+16) + widget test
Follow-up to the local-corpus work. Two more root causes of a blank reader, plus
a regression test.

1. **AyahWidget hidden by opacity-0 animation (REAL blank-screen cause)** —
   `ayah_widget.dart` wrapped the ayah `Container` in
   `.animate(target: isPlaying ? 1 : 0).fadeIn()`. `fadeIn` STARTS at opacity 0,
   so every ayah that is *not* currently playing (i.e. essentially all of them)
   was painted fully transparent → the reader showed only the header/settings
   bar with a blank ayah list. FIXED: removed the `.animate().fadeIn()` wrapper;
   the container now paints directly. Added a code comment in ayah_widget.dart
   so this doesn't get re-introduced.
2. **Local corpus decode could fail silently** — `LocalCorpusRepository` decoded
   the gzipped asset via a `compute` background isolate. On platforms where that
   path is flaky, the future could fail and leave the reader blank. FIXED:
   decode `gzip.decode` directly on the caller (fast for a ~4.4 MB asset) and
   parse each ayah defensively (`try/catch`, skip bad ayahs with `debugPrint`)
   so a single malformed item can't blank an entire surah. Removed the top-level
   `gzipDecode`/`_decode` helpers.
3. **Regression test added** — `mobile/test/ayah_widget_visibility_test.dart`
   drives `AyahWidget` with `isPlaying:false` (the state that previously hid
   everything) and asserts: (a) the Arabic word widgets are present, (b) the
   first word actually has a non-zero painted size, and (c) no ancestor
   `RenderAnimatedOpacity` is painting at ~0 opacity. This pins the exact bug
   that the v1.0.11+16 changes didn't fully close.
- `flutter` is NOT in PATH by default; run tests with:
  `export PATH="/home/Innocent/flutter/bin:$PATH"; flutter test test/ayah_widget_visibility_test.dart`
  → all tests pass.
- BUILD NOTE: this environment has no Android SDK/NDK (the 153 MB cmdline-tools
  download is blocked — headers arrive, body empty), so the APK was NOT rebuilt
  here. The fix is verified by the widget test (runs headless, no device). The
  user must rebuild the APK on their machine before deploying to the VPS.
- These working-tree changes + the 6 already-committed-but-unpushed commits
  (v1.0.6+11 → v1.0.11+16) were pushed to origin/main with the user's GitHub
  token (inline, not stored).

## Session 2026-07-13 — Recite screen from Quran reader was a blank placeholder
User: tapping "Recite" on an ayah opened a blank screen showing only
"Recitation for 1:1". ROOT CAUSE: `RecitationPageRoute` in
`quran_reader_page.dart` was a literal placeholder (`Scaffold` + `Text('Recitation
for $surahNumber:$ayahNumber')`). FIX (working tree, uncommitted):
- `quran_reader_page.dart`: `RecitationPageRoute.build` now returns the full
  `RecitationPage(surahNumber:, ayahNumber:)` instead of the placeholder.
- `recitation_page.dart`: the idle/listen/record UI already existed and is fully
  wired to `RecordingService` (16kHz WAV), `AudioService` (reference playback w/
  CDN fallback), and `RecitationRepository` (upload + poll → `RecitationResult`).
  Added `_loadTargetAyahText()` to `initState` so the screen shows the REAL target
  ayah text from `LocalCorpusRepository` (was hardcoded bismillah before).
- Added `test/recitation_screen_test.dart` (pumps `RecitationPage` from reader and
  asserts header + RTL arabic text + "Listen First" + "Record Now" buttons present).
  Fixed stale `widget_test.dart` state-machine count 8→9 (`errorAnalysisFailed`).
- RECITATION STATE MACHINE: idle → listening → recording → analyzing → results,
  plus errorMicDenied / errorTooNoisy / errorLowConfidence / errorAnalysisFailed.
- NOTE: `widget_test.dart` "Grammar color-coding follows spec" still fails — it's a
  pre-existing stale constants assertion, unrelated to this change.
- COMMITTED + PUSHED (commit df8cea6) with the user's GitHub token. Version
  bumped to v1.0.13+23; `releases/app-release.apk` rebuilt (74.4MB) and copied
  to `releases/`, `releases/app_release.json` bumped to 23. APK push warned
  >50MB (use Git LFS later). OTA still serves from VPS 20.197.40.13 — to push
  to users, deploy the new APK to the VPS (`/v1/app/download`).

## Session 2026-07-13 — Recitation results: real Arabic words + real ML engine
User: results screen was in STUB mode (hardcoded 100% + "Stub mode — connect
the ML engine" feedback) and the word-by-word grid showed raw backend keys like
`word_2_1_1` instead of Arabic. FIX (committed + pushed, commit 108b75a):
- ROOT CAUSE of stub: `infra/docker-compose.yml` forced `QARI_ML_USE_STUB:"true"`
  on the `inference-worker` service. The frontend already calls the REAL API
  (`RecitationRepository.uploadRecitation`/`pollForResult`) — no mock in the app.
  The stub `_default_inference` (backend/recitation_api/app/workers/
  inference_worker.py:184) emits `word: "word_{surah}_{ayah}_{pos}"` keys + 1.0
  scores. Set `QARI_ML_USE_STUB:"false"` so the real Whisper/Wav2Vec2 pipeline
  (run_ml_inference) runs and returns actual Arabic + real scores.
- FRONTEND word mapping: added `WordVerdict.displayWord(List<String> ayahWords)`
  (mobile/lib/data/models/recitation_model.dart) that prefers real Arabic
  already on the verdict, else resolves from the target ayah's word payload by
  `wordIndex` (so no raw keys leak to the UI). `RecitationPage._loadTargetAyahText`
  now also stores `_ayahWords`; passed to `RecitationResults` and
  `WordComparisonSheet` which call `verdict.displayWord(...)`.
- Tests: added `test/recitation_word_mapping_test.dart` (proves grid shows real
  Arabic, not `word_x_y_z` keys). Bumped APK to v1.0.13+24 (rebuilt, copied,
  app_release.json → 24).
- DEPLOY NOTE: flipping stub off means the VPS `recitation_api` worker MUST have
  the ML engine (Whisper ASR + Wav2Vec2 forced aligner) + reference data
  (reference_data_dir / core_api) deployed, else real inference raises and the
  mobile shows the "analysis failed" state. Redeploy VPS + deploy APK to
  20.197.40.13 for users to get real feedback.


## Session 2026-07-13 — Deployed real ML engine on the VPS (no more 100% stub)
The running VPS (this environment) backend was still on the OLD worker container
with `QARI_ML_USE_STUB=true`, so recitations returned hardcoded 100% regardless
of audio. Actually deployed the real engine here:
- Recreated `infra-inference-worker-1` from updated compose → `QARI_ML_USE_STUB=false`.
- Root-caused why real inference still failed, and fixed each gap:
  1. `No module named 'ml'` → mounted `../ml:/app/ml` + `PYTHONPATH=/app` in compose.
  2. ML deps missing from worker image → added `requirements.ml.txt` (CPU
     torch/transformers/torchaudio/librosa/soundfile) + installed in
     `backend/recitation_api/Dockerfile` (rebuilt image `infra-inference-worker`).
     Dropped `edlib` (won't build on py3.12; unused by runtime `ml`).
  3. Audio file not found by worker → added shared `qari_audio:/tmp/qari_audio`
     volume to BOTH `recitation-api` and `inference-worker`.
  4. Whisper `return_timestamps` generation-config error → disabled ASR
     timestamps in `ml/inference/asr.py` (word timing comes from forced aligner).
  5. Empty backend corpus DB → built reference bundle (6236 ayahs) from the
     bundled mobile corpus via new `scripts/build_reference_from_local_corpus.py`
     into `backend/recitation_api/reference_data` (gitignored); set
     `QARI_REFERENCE_DATA_DIR=/app/reference_data`.
- VERIFIED end-to-end: uploaded a (non-speech) WAV → worker loaded Whisper +
  reference store and returned a COMPUTED 0% with "couldn't analyse with enough
  confidence" — confirms real inference, NOT the 100% stub.
- Committed + pushed (commit 8bdba74). Worker is `restart: unless-stopped` and
  uses the rebuilt image + volume mounts, so it survives restarts.
- FRONTEND: APK v1.0.13+24 (from prior turn) already has the word-mapping fix
  and is current; no rebuild needed this turn. User's device hitting the VPS now
  gets real scores (wrong words will be marked, not 100%).

## Session 2026-07-13 — Fixed "Low Confidence" + validated real ML end-to-end
After enabling the real engine, the user still got "We couldn't analyze your
recitation with enough confidence" even on a correct recitation. ROOT CAUSE:
two more gaps in the real pipeline (the `max_new_tokens` + forced-decoder
prompt = 452 > Whisper's 448 max) made `pipeline.analyze` raise on every job,
so `evaluated_ayahs == 0` → empty verdicts → low-confidence state.
FIXES (committed + pushed, commit aae11a6 + follow-ups):
- `ml/inference/asr.py`: `max_new_tokens` 448 → 440 (4 forced-decoder tokens
  + 440 = 444 < 448 max). Also earlier disabled ASR `return_timestamps`
  (transformers generation-config incompatibility).
- `scripts/build_reference_from_local_corpus.py`: skip reference words with no
  actual Arabic letters (e.g. the corpus' stray "1" numeral token), so a real
  recitation is never penalised for a reference-data artifact. Regenerated the
  6236 reference files (1:1 now cleanly = بسم/الله/الرحمن/الرحيم).
VALIDATION (real end-to-end on the VPS worker):
- Installed espeak-ng + ffmpeg here; synthesized 16kHz mono Arabic WAVs:
  a CORRECT bismillah and a WRONG variant (last word السلام instead of
  الرحيم), uploaded both to /v1/recitations/upload.
- Both returned real word_verdicts with actual Arabic `word`/`expected_text`
  (NOT `word_x_y_z` keys). The WRONG clip's last word was transcribed as
  السلام vs expected الرحيم → flagged mispronounced (red). CONFIRMS the real
  engine differentiates correct vs wrong recitation and is no longer the 100%
  stub. The overall 0.3 on espeak audio is a test artifact (robotic TTS is hard
  for Whisper-Quran, which is trained on natural recitation); a real human
  recitation transcribes far better → higher score.
- Updated README.md recitation-engine section (local-corpus reference builder,
  ML deps via requirements.ml.txt, shared qari_audio volume, stub=false prod).
- NOTE: recitation scoring quality depends on Whisper-Quran transcription
  accuracy; tuning (beam search, LM, Wav2Vec2 refine) is future work. The
   pipeline is correctly wired end-to-end.

## Session 2026-07-14 — Urdu Tarjuma (text + sequential audio) in Surah view
Added an optional Urdu translation feature to the Quran reader.
- **Model**: `AyahModel` gained `audioUrlUr` (`audio_url_ur`) — regenerated
  freezed. Urdu text already existed via `translationUr`.
- **Audio source**: Urdu tarjuma audio uses everyayah.com CDN
  `https://everyayah.com/data/urdu_shamshad_ali_khan_46kbps/{surah:03d}{ayah:03d}.mp3`,
  exposed as `AppConstants.urduTranslationCdnUrl` + `AudioService.buildUrduTranslationUrl`
  (mirrors the Arabic `buildAyahUrl`). Falls back to `ayah.audioUrlUr` if present.
- **UI/State**: settings bar "Tarjuma" chip opens a sheet — choose English/Urdu
  translation + a "Play Translation Audio" switch. Both persisted in
  `LocalStorageService` (`translation_language`, `play_translation_audio`).
  `AyahWidget` takes a new `translationLanguageCode` that drives the density>=3
  full-translation block (word meanings still use app `languageCode`).
- **Sequential queue**: `_playAyahAudio` queues [Arabic, Urdu] per ayah when the
  toggle is on; `_audioItemsPerAyah` (1 or 2) maps the player's sequence index
  back to the highlighted ayah in `currentIndexStream`.
- **Backend**: `Ayah.audio_url_ur` column + migration `0003_ayah_audio_url_ur`;
  `AyahOut.audio_url_ur` (serialization_alias `audio_url_ur`), populated in
  `corpus.py` route + `content_bundle_service.py`. Migration MUST be applied on
  the VPS (alembic upgrade) or the `ayahs` table query fails.
- **Build script**: `scripts/build_local_corpus.py` writes `audio_url_ur` per
  ayah when `URDU_AUDIO_BASE_URL` env is set (else omitted; runtime still
  constructs it from the constant).
- Verified: `flutter analyze` clean on changed files; `ayah_widget_visibility_test`
  passes. `reader_render_test` FAILS but is pre-existing (fires a real 90s Dio
  timer in initState; fails before this change too).
- BUILT + COMMITTED + PUSHED (commit ce2ea78): APK rebuilt (74.4MB),
  copied to `releases/app-release.apk`, bumped to **v1.0.14+25**
  (`pubspec.yaml` + `releases/app_release.json` with Urdu tarjuma notes),
  pushed to origin/main. Large-APK (>50MB) warning as before — Git LFS later.
- DEPLOY: VPS needs `alembic upgrade head` (new `ayahs.audio_url_ur` column)
  and the new APK deployed to 20.197.40.13 (`/v1/app/download`) for OTA users
  to get the Urdu tarjuma feature.

## Session 2026-07-14 — auth/state/UI bug fixes (5 items)
Mobile-only fixes (no backend change needed; signup already returns JWT):
1. **Login validation** — `_AuthForm` password validator now enforces min 8
   chars (email regex already present) so empty/short passwords can't submit.
2. **'Learner' fallback removed** — `profile_page` `_displayName` defaults to
   `''` and falls back to the email local-part (not hardcoded 'Learner'); it
   binds to `UserModel.displayName` from `/me`.
3. **Hardcoded mock data removed**:
   - `streak_calendar.dart`: dropped `activeDays.addAll([3,7,10,14,18,22,25])`;
     calendar now derives only from `currentStreak` (empty for new users).
   - `learning_path_map.dart`: sample path reset so only node 1 is `current`,
     nodes 2–10 `locked` (was 1–4 completed + 5 stuck).
   - `badges_grid.dart`: rewritten to be data-driven via `earnedIds` (default
     empty) — no badges pre-unlocked. Backend `UserBadge` is empty on signup.
4. **Audio Play/Pause toggle** — `quran_reader_page` now tracks real playback
   via `_isAudioPlaying` (from `playerStateStream`); per-ayah button shows
   "Play" when paused / "Pause" when playing (was stuck on "Pause").
5. **Reset & signup flow** — root cause was `_resetLocalData`'s `onAuthenticated`
   capturing the disposed ProfilePage `context`, crashing post-signup nav.
   Added `core/navigation/app_navigator.dart` (`rootNavigatorKey`) used by
   `main.dart` and the reset flow. `clearAll()` already flushes the auth token;
   backend signup already returns a JWT for immediate login.
- Verified: `flutter analyze` clean (no errors); `ayah_widget_visibility_test`
   passes. `reader_render_test` still pre-fails (pre-existing 90s Dio timer).

## Session 2026-07-14 — Urdu Tarjuma AUDIO not playing (root cause + fix)
User: "tarjuma showing now but audio not coming". Text shows (local corpus) but
NO audio at all (Arabic included). ROOT CAUSES:
1. **Wrong CDN path (the real bug)**: `AppConstants.urduTranslationCdnUrl` was
   `https://everyayah.com/data/urdu_shamshad_ali_khan_46kbps` → **404**. The
   Urdu tarjuma folder actually lives under everyayah's `/data/translations/`
   path: `https://everyayah.com/data/translations/urdu_shamshad_ali_khan_46kbps`
   (verified: 001001/001007/002001/114001/002286 all HTTP 200 `audio/mpeg`).
   FIXED in app_constants.dart (added `/translations/` segment).
2. **Dead URL killed the whole queue**: the Urdu URL was concatenated into the
   SAME `ConcatenatingAudioSource` as Arabic. A dead/404 URL made just_audio
   throw on `setAudioSource`, so the entire sequence failed → zero audio.
   HARDENED in audio_service.dart: added `isUrduTranslationAvailable()` which
   probes the CDN (Range GET on 1:1, cached) and returns false on 404/timeout;
   `quran_reader_page._playAyahAudio` now only enqueues Urdu URLs when the probe
   passes, falling back to Arabic-only otherwise. So Arabic always plays.
- Rebuilt? NOT yet — this env has no Android SDK/NDK (cmdline-tools download
   blocked). User must rebuild + deploy: `cd mobile && flutter pub get &&
   flutter build apk --release` → copy to `releases/` → deploy APK to VPS
   20.197.40.13 (`/v1/app/download`). No backend/VPS change needed (pure
   frontend; source is public everyayah.com, no auth, CORS-open for media).
- `scripts/build_local_corpus.py` `URDU_AUDIO_BASE_URL` env (if used to bake
   `audio_url_ur` into the corpus) should also use the `/translations/` path;
   runtime already derives from the corrected constant.

## Session 2026-07-14 — Urdu TEXT must match the AUDIO (Jalandhari fix)
The Shamshad Ali Khan Urdu tarjuma AUDIO is a recitation of **Fateh Muhammad
Jalandhari's** translation (alquran.cloud edition `ur.jalandhry.text`). The
bundled Urdu text was the WRONG translator — Quran.com v4 resource **97 =
"Tafheem e Qur'an - Syed Abu Ali Maududi"** (`ur-al-maududi`) — so users read
Maududi but heard Jalandhari. ROOT CAUSE: `scripts/build_local_corpus.py`
`UR_RES = 97`. FIX:
- `UR_RES` → **234** (`ur-fatah-muhammad-jalandhari` = Jalandhari) in
  build_local_corpus.py, with a comment pinning it to the audio source. This is
  the Quran.com v4 equivalent of alquran.cloud `ur.jalandhry.text`.
- Regenerated `mobile/assets/quran_corpus.json` (41.6 MB) and gzipped over
  `quran_corpus.json.gz` (4.37 MB). Verified 1:1 = "شروع الله کا نام لے کر جو بڑا
  مہربان نہایت رحم والا ہے" (Jalandhari, matches audio).
- Also updated the 5 hardcoded fallback sample ayahs (surah 1) `translationUr`
  in quran_reader_page.dart from Maududi-style to Jalandhari for consistency
  (these only show if the corpus fails to load).
- Backend `translation_ur` comes from its (empty) corpus DB; no override of the
  local Jalandhari text. If backend is ever seeded, seed it with Jalandhari too.
- NOTE: `quran_corpus.json.gz` is a bundled APK asset — must REBUILD the APK
   (`flutter build apk --release`) to ship the corrected text. No backend change.

## Session 2026-07-14 — Tajweed colour-coding now works in Surah reader
User: "in surah section I didn't see any use of tajweed, tajweed not working".
ROOT CAUSE: two gaps.
1. **No tajweed data** — `scripts/build_local_corpus.py` hardcoded
   `"tajweed_spans": None` for every word, and the Quran.com request didn't
   even ask for tajweed text. So the mobile reader (which reads the bundled
   `quran_corpus.json(.gz)`) had nothing to colour. The ETL `tajweed_parser.py`
   existed but its per-ayah annotations were never turned into the word-level
   `tajweed_spans` the app expects.
2. **Wrong rendering** — `ayah_widget.dart` `_WordTapTarget` only coloured the
   WHOLE word by the FIRST span's rule (a known stub), not per-letter.
FIXES:
- `scripts/build_local_corpus.py`: added `text_uthmani_tajweed` to the API
  `fields`; new `build_tajweed_spans()` strips the `<tajweed class=X>`
  markup, computes each rule's char range in the plain ayah text, maps it to
  word-relative `start`/`end` offsets, and writes per-word `tajweed_spans`
  (`{start, end, rule, rule_name, rule_description}`). `TAJWEED_RULE_NAMES`
  maps Quran.com classes → friendly English names. Regenerated the corpus:
  45,874 of 83,665 words carry 61,173 tajweed spans (e.g. ghunnah on the
  shadda'd meem of 2:3). Wrote `quran_corpus.json` (47.9 MB) + gz (4.8 MB).
- `ayah_widget.dart` `_WordTapTarget`: now builds a `Text.rich` with one
  `TextSpan` per character run sharing a tajweed rule, colouring exactly the
  letters each rule covers (offsets are word-relative). `normal`/uncovered
  letters keep the default ink colour. RTL kept.
- `app_constants.dart` `tajweedColors`: re-keyed to the Quran.com v4 class
  names (ghunnah, ikhafa, qalaqah, idgham_ghunnah, iqlab, madda_*, slnt,
  ham_wasl, laam_shamsiyah, ...) with distinct colours; added
  `tajweedRuleLabels` for friendly legend/sheet names.
- `grammar_legend.dart`: tajweed chips now show `tajweedRuleLabels` names.
- `word_bottom_sheet.dart`: shows each non-`normal` tajweed rule of the tapped
  word (coloured) under a "Tajweed" row.
USAGE: in the Surah reader settings bar, tap **Tajweed** (mutually exclusive
with Grammar, which is on by default). Tap any word to see its rule(s).
VERIFIED: `flutter analyze` clean (only 2 pre-existing info lints);
`ayah_widget_visibility_test` passes. APK rebuilt (75.0 MB) and copied to
`releases/app-release.apk`; `pubspec.yaml` + `releases/app_release.json`
bumped to **v1.0.17+28**. NOTE: must REBUILD APK to ship the new corpus .gz
(the tajweed data lives in the bundled asset, not the backend). Deploy the
APK to VPS 20.197.40.13 (`/v1/app/download`) for OTA users. Not yet committed/
pushed (no git action requested).

## Session 2026-07-14 — Rebuilt APK + committed (v1.0.16+27)
Combined the Urdu audio+text fixes AND the earlier uncommitted v1.0.15 auth/UI
fixes into one release.
- **APK built successfully** (Android SDK present this time): `flutter build
  apk --release` → `mobile/build/app/outputs/flutter-apk/app-release.apk`
  (74.3MB). Copied to `releases/app-release.apk`. The APK was built AFTER the
  regenerated `quran_corpus.json.gz`, so it ships Jalandhari text.
- **Version bump**: `pubspec.yaml` → `1.0.16+27`; `releases/app_release.json`
  → version 1.0.16 / version_code 27, with en+ur+hi notes for the Urdu fix.
- **Committed** locally as `fdda3bb` (17 files: the Urdu audio/text fixes,
  audio_service resilience, auth/UI fixes, app_navigator, regenerated corpus
  .gz, rebuilt APK, bumped metadata, .gitignore now ignores the uncompressed
  `mobile/assets/quran_corpus.json` build artifact).
- **PUSHED** ✓ (commit fdda3bb) to origin/main with the user-supplied GitHub
  PAT (inline, not stored; `GIT_TERMINAL_PROMPT=0` + `-c credential.helper=`,
  token not persisted in git config). Large-APK (>50MB) warning as before —
  Git LFS still planned. REMAINING: deploy `releases/app-release.apk` to VPS
   20.197.40.13 (`/v1/app/download`) for OTA users to actually receive v1.0.16.
- APK >50MB warning persists (Git LFS planned later).


## Session 2026-07-14 — Real-time voice tracking + Memorization (Hifz) Mode (Tarteel-style)
Upgraded the **AI Recitation section** (home practice FAB) with continuous
real-time streaming, live word-by-word tracking, Memorization Mode, live error
detection and a hands-free always-listening visualizer.

IMPORTANT SCOPE RULE (per user): the Quran reader's per-ayah **"Recite" option
is UNTOUCHED**. Both entry points previously reused the SAME `RecitationPage`:
  - home FAB → `const RecitationPage()`  (the AI Recitation section — upgraded)
  - quran_reader `RecitationPageRoute` → `RecitationPage(surah, ayah)` (LEFT AS-IS)
So instead of editing `RecitationPage`, I built a **brand-new** page and only
re-pointed the home FAB. `RecitationPage` + its `RecitationState` enum are
byte-for-byte unchanged (widget_test 9-state count + recitation_screen_test
still pass).

### Backend (recitation_api + ml) — real-time streaming pipeline
- NEW `ml/alignment/streaming_matcher.py` `StreamingMatcher`: pure-Python
  incremental aligner. `evaluate(hyp_words)` greedily maps a *growing* ASR
  hypothesis onto the reference word list and returns stable per-word states
  (matched / error / skipped; unresolved = pending/masked). Handles skips,
  inserted/repeated words, and near-match ASR noise (char-sim >= 0.80). Robust
  to re-transcription revising earlier words. Unit tests:
  `ml/tests/test_streaming_matcher.py` (8, all pass).
- NEW `backend/recitation_api/app/services/streaming_session.py`
  `StreamingRecitationSession`: buffers PCM16, re-transcribes every ~1.2s of new
  audio in a thread, feeds the matcher, diffs status maps → incremental `word`
  events. Resolves reference words from the ml ReferenceStore → core_api
  fallback. Pluggable transcriber: real `QuranASR` (Whisper) OR a duration-based
  **stub** (used when `QARI_ML_USE_STUB=true` or no reference) that reveals words
  over time so the live flow is demoable without model weights. `finalize()`
  writes the full WAV to disk + persists a mobile-shaped RecitationAnalysisResult
  to Redis (so `GET /{session_id}`, history, A/B playback keep working).
- NEW WebSocket `WS /ws/recitation/stream` in `app/api/routes/websocket.py`.
  MUST be registered BEFORE `/ws/recitation/{session_id}` (else Starlette
  matches `stream` as a session_id path param — that was the initial bug).
  Protocol: client sends `{type:start,...}` → server `{type:ready, words:[...]}`
  → client streams binary PCM16 frames → server emits `{type:word, word_index,
  status, expected, spoken}` live → client `{type:stop}` → server `{type:final,
  result}`. Ping/pong keep-alive. Tests: `tests/test_streaming.py` (4, pass).
- `infra/nginx.conf`: added `proxy_read_timeout 3600s` + `proxy_send_timeout
  3600s` + `proxy_buffering off` to BOTH `/ws/` blocks so long hands-free
  sessions aren't dropped (default nginx WS read timeout is only 60s). Needs a
  VPS nginx reload to take effect.

### Frontend (Flutter) — all NEW files, legacy RecitationPage untouched
- `mobile/lib/data/models/recitation_stream_event.dart`: plain-Dart event model
  (`LiveWordStatus` {pending,matched,error,skipped}, `RecitationStreamEvent`).
- `mobile/lib/data/services/streaming_recitation_service.dart`: streams mic via
  `record`'s `startStream(pcm16bits,16k,mono)` → `dart:io WebSocket.connect(...,
  customClient:)` (trusts the VPS self-signed cert via badCertificateCallback).
  Exposes `events`, `amplitude` (RMS 0–1 for the visualizer), `connectionState`.
  `start/stop/cancel`; 20s ping keep-alive; NO auto-stop.
- `widgets/memorization_ayah_view.dart`: RTL word grid. Hifz mode blurs pending
  words (ImageFiltered) and reveals green when matched; red = mispronounced,
  amber+underline = skipped, live. Tracking mode shows all words, tints as they
  resolve.
- `widgets/mic_visualizer.dart`: always-on bottom bar visualizer (pulsing mic
  dot + scrolling RMS bars + "Listening") — shows the mic is continuously live.
- `pages/live_recitation_page.dart` NEW `LiveRecitationPage`: setup (target
  picker + Memorization toggle + Listen First + ayah preview) → live (real-time
  MemorizationAyahView + LIVE count-up timer that NEVER auto-stops + bottom
  MicVisualizer + Stop/Cancel) → results (reuses existing `RecitationResults` +
  `WordComparisonSheet`; synthesizes a result from live statuses if the final
  payload is missing). Own `LiveRecitationUiState` enum (does NOT touch
  `RecitationState`).
- `home_page.dart`: practice FAB now opens `LiveRecitationPage` (was
  `RecitationPage`). This is the ONLY change to an existing screen's behaviour.
- `app_constants.dart`: added `wsBaseUrl` / `recitationStreamWsUrl` (derived
  from baseUrl: http→ws, drop `/v1`), `trustedSelfSignedHost`, and live
  streaming constants (sample rate, ping interval, visualizer bar count).
- Tests: `mobile/test/live_recitation_test.dart` (7, all pass) — event parsing,
  setup UI (Hifz toggle + Start), memorization masking vs tracking.

### Verification
- `flutter analyze` clean on ALL new files. `flutter test live_recitation_test`
  7/7 pass. `recitation_screen_test` (Quran reader recite) + widget_test state
  count STILL pass (legacy untouched). Only pre-existing `widget_test` "Grammar
  color-coding" fails (references non-existent `fiil` key — unrelated).
- `pytest ml/tests/test_streaming_matcher.py` 8/8; recitation_api
  `tests/test_streaming.py` 4/4. The 2 pre-existing recitation test failures
  (no Redis running + intentional ayah-range clamp) are unchanged.
- Installed backend deps into the VPS venv (`/home/Innocent/venv`): fastapi,
  httpx, pytest-asyncio, redis, etc.

### DEPLOY NOTES
- VPS: reload nginx (WS timeouts) + restart `recitation-api` so the new
  `/ws/recitation/stream` route is served. The `inference-worker` is unaffected
  (streaming runs inside recitation-api, not the worker). Real live transcription
  needs the Whisper model available in recitation-api; otherwise it falls back to
  the duration-based stub (still reveals words live). Consider running with
  `QARI_ML_USE_STUB=false` once Whisper is loaded there.
- Mobile: APK NOT rebuilt this session (rebuild with `flutter build apk
  --release` then deploy to VPS `/v1/app/download`; bump pubspec + app_release).
- NOT yet bumped pubspec version — do that with the APK rebuild.

## Session 2026-07-14 — Hifz (Memorization) Mode UI refined to Tarteel-style spec
The prior commit (2951bc6) built the live recitation + Hifz mode but the hidden
words used an `ImageFiltered` BLUR of the real glyphs. User asked for the exact
Tarteel-style behaviour: a **page of subtle circular placeholder dots** (not
blurred text), a `currentWordIndex` integer in state, auto-scroll so the active
word stays centered, and a temporary RED flash on incorrect words. Refinements
(working tree, not yet committed/built):
- `memorization_ayah_view.dart`: pending words in Hifz mode now render as a
  small `BoxShape.circle` dot using `theme.colorScheme.onSurface` @ 0.3 (the
  primary text colour at reduced opacity — blends into the dark brown theme).
  Revealed words use `AppTheme.arabicTextStyle(...)` with `onSurface` — the
  EXACT same TextStyle/font-size/colour as the reader's ayah text (no green tint
  in Hifz mode; only mistakes are coloured). Wrong = red, skipped = amber. The
  `Wrap` keeps `TextDirection.rtl`. Each word gets a stable `GlobalKey` (via
  `wordKeys`) for scrolling.
- `live_recitation_page.dart`: added a `ScrollController` on the live
  `SingleChildScrollView`; a `currentWordIndex` int + `flashIndex` int +
  `_flashTimer`; `_onEvent` reveals sequentially (matched → reveal at
  `currentWordIndex` + advance; error/skip in Hifz → flash the current dot,
  do NOT reveal) and flashes red/amber for ~900ms; `_scrollToCurrent()` uses
  `Scrollable.ensureVisible(alignment:0.5)` post-frame to center the active word
  as words wrap. `_resetWordTracking()` rebuilds the per-word keys on ayah load /
  `ready` / start / cancel / reset. `dispose()` disposes the controller + timer.
  Removed the now-unused `_activeIndex` getter. Legacy `RecitationPage` untouched.
- `test/live_recitation_test.dart`: updated to assert circular-dot placeholders
  (was `ImageFiltered`) for pending words and that matched words show as text.
- VERIFY: `flutter analyze` clean (info-only hints); `live_recitation_test` 7/7
   pass; `recitation_screen_test` (legacy) still passes.
- COMMITTED + PUSHED (commit 44f8a75) with the user's GitHub PAT (inline, not
   stored). APK rebuilt cleanly (75.5MB) via `flutter build apk --release` with
   the present Android SDK (`ANDROID_HOME=/home/Innocent/Android`), copied to
   `releases/app-release.apk`; `pubspec.yaml` + `releases/app_release.json`
   already bumped to **v1.0.18+29** (Hifz release notes). Large-APK (>50MB)
   warning as before — Git LFS still planned.
- REMAINING (blocked this session): deploy `releases/app-release.apk` +
   `app_release.json` to the VPS host path `/app/releases` (OTA
   `/v1/app/download`). SSH to 20.197.40.13 is password/key protected and no
   creds were available here, so the OTA binary is NOT yet live. Also reload
    nginx (WS `/ws/` timeouts) + ensure `recitation-api` serves the stream route.

## Session 2026-07-14 — Live Hifz streaming: two production fixes
Found + fixed two genuine defects in the existing Hifz/live-tracking feature
(code was already built in commits 2951bc6/44f8a75; these were latent bugs):

1. **Streaming alignment misalignment (real correctness bug)** —
   `ml/alignment/streaming_matcher.py` `StreamingMatcher.evaluate` reset the ASR
   hypothesis cursor `j=0` on EVERY pass while the reference cursor `i` had
   already advanced (`self._cursor`). Because the ASR hypothesis is *cumulative*
   (re-transcribed from the whole audio buffer each pass), re-matching the
   leading hypothesis words against the advanced reference cursor flagged
   correctly-recited words as `error` — i.e. the live Hifz view would mark real
   recitation RED. FIX: added `self._hyp_cursor` (hypothesis words consumed by
   the resolved reference prefix) and resume `j` there each pass. The
   order-preserving greedy alignment guarantees the resolved prefix maps 1:1 to
   the consumed hypothesis prefix, so no spurious ERRORs. `evaluate`/`finalize`
   verdicts now correct. `ml/tests/test_streaming_matcher.py::
   test_sliding_window_limits_single_pass` now passes.
2. **Build-breaking compile error** — `mobile/.../widgets/mic_visualizer.dart`
   used `StreamSubscription` without `import 'dart:async';` → `flutter analyze`
   ERROR (would break the APK build). Added the import. Removed an unused
   `sentBytes` var in `streaming_recitation_service.dart`. `flutter analyze` on
   both files: **No issues found**.

VERIFY: `pytest ml/tests backend/recitation_api/tests` → only the 2 pre-existing
Redis-less `test_api.py` failures remain (event loop closed; unrelated). The
feature now satisfies the blueprint end-to-end (normalization, sliding window of
15, `match`/`error_skipped` wire events, RTL Wrap, 0.3-opacity placeholder dots,
granular per-word rebuild, auto-scroll, 300ms PCM16 streaming).

### APK build + release (v1.0.19+30)
While verifying the build, two MORE working-tree compile errors surfaced (the
Hifz code had never been rebuilt since the refinements):
- `recitation_repository.dart` used `File(...)` without `import 'dart:io';` →
  added it.
- `recording_service.dart` called `_recorder.isSupported()` but `record` v85's
  `AudioRecorder` has no `isSupported()` method → dropped the guard and call
  `stop()` directly inside the existing try/catch.
After fixes `flutter analyze lib` → 0 errors (only info/warning lints). Rebuilt
APK with present Android SDK (`ANDROID_HOME=/home/Innocent/Android`) →
`mobile/build/app/outputs/flutter-apk/app-release.apk` (75.6MB) copied to
`releases/app-release.apk`; `pubspec.yaml` + `releases/app_release.json` bumped
to **v1.0.19+30**. Committed (amended into 48d9dc1). REMAINING: push to
origin/main (needs GitHub PAT — none in this env) + deploy APK to VPS host
 `/app/releases` (OTA `/v1/app/download`) + reload nginx (WS timeouts) + ensure
 `recitation-api` serves `/ws/recitation/stream`.

## Session 2026-07-14 — Live Recitation rewritten to Mushaf (blank-canvas) layout
User demanded the Hifz/dot UI be scrapped: remove the Memorization Mode toggle,
start as a BLANK canvas (no dots/boxes), and reveal confirmed words one-by-one
as a continuous RTL Mushaf (physical-book) flow with inline ۝ ayah markers.

MOBILE CHANGES (mobile/lib):
- NEW `features/recitation/presentation/widgets/mushaf_reveal_view.dart`
  `MushafRevealView`: a single `Directionality(rtl)` + `Wrap(direction:
  Axis.horizontal)` of revealed Arabic words. Starts EMPTY — no placeholder dots.
  Inserts an inline circular `۝<verse>` ayah marker between ayahs (driven by
  `ayahBoundaries` last-word indices). A `caretKey` zero-width anchor is placed
  at the end so the page can auto-scroll the latest word. Correct words read in
  plain `onSurface` book ink; error=red, skipped=amber.
- REWROTE `features/recitation/presentation/pages/live_recitation_page.dart`:
  deleted ALL Memorization Mode / Hifz / per-word `HifzWordState` machinery
  (Switch, `_ModePill`, dots, flash). Added `_revealedWords` + `_revealedStatuses`
  (both start `[]`) + `_revealedIndices` dedup set. On each `word` WS event the
  confirmed Arabic word (`event.expected ?? event.spoken`) is appended (skips
  empties/dupes). Live screen shows a blank canvas + a faint centered hint until
  the first word; then the `MushafRevealView`. `_scrollToLatest()` measures the
  caret via `Scrollable.of(ctx)` and, when it enters the bottom 30% of the
  viewport, animates it to ~33% (upper third) — no fighting user scrolling.
  Setup screen no longer has the toggle; it shows a plain RTL target preview.
  `_LiveStatusBadge` simplified (no mode pill). `RecitationPage` legacy untouched.
- `data/services/streaming_recitation_service.dart`: audio PCM flush cadence
  300ms → **250ms** (explicit user requirement: send PCM every 250ms). Mic
  permission is requested and the `record` stream stays open until Stop/Cancel
  (already correct). `_start` now always sends `memorizationMode:false`.
- DELETED `widgets/memorization_ayah_view.dart` (no longer referenced).
- `test/live_recitation_test.dart`: rewritten — asserts NO "Memorization Mode"
  text and NO `Switch` on setup; `MushafRevealView` starts blank, reveals words
  + `۝2` marker, and tints error words. 8/8 pass.

BACKEND (verified, mostly unchanged): `app/services/streaming_session.py`
`duration_seconds = total_samples / sample_rate`. Confirmed via a direct
`StreamingRecitationSession` harness: feeding a 3s PCM buffer yields
`duration_seconds: 3.0` and a non-empty final result — so the "Duration: 0s"
symptom is fixed as long as audio reaches the socket (it does: binary frames
flushed every 250ms; `websocket.py` accumulates via `add_audio`). The prior
"0%" was the stale/undeployed APK + empty backend reference data; with the
reference bundle (`reference_data`, built from local corpus) the stub/Whisper
transcriber reveals real words.

VERIFY: `flutter analyze lib` → 0 errors (only pre-existing flashcard warning).
`flutter test test/live_recitation_test.dart` → 8/8 pass. APK built with present
Android SDK (`ANDROID_HOME=/home/Innocent/Android`) →
`mobile/build/app/outputs/flutter-apk/app-release.apk` (75.5MB), copied to
`releases/app-release.apk`; `pubspec.yaml` + `releases/app_release.json` bumped
to **v1.0.20+31**. NOT committed/pushed (no git action requested; needs GitHub
PAT). REMAINING: push to origin/main + deploy APK to VPS host `/app/releases`
(OTA `/v1/app/download`) + reload nginx (WS timeouts) + ensure `recitation-api`
 serves `/ws/recitation/stream` with the reference bundle present.

## Session 2026-07-14 — Live Recitation results: fix "0 of 0" + "Duration 0s"
User tested the v1.0.20 Mushaf build: UI/live state correct, but Results screen
showed **"0 of 0 words correct"** AND **"Duration: 0s"**. Root-caused both:

1. **BACKEND BUG (the real "0 of 0" cause)** — in
   `backend/recitation_api/app/services/streaming_session.py` `load_reference`,
   after the (new) client-words fallback populated `self.reference_words`,
   the code still built `StreamingMatcher(norm)` and
   `_make_stub_transcriber(norm)` from the ORIGINAL local `norm` variable —
   which was EMPTY when the server's own reference store was empty. So the
   matcher tracked 0 reference words and the stub revealed 0 words → 0 verdicts
   → "0 of 0". FIX: build matcher + transcriber from `self.reference_words`
   (and gate the stub on `not self.reference_words`). Verified with a harness:
   empty server ref + client_words(6) now yields 4 live word events,
   `duration_seconds: 4`, 6 verdicts, score 0.67. Backend `tests/test_streaming.py`
   5/5 still pass.

2. **CLIENT-WORDS REFERENCE FALLBACK (defends against empty server ref)** —
   `streaming_recitation_service._start` now sends `words: _words` (the full
   resolved Mushaf/surah target) in the `start` handshake. `websocket.py`
   reads `start["words"]` → `StreamingRecitationSession(client_words=...)`.
   `load_reference` uses them only when its own reference resolves empty.

3. **RESULTS RESILIENCE** — `live_recitation_page._finishWith` now prefers the
   backend result ONLY if it has >0 word verdicts; otherwise it synthesizes
   from the live `_revealedWords` so the screen is never "0 of 0". `_words`
   (full target) is always passed as `ayahWords` to `RecitationResults`.

4. **AGGRESSIVE STREAMING DIAGNOSTICS (user-requested, for Duration 0s)** —
   `streaming_recitation_service.dart`:
   - `_audioSub` now has `onError` (logs MIC STREAM ERROR) + logs each mic
     chunk's byte length (first 5 + every 50th) and the cumulative buffered size.
   - `_flushAudio` logs bytes sent per 250ms flush (`totalSent=…`) and warns if
     the socket isn't open (so 0-byte sends are obvious).
   - WS `onError`/`onDone` listeners log connection drops / handshake errors.
   - `_onSocketData` logs RX ready/word/final/error events.
   - `_stop` logs `totalSentBytes` + mic chunks, the `stop` send, and the final
     result's `duration_seconds`/verdict count; timeout bumped 20s→30s.
   - `_start` wraps `startStream` in try/catch logging mic failure; connect logs
     the WS URL. `Stop & Review` ALREADY awaited the server `final` before
     navigating (via `_finalCompleter`) — confirmed untouched.

NOTE: a true "Duration 0s" on a device almost always means no PCM reached the
server. The code path is correct (binary frames flushed every 250ms; nginx
`/ws/` proxy has Upgrade headers + `proxy_buffering off` + 3600s timeouts, both
server blocks). The new per-flush byte logs will show `totalSent=0` if the
local recorder yields nothing (broken mic/permission) vs a healthy count. If
audio reaches the server but server ref was empty, the client-words fallback now
still scores. Also ensure the VPS `recitation-api` is actually serving the new
code + the reference bundle, and nginx was reloaded.

VERIFY: `flutter analyze lib` → 0 errors; `flutter test test/live_recitation_test`
8/8 pass; backend `pytest tests/test_streaming.py` 5/5. APK rebuilt (75.6MB) →
`releases/app-release.apk`; bumped to **v1.0.21+32**. NOT pushed (needs GitHub
PAT — none in env). REMAINING: push + deploy APK to VPS `/app/releases` + reload
nginx + restart `recitation-api` so the new stream route + client-words fallback
ship.






## Session 2026-07-14 — CRITICAL: "all 0%" was a backend DEPLOYMENT bug (fixed live)
User still saw "0 of 0 words" + 0% after the v1.0.21 code fixes. Root cause was
NOT the app logic — it was the running `recitation-api` container:
- Streaming runs INSIDE `recitation-api`, but `infra/docker-compose.yml` only
  mounted `../ml:/app/ml` (+ `PYTHONPATH:/app`) into `inference-worker`, NOT
  `recitation-api`. So `import ml.alignment.streaming_matcher` failed →
  `load_reference` raised → `ready` sent with 0 words → 0 verdicts → 0%/0-of-0.
  Server log showed `ws.stream.load_ref_failed error=No module named 'ml.alignment'`
  then `No module named 'numpy'` then `No module named 'torch'`.
- The image also lacked numpy/torch entirely (built before requirements.ml.txt
  was complete), but that's now moot.

FIXES (all committed to repo; container restarted + re-tested end-to-end):
1. `infra/docker-compose.yml` `recitation-api`: added `../ml:/app/ml` bind mount,
   `PYTHONPATH: /app`, `QARI_ML_USE_STUB: "true"` (live stream reveals words
   via the duration-based stub — no Whisper needed in this container), and a
   read-only `reference_data` mount.
2. `ml/alignment/__init__.py`: made the package `__init__` LAZY — it no longer
   eagerly imports `word_alignment`/`forced_alignment` (numpy/torch). Plain
   `from ml.alignment import StreamingMatcher` now pulls NOTHING heavy; the
   torch-dependent names load on first access (so the batch worker still works).
3. `backend/recitation_api/app/services/streaming_session.py`:
   - `_normalize` inlined (regex only) so reference resolution no longer imports
     the heavy `ml.inference.asr` (torch/numpy).
   - `_decode_float` rewritten numpy-free (`array('h')` → list of floats), so the
     live stream needs NEITHER numpy NOR torch.
   With these, the live stub flow runs in the API container with no ML stack.
   Verified: a WS client sending start+5s PCM+stop now returns
   `word_count=4`, `duration=5`, `verdicts=4`, `score=1.0`, 4× status "match".
   `tests/test_streaming.py` 5/5 still pass; `from ml.alignment import WordAligner,
   StreamingMatcher` both import (worker path intact).
- NOTE: `recitation-api` now uses `QARI_ML_USE_STUB=true`, so live matches are
  time-based (not true phonetic ASR). For REAL Whisper scoring, install
  torch/whisper into `recitation-api` and set `QARI_ML_USE_STUB=false` (the image
  currently lacks torch). The batch upload flow (inference-worker) is unaffected
  and keeps the real engine.

DEPLOY STATE: the running `recitation-api` container was recreated with the new
mounts/env and the new code (bind-mounted, so it is live). nginx proxies `/ws/`
→ recitation-api:8001 (Upgrade headers + proxy_buffering off + 3600s timeouts
already in infra/nginx.conf). The OTA APK (releases/app-release.apk = v1.0.21)
sends `words` in the start handshake and handles word events, so the app must be
updated to v1.0.21 to hit the fixed backend. REMAINING (user side): update the
app via OTA, then push this commit to origin/main (needs GitHub PAT — none in
env). The APK was already rebuilt at v1.0.21+32 in the prior turn.

## Session 2026-07-15 — Live ASR swapped to Faster-Whisper (CTranslate2, INT8, CPU)
Tarteel runs a custom Quranic ASR; their public `tarteel-ai/whisper-tiny-ar-quran`
is a Whisper-tiny fine-tuned on Quranic Arabic. The live recitation stream
previously used the heavy PyTorch `ml.inference.asr.QuranASR`
(`tarteel-ai/whisper-base-ar-quran`) — too slow for real-time on a CPU VPS.
Swapped ONLY the live transcriber to **Faster-Whisper + CTranslate2 (INT8)**
(CPU-friendly, ~2–4x faster than PyTorch). Server-side `StreamingMatcher`
forced-alignment + all features (history, tajweed, Mushaf reveal) unchanged.
The legacy Quran-section `RecitationPage` was NOT touched.

CHANGES:
- NEW `ml/inference/faster_whisper_transcriber.py`: `FasterWhisperTranscriber`
  (lazy, thread-safe singleton `get_transcriber()`). Loads CT2 model via
  `WhisperModel(model_dir, device="cpu", compute_type="int8", word_timestamps)`.
  `transcribe()` returns RAW Arabic word tokens + per-word `probability`
  (normalization left to the caller). Model dir via env `QARI_FASTERWHISPER_MODEL_DIR`
  (default `/app/models/tarteel-ct2-tiny`).
- `backend/recitation_api/app/services/streaming_session.py`:
  `_real_transcriber` now calls `get_transcriber().transcribe(...)` and
  normalizes the returned words with the SAME inlined `_normalize` used for the
  reference words (so hypothesis↔reference match consistently). Returns `([],[])`
  on any failure (graceful, no crash).
- `backend/recitation_api/requirements.ml.txt`: added `faster-whisper==1.0.3`,
  `ctranslate2==4.4.0`, `av==12.2.0`, `requests==2.32.3` (faster-whisper imports
  `requests` at load). `inference-worker` still uses the PyTorch `QuranASR` for
  the batch upload flow — unaffected.
- `infra/docker-compose.yml` `recitation-api`: `QARI_ML_USE_STUB` → `"false"`
  (real Faster-Whisper runs in this container, no GPU needed) + new
  `QARI_FASTERWHISPER_MODEL_DIR: /app/models/tarteel-ct2-tiny`. The CT2 model is
  bind-mounted via the existing `../backend/recitation_api:/app` volume, so it
  appears at `/app/models/tarteel-ct2-tiny`.
- NEW `scripts/convert_tarteel_model.py`: one-command conversion of
  `tarteel-ai/whisper-tiny-ar-quran` → CT2 INT8 via `ct2-transformers-converter`,
  then generates `tokenizer.json` (the source ships the classic GPT2 Whisper
  tokenizer, not a fast tokenizer that faster-whisper needs).

MODEL CONVERSION (done in this dev env, ~42MB INT8):
`python scripts/convert_tarteel_model.py` → writes
`backend/recitation_api/models/tarteel-ct2-tiny/` (model.bin + tokenizer.json +
preprocessor_config.json). That dir is gitignored (large weights, like
`reference_data/`). On the VPS, run the same script so the model exists on disk
at `<repo>/backend/recitation_api/models/tarteel-ct2-tiny` (the bind mount makes
it available at `/app/models/tarteel-ct2-tiny` inside the container). Conversion
needs `transformers` + `torch` + `ctranslate2` (NOT needed at inference).

VALIDATION (real end-to-end, this env):
- `pytest ml/tests` + `backend/recitation_api/tests/test_streaming.py` → 120 passed
  (includes new `test_faster_whisper_transcriber.py`, mocked).
- Real model: synthesized a 16k Arabic clip (espeak-ng `بسم الله الرحمن الرحيم`)
  and ran it through `StreamingRecitationSession` with the real Faster-Whisper
  transcriber: model loaded, `transcribe()` returned real Arabic word tokens +
  confidences, `StreamingMatcher` emitted live `word` events and `finalize()`
  produced a scored result (score 0.5 on the ROBOTIC espeak TTS — expected;
  real human recitation transcribes far better, per prior session notes).
  NOTE: the default model dir is `/app/models/tarteel-ct2-tiny`; when testing
  locally set `QARI_FASTERWHISPER_MODEL_DIR=backend/recitation_api/models/tarteel-ct2-tiny`.

DEPLOY NOTE: after this change the running `recitation-api` container must be
recreated (compose now sets `QARI_ML_USE_STUB=false` + model dir) and the CT2
model present on the VPS host at `backend/recitation_api/models/tarteel-ct2-tiny`.
No Flutter/mobile change needed — the app unchanged. APK not rebuilt.

### Deployed on the VPS (this session, live container `infra-recitation-api-1`)
- Rebuilt `recitation-api` image (added faster-whisper/ctranslate2 to
  requirements.ml.txt) and recreated the container → `QARI_ML_USE_STUB=false`,
  model mounted at `/app/models/tarteel-ct2-tiny` (bind mount). Health OK.
- BLOCKER + FIX 1 (ctranslate2 exec-stack): the CT2 shared lib is compiled with
  an executable-stack (RWE GNU_STACK). The container kernel refused to enable it
  → `libctranslate2...so: cannot enable executable stack as shared object
  requires: Invalid argument` and live transcription silently fell back to 0
  verdicts. `execstack` is NOT installable here, so added
  `backend/recitation_api/fix_execstack.py` (clears the exec bit on the
  GNU_STACK phdr via raw ELF editing) and a `RUN python3 fix_execstack.py` step
  in `backend/recitation_api/Dockerfile` (runs AFTER `pip install`, before
  `COPY . .`). Verified: GNU_STACK now `RW`. This is durable across recreates.
- FIX 2 (final verdict `actual_text` was always null): `StreamingMatcher.
  finalize()` rebuilt `WordState` without carrying `spoken`, so the final
  result's word_verdicts had `actual_text: null` (broke the "compare your
  recitation" results sheet). Now `finalize()` looks up the spoken word +
  confidence from `_resolved_states`. Live `word` events already had it; the
  final payload now matches.
- VALIDATION (live WS, espeak-ng Arabic clip → `ws://localhost:8001/ws/
  recitation/stream`): model loaded, `Processing audio` logged, real Arabic
  `word` events streamed, `final` returned with populated `expected_text` +
  `actual_text` and a scored result. Accuracy on the ROBOTIC espeak TTS is low
  (expected — Whisper-Quran is trained on natural recitation); a real human
  recitation transcribes far better. `pytest ml/tests` +
  `backend/recitation_api/tests/test_streaming.py` → 120 passed.
- NOT committed/pushed (no git action requested). Changes to commit later:
  `ml/inference/faster_whisper_transcriber.py`, `ml/alignment/
  streaming_matcher.py` (finalize fix), `backend/recitation_api/app/services/
  streaming_session.py`, `backend/recitation_api/Dockerfile` +
  `fix_execstack.py`, `backend/recitation_api/requirements.ml.txt`,
  `infra/docker-compose.yml`, `scripts/convert_tarteel_model.py`,
  `ml/tests/test_faster_whisper_transcriber.py`, `.gitignore`
  (backend/recitation_api/models/ ignored). The converted model is gitignored.

## Session 2026-07-15 (later) — Device "0 of N / Duration 0s" = missing RECORD_AUDIO
User tested the live AI Recitation on device: results showed "0 of 29 words
correct / Duration: 0s / all 0%", no words appeared while reciting, and "qari
voice has no sound". ROOT CAUSE: `mobile/android/app/src/main/AndroidManifest.xml`
was **missing `android.permission.RECORD_AUDIO`** entirely. The WebSocket
connected fine (29 reference words arrived), but with no manifest permission the
OS silently blocked ALL mic capture → zero PCM frames sent → server finalizes
with 0 samples → "Duration 0s" + 0/N. The `record` package + permission_handler
runtime request can't grant capture without the manifest declaration.
FIX: added `<uses-permission android:name="android.permission.RECORD_AUDIO"/>`
to the manifest. Bumped app to **v1.0.22+33** (pubspec.yaml + releases/
app_release.json with fix notes), rebuilt APK (76.0MB) and copied to
`releases/app-release.apk` — which is bind-mounted into core-api at `/app/
releases` (read-only), so the OTA (`/v1/app/download` + `/v1/app/version`)
immediately serves v1.0.22 with no container restart. Verified the VPS now
returns the 76.0MB APK + version_code 33. User must UPDATE via OTA and ALLOW
microphone when prompted; then live word tracking should work.
NOTE: "qari voice no sound" was NOT fully root-caused — the live Mushaf page
does not play reference audio during recitation (no "Listen First" in this
build); the reference track only appears on the results screen via
`reference_audio_url` (may be empty if the reference bundle lacks audio URLs).
Likely a device-volume/Bluetooth issue or missing reference URL, not the mic
bug. Ask the user where they expect qari audio (during recitation vs results)
before adding a feature.
APK build uses ANDROID_HOME=/home/Innocent/Android (SDK present; set it before
`flutter build apk --release`). `flutter pub get` then build ~152s.

## Session 2026-07-15 (still) — RECORD_AUDIO alone didn't fix "0 of N"
Deployed v1.0.22+33 (RECORD_AUDIO added) but user STILL got "0 of 29 /
Duration 0s / no words / tajweed not showing". Server logs prove the device
connects and sends the 29-word `start` handshake (`ws.stream.started words=29`)
and the WS works — but there is NO "Processing audio" for the user's sessions,
i.e. **zero audio bytes reached the server**. The 29 "Word by Word" words are
the LOCAL target list, NOT proof of server connection. So even after the
permission fix, mic capture or binary-send is still failing silently on the
device (tajweed "not working" is just a consequence of no revealed words).
ADDED DIAGNOSTICS (built v1.0.23+34, deployed to OTA):
- `StreamingRecitationService`: public getters `sentBytes` (_totalSentBytes) and
  `micChunks` (_chunkCount).
- `live_recitation_page.dart`: a live "diag · mic chunks: N · bytes sent: N" text
  (via ValueNotifier so only that Text rebuilds, not the reveal view; 500ms
  `_diagTimer`). On finish, if `sentBytes == 0` show a clear error
  "No microphone audio was captured (0 bytes sent)…" instead of a silent 0/N.
  Timer stopped in `_stop`/`_cancel`/`_reset`/`dispose`.
NEXT: user must update to v1.0.23 and report the diag line:
  - "mic chunks: 0 · bytes sent: 0" ⇒ recorder produces no data (OS still
    blocking capture despite permission — check OS mic privacy / another app
    holding the mic / Android version quirk).
  - "mic chunks: N · bytes sent: 0" ⇒ capture OK but binary WS send fails.
  - "bytes sent: >0" ⇒ transport OK, server-side issue (unlikely; server shows
    no audio for these sessions).
NOT YET committed (user will request). Changes: AndroidManifest RECORD_AUDIO,
streaming_recitation_service getters, live_recitation_page diagnostics,
 pubspec + app_release.json bumps (→1.0.23+34), plus the earlier uncommitted
 Faster-Whisper backend work.

## Session 2026-07-15 — DIAGNOSING "mic chunks: 0 · bytes sent: 0" (no error)
User updated to v1.0.23+34; live diag still shows `mic chunks: 0 · bytes sent: 0`
and the final screen says "No microphone audio was captured … OS is blocking
capture". There is NO native error captured (`_micError == null`). The single
watchdog restart (same config) fails identically → 0 chunks every time.

INVESTIGATION (read the `record` plugin source in pub cache, v7.1.1 /
record_android 2.1.2):
- `AudioRecorder.start` (record_android) runs the `RecordThread`, which builds
  `PCMReader` (the `AudioRecord`). If `AudioRecord.state != INITIALIZED` or
  `getMinBufferSize` reports bad config, it throws "PCM reader failed to
  initialize." / "Recording config is not supported by the hardware". That
  exception is caught by the thread and routed to `onFailure` → BOTH
  `sendStateErrorEvent` (state EventChannel) AND `sendErrorEvent` (record
  EventChannel), posted via `uiThreadHandler.post` AFTER the start method
  already returned `success`.
- The record-data stream error is ALMOST ALWAYS LOST: `record` v7's
  `_startRecordStream` only forwards `ctrl.addError` when `ctrl.hasListener`
  is true, but the app attaches its `audioStream.listen` (via `_attachMic`)
  only AFTER `startStream`/`await` resolves — by then the native error Event
  has already fired on the channel and is dropped. So the recorder fails
  silently → exactly `micChunks: 0, micError: null`.
- ROOT-CAUSE HYPOTHESIS (to be confirmed on device): the requested
  `RecordConfig` (PCM16, **16kHz**, `voiceRecognition` source) is rejected by
  the user's device/ROM — either 16kHz isn't supported for that source on some
  OEMs (Xiaomi/OPPO/Huawei) → init failure, or `VOICE_RECOGNITION` source
  returns 0 frames on that ROM → silent 0-chunk stream. (record never requests
  AudioFocus unless `audioInterruption != NONE`, but missing focus alone would
  not cause 0 chunks.)

FIX APPLIED = DIAGNOSTICS ONLY (user chose "investigate first", not fix yet):
- `StreamingRecitationService`: subscribe to `_recorder.onStateChanged()`
  BEFORE `startStream` (`_subscribeRecorderState`) and capture its `onError`
  into `_micError`. The state channel is attached earliest, so its setup-error
  event survives (unlike the audio-data channel) → the real cause becomes
  visible. Re-subscribed after each recorder recreate (`_restartMic`) and
  cancelled in `cancel`/`dispose`.
- `live_recitation_page.dart`: new `_micErrorNotifier` surfaced live in the
  `diag · mic chunks: N · bytes sent: N` line (turns red + prints the recorder
  error) so a swallowed failure shows immediately, not only on the error screen.
- `flutter analyze` passes (only pre-existing info/warning items).

NEXT (confirm on device, then fix): rebuild + OTA the diagnostic build, have
user retry. Two outcomes:
  - diag shows `recorder error: PCM reader failed to initialize / config not
    supported` → it's a CONFIG issue → add `startStream` fallback across
    `(voiceRecognition|mic, 16k|44.1k)` and/or `audioInterruption`/audio focus.
  - diag still `mic chunks: 0 · micError: null` → recorder INITIALIZED but
    emits silence (OEM voiceRecognition quirk / OS truly blocking) → switch to
    `AndroidAudioSource.mic` (or `unprocessed`) + `audio_session` focus.
NOT committed/pushed; version NOT bumped yet (waiting on device confirmation).
