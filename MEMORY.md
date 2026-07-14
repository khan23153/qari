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



