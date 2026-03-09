#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -x "./gradlew" ]]; then
  ./gradlew :app:assembleDebug
else
  echo "gradlew not found. Generate wrapper in Android Studio or run: gradle wrapper"
  exit 1
fi

echo "APK path: app/build/outputs/apk/debug/app-debug.apk"
