# AVENZO — Project Status & Roadmap

> Document Status: **ACTIVE — Phase 4 Complete**
> Last Updated: 2026-08-18
> Active Branch: `develop`

---

## Overall Progress Overview

```
[Phase 0: Foundation] ──► [Phase 1: Core Backend] ──► [Phase 2: Inventory Intel & FEFO] ──► [Phase 3: Business Web] ──► [Phase 4: Consumer App Foundation]
       ✅ COMPLETE               ✅ COMPLETE                       ✅ COMPLETE                    ✅ COMPLETE                     ✅ COMPLETE
```

---

## Phase Status Summary

| Phase | Description | Target Component | Status | Notes |
|-------|-------------|------------------|--------|-------|
| **Phase 0** | Foundation + Architecture | Monorepo / Docs | ✅ **COMPLETE** | Initial repo structure, docs, scaffolds |
| **Phase 1** | Core Backend & Database Foundation | Backend / DB | ✅ **COMPLETE** | PostgreSQL, Alembic, Auth, Products, Warehouses, Batches, Inventory, 17/17 tests passing |
| **Phase 2** | Inventory Intelligence & FEFO | Backend / FEFO | ✅ **COMPLETE** | FEFO 5-level ranking, non-mutating allocation preview, FEFO violation audit logs, Expiry & Risk metrics, 23/23 tests passing |
| **Phase 3** | Business Web Foundation | React / Web | ✅ **COMPLETE** | Vite, React 19, TypeScript, React Router, TanStack Query, AuthContext, Dashboard, Product, Category, Inventory, Batches, FEFO Preview & Risk Screens |
| **Phase 4** | Consumer App Foundation | Flutter Mobile | ✅ **COMPLETE** | Riverpod 2.x, GoRouter, Dio 5.x, flutter_secure_storage, Material 3 Consumer theme, Auth, Role validation via /auth/me, Navigation Shell, 17/17 tests passing |
| **Phase 5A** | Consumer Pantry Backend | FastAPI / DB | ✅ **COMPLETE** | `consumer_pantries`, `pantry_items`, `pantry_item_logs` tables, Alembic migration, pantry CRUD, consume/discard actions, DTE expiry sorting, ownership isolation security, 28/28 tests passing |
| **Phase 5B** | Consumer Pantry Flutter UI | Flutter Mobile | ✅ **COMPLETE** | `PantryItemModel`, `PantryRepository`, Riverpod `pantryNotifierProvider`, interactive Material 3 `PantryScreen`, `AddPantryItemModal`, `PantryItemDetailSheet`, Consume/Discard/Delete actions, 25/25 Flutter tests passing, `flutter analyze` 0 issues |
| **Phase 5C** | Expiry Local Notifications | Flutter Mobile | ✅ **COMPLETE** | `NotificationService`, `ExpiryNotificationScheduler`, Android notification channel `avenzo_expiry_alerts`, deterministic stable item notification IDs, 7d/3d/0d warning scheduling rules, idempotency & pantry lifecycle sync, 33/33 Flutter tests passing |
| **Phase 5D** | Barcode & Camera Scanner | Flutter Mobile | ✅ **COMPLETE** | Real camera preview via `mobile_scanner`, barcode normalization, `ProductLookupRepository`, `ScannedProductConfirmationSheet`, pre-filled AddToPantry flow, manual fallback, 40/40 Flutter tests passing |
| **Phase 5E** | Consumer Receipt OCR Ingestion | Flutter Mobile | ✅ **COMPLETE** | On-device ML Kit text recognition (`google_mlkit_text_recognition`), rule-based `ReceiptLineParser`, noise filtering, `ReceiptProductMatcher`, Material 3 `ReceiptReviewScreen`, batch ingestion into `PantryNotifier` & Expiry notifications, 46/46 Flutter tests passing |
| **Phase 5F** | Personalized Insights & Recommendations | FastAPI / Flutter | ✅ **COMPLETE** | Pluggable `RecommendationEngine` / `RuleBasedRecommendationEngine`, `consumer_recommendations` table & Alembic migration `5f01`, taxonomy (`USE_SOON`, `WASTE_RISK`, `OVERSTOCK`, `CONSUMPTION_INSIGHT`, `EXPIRY_PRIORITY`), explainable reasons, `/api/v1/recommendations` REST API, Material 3 `RecommendationsScreen`, Home Dashboard Smart Insights banner, 31/31 pytest backend & 52/52 Flutter tests passing |
| **Phase 6** | Notifications & Integrations | FCM / System | ⏳ PLANNED | Push alerts, webhooks, third-party sync |
| **Phase 7** | System Hardening & Deployment | Infrastructure | ⏳ PLANNED | Security audit, performance tuning, production setup |

---

## Phase 4 Implementation Breakdown

| Component | Status | Details |
|-----------|--------|---------|
| Approved Dependencies | ✅ IMPLEMENTED | `flutter_riverpod`, `riverpod_annotation`, `go_router`, `dio`, `flutter_secure_storage`, `intl`, `equatable` |
| Consumer Design System | ✅ IMPLEMENTED | Fresh Emerald Green (`#0D9488`) & Mint palette, Material 3 `AppTheme`, custom typography, reusable `AvenzoButton` & `AvenzoTextField` |
| Secure Storage & Tokens | ✅ IMPLEMENTED | `SecureStorageService` wrapping `flutter_secure_storage` for JWT `access_token` and `refresh_token` persistence via secure platform-backed storage using Android Keystore/EncryptedSharedPreferences and iOS Keychain |
| ApiClient & Token Refresh | ✅ IMPLEMENTED | `ApiClient` wrapping Dio with `AuthInterceptor` handling Bearer token injection and queued 401 refresh flow via `/api/v1/auth/refresh` |
| Consumer Role Validation | ✅ IMPLEMENTED | `AuthRepository` and `AuthNotifier` validating authenticated profile via backend `GET /api/v1/auth/me`. Rejects non-CONSUMER roles (`STAFF`, `ADMIN`), revokes session, and presents clear error UI |
| Router & Auth Guards | ✅ IMPLEMENTED | `GoRouter` setup with `/splash`, `/login`, `/register`, and `StatefulShellRoute` protecting consumer screens |
| Consumer Screens & Shells | ✅ IMPLEMENTED | `SplashScreen`, `LoginScreen`, `RegisterScreen`, `BottomNavShell`, `HomeDashboardScreen`, `PantryScreenShell` (planned backend notice), `ScannerScreenShell` (scanner placeholder), `ExpiryScreenShell` (tracking notice), and `ProfileScreen` |
| Test Suite & Verification | ✅ IMPLEMENTED | 11/11 tests passing (`flutter test`), 0 issues in `flutter analyze` |
| Deferred Features | ⏳ PLANNED | Digital Pantry CRUD, Live Barcode Scanner, OCR Label Extraction, Push Notifications (deferred to Phases 5 & 6) |

---

*AVENZO Project Status — Phase 4 Complete*
