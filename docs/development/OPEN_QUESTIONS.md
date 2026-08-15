# AVENZO — Open Questions

> This document records architectural, technical, and business decisions that require confirmation before implementation.
> Any developer encountering an ambiguous decision should record it here.
> Last Updated: 2026-08-15

---

## Format

Each question follows this format:

**Q-XXX: Short Title**
- **Raised by:** [Person]
- **Date raised:** [Date]
- **Context:** Why this question matters
- **Options:** Possible approaches
- **Decision needed from:** [Person/Team]
- **Status:** OPEN / DECIDED / DEFERRED

---

## Open Questions

---

**Q-001: GitHub Repository Name and Visibility**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** GitHub CLI is not installed. The GitHub repository must be created manually.
- **Options:**
  1. Create repo at `https://github.com/AakashDesai22/Avenzo` (private)
  2. Create as a different name or different account
- **Decision needed from:** Aakash
- **Status:** OPEN — Action required: Create GitHub repository and run:
  ```
  git remote add origin https://github.com/AakashDesai22/Avenzo.git
  git push -u origin main
  ```

---

**Q-002: OCR Library Selection**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** OCR is required for product/batch/date extraction from consumer-scanned images. The project requires a lightweight, open-source approach.
- **Options:**
  1. **Tesseract + pytesseract** — Mature, offline, open-source, good for printed text
  2. **EasyOCR** — Deep learning based, better accuracy, heavier, open-source
  3. **PaddleOCR** — State-of-the-art, multilingual, open-source, heavier
  4. **Google Vision API** — Best accuracy, paid/quota-based, cloud dependency
- **Recommendation:** Start with Tesseract for foundation; upgrade to EasyOCR if accuracy is insufficient
- **Decision needed from:** Aakash
- **Status:** OPEN — Decide before Phase 4 (AI Service) begins

---

**Q-003: Object Storage Provider**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** Product images, batch documents, and OCR uploads will need cloud storage.
- **Options:**
  1. **Cloudflare R2** — Generous free tier, S3-compatible
  2. **AWS S3** — Industry standard, costs money
  3. **MinIO (self-hosted)** — Full control, requires server
  4. **Hostinger Object Storage** — If available on chosen Hostinger plan
  5. **Local filesystem** — Dev only, not production-ready
- **Decision needed from:** Aakash
- **Status:** OPEN — Decide before image upload features are built

---

**Q-004: Flutter SDK Installation**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** Flutter is not installed on the development machine. The consumer-app project structure has been created manually, but `flutter create` could not be run.
- **Action required:**
  1. Install Flutter SDK: https://docs.flutter.dev/get-started/install/windows/mobile
  2. Run `flutter doctor` to verify environment
  3. Run `flutter pub get` inside `consumer-app/`
- **Decision needed from:** Aakash
- **Status:** OPEN — Required before Phase 3 begins

---

**Q-005: Docker Desktop Installation**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** Docker is not installed. Docker Compose configuration for development has been created (PostgreSQL + Backend) but cannot be run yet.
- **Action required:**
  1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
  2. After install, test: `docker compose -f infrastructure/docker/docker-compose.dev.yml up -d`
- **Decision needed from:** Aakash
- **Status:** OPEN — Required before database development begins

---

**Q-006: PostgreSQL Development Approach**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** Before database migrations can run, a PostgreSQL instance must be available.
- **Options:**
  1. **Docker Compose** (recommended) — Isolated, version-locked, team-consistent
  2. **Local PostgreSQL install** — Direct install on Windows
  3. **Cloud PostgreSQL** — Free tier (Supabase, Neon) for early development
- **Recommendation:** Docker Compose approach (already configured)
- **Decision needed from:** Aakash
- **Status:** OPEN — Blocked on Q-005 (Docker installation)

---

**Q-007: Redis Inclusion**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** Redis may be needed for:
  - JWT refresh token invalidation (blacklisting)
  - Caching AI recommendations
  - Background task queues (Celery)
- **Options:**
  1. Include Redis from Phase 1 for token management
  2. Use PostgreSQL for token blacklisting initially, add Redis later
  3. Skip Redis entirely (simpler architecture)
- **Recommendation:** Use PostgreSQL for token management initially; add Redis only when caching or background jobs are needed
- **Decision needed from:** Aakash
- **Status:** OPEN — Decide before Phase 1 auth implementation

---

**Q-008: Background Task Handling**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** Some operations (sending notifications, running AI predictions, batch expiry checks) are async and long-running.
- **Options:**
  1. **FastAPI BackgroundTasks** — Simple, no extra infrastructure, limited
  2. **Celery + Redis** — Robust, scalable, distributed — more complex
  3. **ARQ (Async Redis Queue)** — Lighter Celery alternative
- **Recommendation:** Start with FastAPI BackgroundTasks; migrate to Celery if scale demands
- **Decision needed from:** Aakash
- **Status:** OPEN — Decide before notification and AI scheduling is implemented

---

**Q-009: Multi-warehouse Support Scope**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** The schema supports multiple warehouses. Does the initial implementation scope include:
  - Single warehouse (simpler FEFO logic)
  - Multiple warehouses from the start (cross-warehouse inventory)
- **Decision needed from:** Aakash
- **Status:** OPEN — Affects FEFO and inventory API design in Phase 1

---

**Q-010: Payment Integration**
- **Raised by:** Architecture Agent
- **Date raised:** 2026-08-15
- **Context:** Consumer orders imply payment. Payment integration is listed as "not in scope" for early phases.
- **Options:**
  1. Razorpay (India-focused)
  2. Stripe (international)
  3. COD (Cash on Delivery) only for initial build
  4. Mock payment for demo purposes
- **Recommendation:** COD + mock payment for demo; defer real payment integration
- **Decision needed from:** Aakash
- **Status:** OPEN — Decide before Phase 3 consumer checkout is built

---

## Decided Questions

*(None yet — all questions raised in Phase 0)*

---

## Deferred Questions

*(None yet)*

---

*Open Questions Document — AVENZO*
