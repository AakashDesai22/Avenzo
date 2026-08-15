# AVENZO — Deployment Plan

> Document Status: **DRAFT — Foundation Phase**
> Last Updated: 2026-08-15
> ⚠️ DO NOT deploy anything yet. This is a planning document only.

---

## Overview

This document outlines potential future deployment strategies for the AVENZO platform. No deployment decisions have been finalized. The platform is currently in development (Phase 0).

---

## Architecture Components to Deploy

| Component | Technology | Deployment Unit |
|-----------|-----------|----------------|
| Backend API | FastAPI + Python | Docker container / WSGI server |
| AI Service | FastAPI + Python | Docker container |
| Business Web | React + TypeScript | Static files (CDN/hosting) |
| Consumer App | Flutter | APK (Android) / IPA (iOS) |
| Database | PostgreSQL | Managed DB or self-hosted |
| Notifications | Firebase FCM | Google-managed (no hosting needed) |

---

## Deployment Options Under Consideration

### Option A — Hostinger (Available Account)

**Profile:** Web hosting + VPS provider

| Aspect | Notes |
|--------|-------|
| Backend API | VPS instance (Ubuntu) with Gunicorn + Nginx reverse proxy |
| AI Service | Same VPS or separate VPS (if resources allow) |
| Business Web | Hostinger static hosting or Nginx on VPS |
| Database | PostgreSQL on VPS or Hostinger managed DB (if available) |
| Cost | Existing account — check plan capabilities |
| Pros | Existing account, potentially lower cost |
| Cons | Less managed than cloud providers, manual maintenance |

**Required actions before using Hostinger:**
1. Review current Hostinger plan capabilities (VPS, database, storage)
2. Determine if a VPS plan exists or needs to be purchased
3. Confirm SSH access to server
4. DO NOT activate or modify Hostinger account until Phase 6

---

### Option B — Cloud Platforms (Free Tier)

| Provider | Backend | Database | Web | Notes |
|----------|---------|----------|-----|-------|
| **Railway** | ✅ Free tier | PostgreSQL included | ✅ | Simple deployment, generous free tier |
| **Render** | ✅ Free tier | PostgreSQL add-on | ✅ Static | Auto-deploy from GitHub |
| **Fly.io** | ✅ Free tier | External DB | — | Docker-native, good performance |
| **Supabase** | — | ✅ Free PostgreSQL | — | Managed PostgreSQL + extras |
| **Neon** | — | ✅ Free PostgreSQL | — | Serverless PostgreSQL |
| **Vercel** | ❌ (Python limited) | — | ✅ | Best for React frontend only |
| **Netlify** | ❌ (Python limited) | — | ✅ | Best for React frontend only |

---

### Option C — Cloud VPS (Paid)

| Provider | Notes |
|----------|-------|
| DigitalOcean Droplet | $6/month VPS, predictable pricing |
| AWS EC2 | Industry standard, free tier limited |
| Google Cloud Run | Serverless containers, pay-per-use |
| Azure App Service | Enterprise, student credits available |

---

### Option D — Hybrid Approach (Recommended for Academic Project)

```
Frontend (React)  →  Vercel (free)
Backend API       →  Railway / Render (free tier)
AI Service        →  Railway (separate service)
Database          →  Neon (free PostgreSQL)
Mobile App        →  Direct APK distribution (for demo)
Notifications     →  Firebase (free tier)
```

**Pros:** Zero cost, globally distributed, auto-deploy from GitHub
**Cons:** Free tier limitations (sleep on inactivity, storage limits)

---

## Mobile App Distribution

| Platform | Method | Notes |
|----------|--------|-------|
| Android | APK file | Direct install for demo |
| Android | Google Play | Requires developer account ($25 one-time) |
| iOS | TestFlight | Requires Apple Developer account ($99/year) |
| iOS | Direct IPA | Requires device registration |

**Recommendation:** Build and distribute Android APK directly for academic demonstration. iOS can be demonstrated via simulator.

---

## Deployment Checklist (Phase 6 — Not Yet)

- [ ] Finalize deployment platform decision
- [ ] Set up production environment variables (not stored in Git)
- [ ] Configure SSL/HTTPS (mandatory for production)
- [ ] Set up database backups
- [ ] Configure production logging and monitoring
- [ ] Set up CI/CD pipeline for automatic deployment
- [ ] Configure CORS for production domains
- [ ] Security audit before going live
- [ ] Load testing before public launch
- [ ] Configure Firebase for production

---

## Secrets Management (Production)

**Never store secrets in:**
- Source code
- Git repository
- Docker images

**Use instead:**
- Platform-specific environment variables (Railway, Render, etc.)
- Hostinger environment configuration
- `.env` files on VPS (never committed)
- Secret managers (AWS Secrets Manager, etc. — for scaled deployments)

---

## Estimated Timeline

| Phase | Target |
|-------|--------|
| Phase 0 (Foundation) | August 2026 |
| Phase 1 (Core Backend) | September 2026 |
| Phase 2 (Business Web) | October 2026 |
| Phase 3 (Consumer App) | November 2026 |
| Phase 4 (AI/ML) | November-December 2026 |
| Phase 5 (Integration) | December 2026 |
| Phase 6 (Deployment) | January 2027 |

*These are planning estimates only. Adjust based on actual progress.*

---

*Deployment Plan — AVENZO Phase 0 Foundation*
