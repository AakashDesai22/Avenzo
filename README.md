# AVENZO

> **One Product. One Lifecycle. One Intelligence.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Foundation](https://img.shields.io/badge/Status-Foundation%20Setup-blue)]()
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)]()
[![Frontend: React+TS](https://img.shields.io/badge/Frontend-React%2BTypeScript-61dafb)]()
[![Mobile: Flutter](https://img.shields.io/badge/Mobile-Flutter-02569B)]()
[![AI: Python](https://img.shields.io/badge/AI-Python%20%7C%20scikit--learn-F7931E)]()

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Being Solved](#2-problem-being-solved)
3. [Core Concept](#3-core-concept)
4. [Business Platform](#4-business-platform)
5. [Consumer Application](#5-consumer-application)
6. [AI/ML Layer](#6-aiml-layer)
7. [Technology Stack](#7-technology-stack)
8. [High-Level Architecture](#8-high-level-architecture)
9. [Repository Structure](#9-repository-structure)
10. [Development Status](#10-development-status)
11. [Local Setup](#11-local-setup)
12. [Team Workflow](#12-team-workflow)
13. [Future Modules](#13-future-modules)

---

## 1. Project Overview

**AVENZO** is an AI-driven Product Lifecycle Intelligence Platform designed for inventory-intensive businesses and their consumers. It bridges the gap between warehouse operations and end-consumer product tracking by providing a single unified intelligence layer that covers the full product lifecycle — from supplier to digital pantry.

AVENZO is a final-year engineering project developed as a comprehensive demonstration of modern full-stack architecture, AI/ML integration, and mobile application development.

---

## 2. Problem Being Solved

Modern businesses face critical challenges in inventory management:

- **Product expiry waste** — Businesses lose significant revenue from expired stock that was not managed using FEFO (First Expired, First Out) principles
- **Stockout blind spots** — Demand spikes go unpredicted, leading to lost sales
- **Consumer expiry blindness** — Consumers have no intelligent system to track product expiry in their home
- **Disconnected lifecycle** — Supplier → Warehouse → Consumer operates in silos with no shared intelligence

AVENZO solves these problems by creating a connected, intelligent platform where every participant — supplier, business, and consumer — benefits from a shared lifecycle intelligence layer.

---

## 3. Core Concept

The AVENZO lifecycle:

```
Supplier
  → Product Creation
  → Batch Tracking (with manufacturing/expiry dates)
  → Warehouse Receiving
  → Inventory (FEFO-prioritized)
  → Order Fulfillment
  → Consumer Purchase
  → Digital Pantry (automatic product tracking)
  → Expiry Intelligence
  → AI Predictions & Recommendations
  → Business Feedback Loop
```

**AI is a decision-support layer.** It recommends; humans decide. AI does not silently modify authoritative database records.

---

## 4. Business Platform

The **Business/Staff Web Application** (React + TypeScript) provides:

| Module | Status |
|--------|--------|
| Inventory Management | 📋 PLANNED |
| Warehouse Management | 📋 PLANNED |
| Product & Category Management | 📋 PLANNED |
| Batch Tracking | 📋 PLANNED |
| Expiry Management | 📋 PLANNED |
| FEFO (First Expired, First Out) Ordering | 📋 PLANNED |
| Stock Receiving | 📋 PLANNED |
| Order Management | 📋 PLANNED |
| Business Analytics Dashboard | 📋 PLANNED |
| AI Recommendations Panel | 📋 PLANNED |
| Supplier Management | 📋 PLANNED |
| Risk Monitoring | 📋 PLANNED |
| User & Role Management | 📋 PLANNED |

---

## 5. Consumer Application

The **Consumer Mobile Application** (Flutter) provides:

| Feature | Status |
|---------|--------|
| Product Browsing & Search | 📋 PLANNED |
| Cart & Checkout | 📋 PLANNED |
| Order History | 📋 PLANNED |
| Digital Pantry | 📋 PLANNED |
| Manual Product Addition | 📋 PLANNED |
| Barcode/QR Code Scanning | 📋 PLANNED |
| OCR (Date & Product Extraction) | 📋 PLANNED |
| Expiry Tracking | 📋 PLANNED |
| Expiry Push Notifications | 📋 PLANNED |
| Product Lifecycle Information | 📋 PLANNED |

---

## 6. AI/ML Layer

The **AI Service** (Python + FastAPI + scikit-learn) provides:

| Capability | Status |
|-----------|--------|
| OCR — Product/Batch/Date Extraction | 📋 PLANNED |
| Demand Forecasting | 📋 PLANNED |
| Waste Prediction | 📋 PLANNED |
| Stockout Prediction | 📋 PLANNED |
| Overstock Prediction | 📋 PLANNED |
| Expiry Risk Scoring | 📋 PLANNED |
| Inventory Risk Scoring | 📋 PLANNED |
| Smart Reorder Recommendations | 📋 PLANNED |

> ⚠️ **AI Principle**: All AI outputs are advisory. Business rules and verified database records remain authoritative at all times. No AI model will silently modify critical inventory records.

---

## 7. Technology Stack

| Layer | Technology |
|-------|-----------|
| Consumer Mobile | Flutter + Dart |
| Business Web | React + TypeScript (Vite) |
| Backend API | Python + FastAPI |
| Database | PostgreSQL |
| AI/ML | Python, scikit-learn, Pandas, NumPy |
| OCR | TBD — lightweight, open-source approach |
| Notifications | Firebase Cloud Messaging (FCM) |
| Authentication | JWT (via FastAPI) |
| State Management (Flutter) | Riverpod |
| Version Control | Git + GitHub |
| Containerization | Docker (development environment) |

---

## 8. High-Level Architecture

```
                    AVENZO PLATFORM
                          |
         +----------------+----------------+
         |                                 |
  Consumer Mobile App              Business Web App
    (Flutter + Dart)              (React + TypeScript)
         |                                 |
         +----------------+----------------+
                          |
                     REST API (HTTPS)
                          |
                   FastAPI Backend
                   (Python 3.13+)
                          |
         +----------------+----------------+
         |                |                |
    PostgreSQL         AI Service      FCM Service
    (Database)    (Python + ML libs)  (Notifications)
```

**Core Principle:**
- Frontend layers NEVER access the database directly
- All data flows through the FastAPI backend
- AI service communicates through controlled backend interfaces
- Business logic resides primarily in the backend

---

## 9. Repository Structure

```
Avenzo/
│
├── README.md                    # This file
├── .gitignore                   # Comprehensive ignore rules
├── LICENSE                      # MIT License
├── CONTRIBUTING.md              # Contribution guidelines
├── CHANGELOG.md                 # Version history
├── .env.example                 # Environment variable template
│
├── docs/                        # All project documentation
│   ├── architecture/            # System architecture docs
│   ├── api/                     # API design and specifications
│   ├── database/                # Database schema documentation
│   ├── requirements/            # Functional/non-functional requirements
│   └── development/             # Developer guides and status
│
├── backend/                     # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py              # Application entry point
│   │   ├── core/                # Config, security, database
│   │   ├── api/                 # Route handlers (versioned)
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic services
│   │   ├── repositories/        # Database access layer
│   │   ├── middleware/          # Custom middleware
│   │   └── utils/               # Utility functions
│   ├── tests/                   # pytest test suite
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Backend container definition
│   └── .env.example             # Backend environment template
│
├── ai-service/                  # AI/ML Microservice
│   ├── app/
│   │   ├── main.py              # AI service entry point
│   │   ├── models/              # ML model wrappers
│   │   ├── services/            # Prediction services
│   │   ├── pipelines/           # Data pipelines
│   │   └── utils/               # Utility functions
│   ├── models/                  # Trained model artifacts (gitignored)
│   ├── notebooks/               # Jupyter exploration notebooks
│   ├── tests/                   # AI service tests
│   ├── requirements.txt         # AI dependencies
│   └── README.md                # AI service documentation
│
├── consumer-app/                # Flutter Mobile Application
│   ├── lib/
│   │   ├── main.dart            # App entry point
│   │   ├── app/                 # App configuration
│   │   ├── core/                # Core utilities, services, constants
│   │   ├── features/            # Feature modules
│   │   └── shared/              # Shared widgets and components
│   └── pubspec.yaml             # Flutter dependencies
│
├── business-web/                # React + TypeScript Web Application
│   ├── src/
│   │   ├── api/                 # API service layer
│   │   ├── components/          # Reusable components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── types/               # TypeScript type definitions
│   │   └── utils/               # Utility functions
│   └── package.json             # Node dependencies
│
├── database/                    # Database design and migrations
│   ├── migrations/              # Alembic migration files
│   ├── seeds/                   # Seed data scripts
│   ├── schema/                  # Schema documentation
│   └── README.md
│
├── infrastructure/              # Infrastructure configuration
│   ├── docker/                  # Docker compose files
│   ├── deployment/              # Deployment guides
│   └── README.md
│
├── scripts/                     # Setup and utility scripts
│
└── .github/                     # GitHub configuration
    ├── workflows/               # CI/CD workflows
    ├── ISSUE_TEMPLATE/          # Issue templates
    └── pull_request_template.md # PR template
```

---

## 10. Development Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0 — Foundation | ✅ IN PROGRESS | Repository, architecture, docs setup |
| Phase 1 — Core Backend | 📋 PLANNED | Auth, users, products, inventory APIs |
| Phase 2 — Business Web | 📋 PLANNED | React frontend for business operations |
| Phase 3 — Consumer App | 📋 PLANNED | Flutter mobile application |
| Phase 4 — AI/ML | 📋 PLANNED | Predictions and recommendations |
| Phase 5 — Integration | 📋 PLANNED | Full system integration and testing |
| Phase 6 — Deployment | 📋 PLANNED | Production deployment |

See [docs/development/PROJECT_STATUS.md](docs/development/PROJECT_STATUS.md) for detailed status tracking.

---

## 11. Local Setup

### Prerequisites

| Tool | Required Version | Install |
|------|-----------------|---------|
| Git | 2.x+ | [git-scm.com](https://git-scm.com) |
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18.x+ | [nodejs.org](https://nodejs.org) |
| Flutter | 3.x+ | [flutter.dev](https://flutter.dev) |
| Docker Desktop | Latest | [docker.com](https://docker.com) |
| PostgreSQL | 15+ | Via Docker (recommended) |

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/AakashDesai22/Avenzo.git
cd Avenzo

# 2. Set up backend
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
uvicorn app.main:app --reload --port 8000

# 3. Set up business web (new terminal)
cd business-web
npm install
cp .env.example .env.local
npm run dev

# 4. Set up consumer app (new terminal — requires Flutter installed)
cd consumer-app
flutter pub get
flutter run

# 5. Start databases with Docker (new terminal)
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml up -d
```

See [docs/development/DEVELOPMENT_GUIDE.md](docs/development/DEVELOPMENT_GUIDE.md) for detailed setup instructions.

---

## 12. Team Workflow

```
main branch        — stable, protected
develop branch     — integration branch
feature/*          — new features (from develop)
fix/*              — bug fixes
docs/*             — documentation updates
chore/*            — maintenance tasks
```

**Pull Request Process:**
1. Create a feature branch from `develop`
2. Implement changes with proper tests
3. Submit a PR against `develop`
4. Require at least one code review
5. Merge only when CI passes

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## 13. Future Modules

The following modules are planned for future development phases:

- **Advanced Analytics Dashboard** — Business intelligence with charts and KPIs
- **Demand Forecasting Engine** — ML-based predictions
- **Waste Reduction System** — AI-driven FEFO optimization
- **OCR Pipeline** — Automated product/batch/date extraction from images
- **Supplier Portal** — Self-service supplier interface
- **Mobile Barcode Scanning** — Real-time inventory scanning
- **Notification Engine** — Multi-channel expiry and reorder alerts
- **Audit Trail System** — Complete action logging
- **Report Generation** — Exportable business reports
- **Multi-warehouse Support** — Distributed inventory management

---

## Documentation

| Document | Description |
|----------|-------------|
| [System Architecture](docs/architecture/system-architecture.md) | Full technical architecture |
| [API Design](docs/api/api-design.md) | REST API specifications |
| [Database Schema](docs/database/schema.md) | Entity relationships and design |
| [Project Status](docs/development/PROJECT_STATUS.md) | Current development status |
| [Development Guide](docs/development/DEVELOPMENT_GUIDE.md) | Developer setup guide |
| [Deployment Plan](docs/infrastructure/deployment-plan.md) | Future deployment strategy |
| [Open Questions](docs/development/OPEN_QUESTIONS.md) | Pending architectural decisions |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

*AVENZO — One Product. One Lifecycle. One Intelligence.*
