#!/usr/bin/env bash
# Writes mobile/android/key.properties from GitHub secrets so every CI build
# is signed with the same Safha release key.
#
# Without one fixed key each GitHub runner signs with a fresh random debug
# key, so a new APK cannot install over the previous one ("App not
# installed") and the in-app updater fails.
#
# Secrets: SAFHA_KEYSTORE_BASE64, SAFHA_KEYSTORE_PASSWORD, SAFHA_KEY_ALIAS,
# SAFHA_KEY_PASSWORD (mapped to env vars of the same name by the workflow).
#
# Usage: ci_android_signing.sh [--required]
#   --required  fail when the secrets are missing (release builds)
#   otherwise   warn and fall back to the runner's debug key (previews)
set -euo pipefail

REQUIRED=0
[[ "${1:-}" == "--required" ]] && REQUIRED=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROPS="$ROOT/mobile/android/key.properties"

if [[ -z "${SAFHA_KEYSTORE_BASE64:-}" || -z "${SAFHA_KEYSTORE_PASSWORD:-}" ]]; then
  MSG="Release signing secrets are not set (SAFHA_KEYSTORE_BASE64, SAFHA_KEYSTORE_PASSWORD, SAFHA_KEY_ALIAS, SAFHA_KEY_PASSWORD). Add them under Settings > Secrets and variables > Actions."
  if [[ "$REQUIRED" -eq 1 ]]; then
    echo "::error::$MSG Refusing to publish an APK signed with a random key: it could not update existing installs."
    exit 1
  fi
  echo "::warning::$MSG This APK is signed with a temporary key and will not install over an earlier one."
  exit 0
fi

KEYSTORE="${RUNNER_TEMP:-/tmp}/safha-release.jks"
umask 077
printf '%s' "$SAFHA_KEYSTORE_BASE64" | base64 -d > "$KEYSTORE"
cat > "$PROPS" <<EOF
storeFile=$KEYSTORE
storePassword=$SAFHA_KEYSTORE_PASSWORD
keyAlias=${SAFHA_KEY_ALIAS:-safha}
keyPassword=${SAFHA_KEY_PASSWORD:-$SAFHA_KEYSTORE_PASSWORD}
EOF
echo "Release signing configured (key alias: ${SAFHA_KEY_ALIAS:-safha})."
