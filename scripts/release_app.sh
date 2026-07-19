#!/usr/bin/env bash
#
# Qari app release script — builds a release APK and publishes it for OTA
# (over-the-air) delivery. No Play Store upload required: the backend serves
# the APK from /releases and the app downloads+installs it in-app.
#
# Usage:
#   ./scripts/release_app.sh                         # build + publish as-is
#   ./scripts/release_app.sh --bump                  # bump version_code (patch)
#   ./scripts/release_app.sh --bump --data-version   # also bump backend data_version
#   ./scripts/release_app.sh --notes-en "Bug fixes" --notes-ur "..."
#   ./scripts/release_app.sh --use-tarteel-live false   # use in-house VPS backend
#   ./scripts/release_app.sh --tarteel-token <hex>      # bake DRF auth token
#
# The live recitation stream defaults to Tarteel's real-time voice API.
# Override via env (USE_TARTEEL_LIVE, TARTEEL_LIVE_TOKEN) or the flags above.
#
# After running, commit releases/app_release.json + releases/app-release.apk
# and push to the server (or sync the releases/ dir to the host). The running
# backend picks up the new file + JSON with no restart.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOBILE="$ROOT/mobile"
RELEASES="$ROOT/releases"
APK_OUT="$MOBILE/build/app/outputs/flutter-apk/app-release.apk"
APK_DST="$RELEASES/app-release.apk"
RELEASE_JSON="$RELEASES/app_release.json"

ANDROID_HOME="${ANDROID_HOME:-/home/Innocent/Android}"
export ANDROID_HOME

BUMP=0
BUMP_DATA=0
NOTES_EN=""
NOTES_UR=""
NOTES_HI=""

# ── Tarteel live tracking flags ────────────────────────────────────────────
# The live recitation stream defaults to Tarteel's real-time voice API
# (wss://voice-v2.tarteel.io) rather than our own /ws/recitation/stream VPS
# backend. Pass USE_TARTEEL_LIVE=false to revert to the in-house backend.
# The DRF auth token is read from $TARTEEL_LIVE_TOKEN (or --tarteel-token).
USE_TARTEEL_LIVE="${USE_TARTEEL_LIVE:-true}"
TARTEEL_LIVE_TOKEN="${TARTEEL_LIVE_TOKEN:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bump) BUMP=1 ;;
    --data-version) BUMP_DATA=1 ;;
    --notes-en) NOTES_EN="$2"; shift ;;
    --notes-ur) NOTES_UR="$2"; shift ;;
    --notes-hi) NOTES_HI="$2"; shift ;;
    --tarteel-token) TARTEEL_LIVE_TOKEN="$2"; shift ;;
    --use-tarteel-live) USE_TARTEEL_LIVE="$2"; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

# ── Bump version in pubspec.yaml (version: x.y.z+CODE) ─────────────────────
bump_pubspec() {
  local pubspec="$MOBILE/pubspec.yaml"
  python3 - "$pubspec" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
m = re.search(r'^version:\s*(\d+\.\d+\.\d+)\+(\d+)\s*$', s, re.M)
if not m:
    print("Could not parse version line in pubspec.yaml"); sys.exit(1)
ver, code = m.group(1), int(m.group(2))
code += 1
s = s[:m.start()] + f"version: {ver}+{code}\n" + s[m.end():]
open(p, "w").write(s)
print(f"Bumped pubspec version_code -> {code}")
PY
}

[[ "$BUMP" -eq 1 ]] && bump_pubspec

# ── Build the release APK ──────────────────────────────────────────────────
echo "==> Building release APK (USE_TARTEEL_LIVE=$USE_TARTEEL_LIVE)..."
DART_DEFINES="--dart-define=USE_TARTEEL_LIVE=$USE_TARTEEL_LIVE"
if [[ -n "$TARTEEL_LIVE_TOKEN" ]]; then
  DART_DEFINES="$DART_DEFINES --dart-define=TARTEEL_LIVE_TOKEN=$TARTEEL_LIVE_TOKEN"
fi
( cd "$MOBILE" && flutter pub get && flutter build apk --release $DART_DEFINES )

if [[ ! -f "$APK_OUT" ]]; then
  echo "Build failed: $APK_OUT not found" >&2
  exit 1
fi

mkdir -p "$RELEASES"
cp -f "$APK_OUT" "$APK_DST"
echo "==> APK copied to $APK_DST ($(du -h "$APK_DST" | cut -f1))"

# ── Update releases/app_release.json ───────────────────────────────────────
python3 - "$RELEASE_JSON" <<PY
import json, re, sys, subprocess
p = sys.argv[1]
s = open(p).read()
data = json.loads(s)

m = re.search(r'^version:\s*(\d+\.\d+\.\d+)\+(\d+)\s*$',
              open("$MOBILE/pubspec.yaml").read(), re.M)
ver, code = m.group(1), int(m.group(2))

data["version"] = ver
data["version_code"] = code
data["apk_url"] = "https://20.197.40.13/v1/app/download"

if "$NOTES_EN": data["notes_en"] = "$NOTES_EN"
elif "$USE_TARTEEL_LIVE" == "true":
    data["notes_en"] = "Live Recitation routes through Tarteel's real-time voice API (wss://voice-v2.tarteel.io) with the captured protocol (base64 JSON audio frames)."
if "$NOTES_UR": data["notes_ur"] = "$NOTES_UR"
if "$NOTES_HI": data["notes_hi"] = "$NOTES_HI"

if "$BUMP_DATA" == "1":
    data["data_version"] = int(data.get("data_version", 0)) + 1
    print(f"Bumped data_version -> {data['data_version']}")

open(p, "w").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(f"==> Published {ver} (code {code}) to app_release.json")
PY

echo "Done. Sync releases/ to the host and the app will OTA-update on next launch."
