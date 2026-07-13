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

## Open tasks / TODO
- (add as discovered)
