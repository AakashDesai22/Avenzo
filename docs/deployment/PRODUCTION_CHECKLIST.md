# AVENZO Production Deployment Security & Readiness Checklist

## 1. Secrets & Credentials Safety
- [x] Zero service-account keys or `.json` credential files tracked in Git repository.
- [x] Zero private keys or passwords in source code.
- [x] `.env` and `.env.*` listed in root and backend `.gitignore`.
- [x] `GOOGLE_APPLICATION_CREDENTIALS` points to external filepath outside repository root.
- [x] Production `JWT_SECRET` generated using strong cryptographic entropy (>64 chars).

## 2. Backend Security & Configuration
- [x] `APP_ENV=production` configured.
- [x] `APP_DEBUG=false` enforced (disables `/docs`, `/redoc`, and `/openapi.json`).
- [x] Database password and connection string verified for production DB instance.
- [x] CORS allowed origins restricted to trusted domain URLs (no wildcards `*`).
- [x] Pydantic settings strict model validation active (`validate_production_settings`).
- [x] Exception handlers sanitize internal error tracebacks and return safe 500 JSON responses.

## 3. Database & Migrations
- [x] Alembic migration chain verified (`alembic upgrade head`).
- [x] Foreign key indexes, cascade deletes, and unique constraints validated across all models.
- [x] User-based data isolation (ownership verification on `/pantry`, `/recommendations`, `/notifications`, `/devices`).

## 4. Firebase Cloud Messaging (FCM)
- [x] Firebase Admin SDK initialized with service account.
- [x] Automatic invalid token deactivation active (`UnregisteredError` -> `is_active=False`).
- [x] `select_default_fcm_provider()` enforces strict `RuntimeError` on missing credentials when `APP_ENV=production`.

## 5. Mobile App (Flutter Consumer)
- [x] `API_BASE_URL` injected at build-time via `--dart-define=API_BASE_URL=...`.
- [x] Auth token stored securely in `FlutterSecureStorage`.
- [x] Android permissions (`INTERNET`, `POST_NOTIFICATIONS`, `CAMERA`) verified in `AndroidManifest.xml`.
- [x] Android release APK successfully compiled (`flutter build apk --release`).
