# Android MVP (Kotlin + Compose)

## Architecture
- `domain/`: model + repository contract + use cases
- `data/`: Retrofit + Room + repository implementation
- `presentation/`: ViewModel + Compose screens

## Run
1. Open `android/` in Android Studio.
2. Ensure backend is running at `http://10.0.2.2:8000/v1/` for emulator.
3. Sync Gradle and run `app`.

## Build package
- Debug APK: `./build_apk.sh`
- Release AAB: `./build_aab.sh`
- If wrapper is missing, create Gradle wrapper first (`gradle wrapper` or Android Studio sync).

## Screens
- Risk disclosure (mandatory)
- Search
- Detail (quote + short/mid prediction + explain + add watchlist)
- Watchlist

## iOS extension readiness
- API versioned as `/v1`
- Stable DTO field names and error envelope
- Core business rules in backend/domain layer (not UI)
