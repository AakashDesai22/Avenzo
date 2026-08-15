# AVENZO — Development Guide

> For: Developers setting up AVENZO locally
> Last Updated: 2026-08-15

---

## Prerequisites

Install the following before starting:

| Tool | Version | Download |
|------|---------|----------|
| Git | 2.x+ | https://git-scm.com |
| Python | 3.11+ | https://python.org |
| pip | Latest | Included with Python |
| Node.js | 18.x+ | https://nodejs.org |
| Docker Desktop | Latest | https://docker.com |
| Flutter SDK | 3.x+ | https://flutter.dev |
| VS Code (recommended) | Latest | https://code.visualstudio.com |

---

## Step 1 — Clone Repository

```bash
git clone https://github.com/AakashDesai22/Avenzo.git
cd Avenzo
```

---

## Step 2 — Backend Setup

```bash
# Navigate to backend
cd backend

# Create Python virtual environment
python -m venv venv

# Activate venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your local values (see docs/database for DB config)

# Start the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API documentation (auto-generated): http://localhost:8000/docs
Health check: http://localhost:8000/health

---

## Step 3 — Database Setup (Docker)

> Requires Docker Desktop installed and running.

```bash
# From the project root:
cd infrastructure/docker

# Start PostgreSQL (and backend if desired)
docker compose -f docker-compose.dev.yml up -d postgres

# Verify PostgreSQL is running
docker compose -f docker-compose.dev.yml ps
```

The PostgreSQL database will be available at:
- Host: `localhost`
- Port: `5432`
- Database: `avenzo_db`
- Username: `avenzo_user`
- Password: (set in your `.env` file)

### Running Migrations (when Alembic is set up — Phase 1)

```bash
cd backend
alembic upgrade head
```

---

## Step 4 — Business Web Setup

```bash
cd business-web

# Install Node dependencies
npm install

# Configure environment
copy .env.example .env.local
# Edit VITE_API_BASE_URL to point to your backend

# Start development server
npm run dev
```

Business web will be available at: http://localhost:5173

---

## Step 5 — Consumer App Setup (Flutter)

> Requires Flutter SDK installed. Run `flutter doctor` to verify.

```bash
cd consumer-app

# Install Flutter dependencies
flutter pub get

# Run on connected device or emulator
flutter run
```

---

## Step 6 — AI Service Setup

```bash
cd ai-service

# Create Python virtual environment
python -m venv venv

# Activate venv
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env

# Start AI service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

AI service will be available at: http://localhost:8001

---

## Running Tests

### Backend Tests

```bash
cd backend
# Activate venv first
pytest tests/ -v
```

### Business Web Tests

```bash
cd business-web
npm run test
```

### Flutter Tests

```bash
cd consumer-app
flutter test
```

---

## Environment Variables

Each component has its own `.env.example`. Copy and configure before running:

| Component | File | Copy To |
|-----------|------|---------|
| Root | `.env.example` | `.env` |
| Backend | `backend/.env.example` | `backend/.env` |
| AI Service | `ai-service/.env.example` | `ai-service/.env` |
| Business Web | `business-web/.env.example` | `business-web/.env.local` |

**NEVER commit `.env` files to Git.**

---

## Branch Workflow

```bash
# Start a new feature
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes, commit often
git add .
git commit -m "feat(scope): descriptive message"

# Push and open PR
git push origin feature/your-feature-name
# Then open PR against 'develop' on GitHub
```

---

## Useful Commands Reference

### Backend
```bash
uvicorn app.main:app --reload --port 8000    # Start backend
pytest tests/ -v                              # Run all tests
alembic revision --autogenerate -m "msg"      # Create migration (Phase 1+)
alembic upgrade head                          # Apply migrations
```

### Business Web
```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run test         # Run tests
```

### Flutter
```bash
flutter pub get      # Install dependencies
flutter run          # Run on device/emulator
flutter test         # Run tests
flutter build apk    # Build Android APK
flutter doctor       # Check environment
```

### Docker
```bash
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d     # Start all services
docker compose -f infrastructure/docker/docker-compose.dev.yml down       # Stop all services
docker compose -f infrastructure/docker/docker-compose.dev.yml logs -f    # View logs
```

---

## VS Code Recommended Extensions

- Python (Microsoft)
- Pylance
- ESLint
- Prettier
- Flutter
- Dart
- Docker
- GitLens
- REST Client (for API testing)

---

*Development Guide — AVENZO*
