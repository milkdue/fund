#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -x "./gradlew" ]]; then
  ./gradlew :app:bundleRelease
else
  echo "gradlew not found. Generate wrapper in Android Studio or run: gradle wrapper"
  exit 1
fi

echo "AAB path: app/build/outputs/bundle/release/app-release.aab"
