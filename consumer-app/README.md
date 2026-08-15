# AVENZO Consumer App — Flutter

> **Foundation Scaffold — Phase 0**
> Flutter SDK is NOT yet installed on this machine.

---

## ⚠️ Setup Required

Flutter SDK must be installed before this project can run.

### Install Flutter

1. Download Flutter SDK: https://docs.flutter.dev/get-started/install/windows/mobile
2. Add to PATH
3. Run `flutter doctor` to verify
4. Run `flutter pub get` in this directory

---

## Chosen State Management: Riverpod

**Decision:** Riverpod (flutter_riverpod) is the official state management approach for AVENZO consumer app.

**Rationale:**
- Compile-safe providers (no runtime errors)
- No BuildContext dependency
- Excellent for async operations (AsyncNotifier)
- Testable without mocking
- No mixing of state management libraries allowed

---

## Project Structure

```
consumer-app/
├── lib/
│   ├── main.dart               App entry point
│   ├── app/
│   │   └── app.dart            Root widget, routing, theme
│   ├── core/
│   │   ├── constants/          App constants, API URLs
│   │   ├── services/
│   │   │   └── api_service.dart HTTP client (Dio)
│   │   ├── utils/              Utility functions
│   │   └── errors/             Error types and handling
│   ├── features/
│   │   ├── auth/               Login, registration
│   │   │   ├── data/           API data source
│   │   │   ├── domain/         Business models, repo interface
│   │   │   └── presentation/   UI + Riverpod providers
│   │   ├── products/           Product browsing
│   │   ├── cart/               Shopping cart
│   │   ├── orders/             Order history
│   │   ├── pantry/             Digital pantry
│   │   ├── scanning/           Barcode/QR/OCR
│   │   └── notifications/      Push notifications
│   └── shared/
│       ├── widgets/            Reusable UI components
│       └── models/             Shared data models
├── android/                    Android platform files
├── ios/                        iOS platform files
└── pubspec.yaml                Flutter project config
```

---

## Development Setup

After installing Flutter:

```bash
cd consumer-app

# Verify environment
flutter doctor

# Install dependencies
flutter pub get

# Run on connected device or emulator
flutter run

# Run tests
flutter test
```

---

## Key Dependencies (pubspec.yaml)

| Package | Purpose |
|---------|---------|
| flutter_riverpod | State management |
| dio | HTTP client for API calls |
| go_router | Navigation / routing |
| firebase_messaging | FCM push notifications |
| mobile_scanner | Barcode / QR scanning |
| image_picker | Camera/gallery access |
| shared_preferences | Local storage |
| intl | Internationalization / date formatting |
| flutter_local_notifications | Local notification display |

---

## Coding Standards

- **State management**: Riverpod only — no Provider, GetX, BLoC mixing
- **API calls**: Only through `core/services/api_service.dart`
- **Constants**: No hardcoded strings/URLs — use `core/constants/app_constants.dart`
- **Feature structure**: Every feature follows data/domain/presentation layers
- **Naming**: snake_case for files, PascalCase for classes, camelCase for variables

---

*AVENZO Consumer App — Phase 0 Foundation*
