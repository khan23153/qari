#!/usr/bin/env bash
# Checks an APK installs on every phone Safha supports:
#   - minimum Android version is 7.0 (API 24) or lower,
#   - native code for 32-bit and 64-bit ARM phones (and x86_64 emulators),
#   - signed with the Safha release key (when --release-key is given), so it
#     updates over earlier installs.
#
# Usage: ci_verify_apk.sh APK [--release-key]
set -euo pipefail

APK="$1"
RELEASE_KEY=0
[[ "${2:-}" == "--release-key" ]] && RELEASE_KEY=1

# SHA-256 of the Safha release signing certificate (public, safe to commit).
SAFHA_CERT_SHA256="ac802750737d3a43dab4133375b8fc6b6615da553e15597c3cb03a214ea323b1"
MAX_MIN_SDK=24

BUILD_TOOLS=$(find "$ANDROID_HOME/build-tools" -maxdepth 1 -mindepth 1 -type d | sort -V | tail -n 1)
BADGING=$("$BUILD_TOOLS/aapt" dump badging "$APK")
echo "$BADGING" | grep -E "^(package|sdkVersion|targetSdkVersion|native-code)" || true

MIN_SDK=$(echo "$BADGING" | sed -n "s/^sdkVersion:'\([0-9]*\)'.*/\1/p")
if [[ -z "$MIN_SDK" || "$MIN_SDK" -gt "$MAX_MIN_SDK" ]]; then
  echo "::error::minSdk is ${MIN_SDK:-unknown}; Safha must install on Android 7.0 (API $MAX_MIN_SDK)."
  exit 1
fi

NATIVE=$(echo "$BADGING" | grep "^native-code:" || true)
for abi in armeabi-v7a arm64-v8a x86_64; do
  if ! echo "$NATIVE" | grep -q "'$abi'"; then
    echo "::error::APK has no $abi code; phones of that type cannot install it."
    exit 1
  fi
done

CERTS=$("$BUILD_TOOLS/apksigner" verify --print-certs "$APK")
echo "$CERTS" | grep -i "SHA-256" || true
if [[ "$RELEASE_KEY" -eq 1 ]]; then
  if ! echo "$CERTS" | tr 'A-F' 'a-f' | grep -q "$SAFHA_CERT_SHA256"; then
    echo "::error::APK is not signed with the Safha release key; it would not update existing installs."
    exit 1
  fi
fi
echo "APK OK: minSdk $MIN_SDK, ABIs armeabi-v7a arm64-v8a x86_64."
