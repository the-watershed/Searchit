# Historical Markers Tracker — Android App

An Android app that lets you track which **historical markers** you've visited across the United States.

## Features

| Feature | Details |
|---|---|
| 📋 Marker list | Scrollable list of 30 real US historical markers |
| 🔍 Filter chips | One-tap filter: **All · Visited · Unvisited** |
| ✅ Visit toggle | Tap the ✔ FAB on the detail screen **or** long-press a row to mark a visit |
| 🗓 Visit date | Records the exact date & time of each check-in |
| 📖 Full description | Detail screen with historical context for every marker |
| 📍 GPS coordinates | Latitude/longitude stored per marker for future map integration |
| 💾 Offline-first | All data stored locally in a Room/SQLite database — no internet required |

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Kotlin |
| UI | XML Views + View Binding + Material Components 3 |
| Architecture | MVVM — ViewModel + LiveData + Repository |
| Database | Room (SQLite) |
| Async | Kotlin Coroutines |
| Min SDK | API 26 (Android 8.0) |
| Target SDK | API 34 (Android 14) |

## Project Structure

```
android/
├── app/
│   └── src/main/
│       ├── java/com/jureka/historicalmarkers/
│       │   ├── data/
│       │   │   ├── Marker.kt            # Room entity
│       │   │   ├── MarkerDao.kt         # Database queries
│       │   │   ├── MarkerDatabase.kt    # Singleton DB
│       │   │   ├── MarkerRepository.kt  # Data access layer
│       │   │   └── DataSeeder.kt        # 30 seed markers
│       │   ├── viewmodel/
│       │   │   ├── MarkerListViewModel.kt    # Drives MainActivity
│       │   │   └── MarkerDetailViewModel.kt  # Drives detail screen
│       │   └── ui/
│       │       ├── MainActivity.kt      # List screen
│       │       ├── MarkerDetailActivity.kt  # Detail/check-in screen
│       │       └── MarkerAdapter.kt     # RecyclerView adapter
│       ├── res/
│       │   ├── layout/                  # activity_main, activity_marker_detail, item_marker
│       │   ├── drawable/                # Vector icons
│       │   ├── menu/                    # Overflow filter menu
│       │   └── values/                  # strings, colors, themes
│       └── AndroidManifest.xml
├── gradle/
│   ├── wrapper/                         # Gradle wrapper (8.7)
│   └── libs.versions.toml               # Version catalog
├── build.gradle.kts                     # Root build file
├── settings.gradle.kts
├── gradle.properties
├── gradlew / gradlew.bat
└── README.md
```

## Building & Running

### Prerequisites

1. **Android Studio** Hedgehog (2023.1.1) or newer  
2. **Android SDK** with API 26+ and Build Tools 34.x  
3. Java 17 (bundled with Android Studio)

### Steps

```bash
# From the android/ directory:
./gradlew assembleDebug

# Or open android/ as a project in Android Studio and click ▶ Run
```

The APK will be at `app/build/outputs/apk/debug/app-debug.apk`.

## Adding More Markers

Edit `DataSeeder.kt` and append a new `Marker(...)` object to the list returned by
`getDefaultMarkers()`.  The seeder runs every launch; existing rows are skipped via
Room's `IGNORE` conflict strategy so your additions appear on the next app start
without disturbing existing visit records.

Full national datasets are available from [hmdb.org](https://www.hmdb.org) (Historical Marker Database).
