#!/usr/bin/env bash
# =============================================================================
# AVENZO — Development Setup Script (Unix/Mac/Linux)
# Run this script once to set up your local development environment.
# =============================================================================

set -e

echo "======================================"
echo "  AVENZO — Development Setup"
echo "======================================"
echo ""

# Check prerequisites
command -v git >/dev/null 2>&1 || { echo "ERROR: git not found. Install git first."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found. Install Python 3.11+."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "ERROR: node not found. Install Node.js 18+."; exit 1; }

echo "✅ Prerequisites found"
echo ""

# Setup Backend
echo "--- Setting up Backend ---"
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  backend/.env created from .env.example — please edit with real values"
fi
deactivate
cd ..
echo "✅ Backend setup complete"
echo ""

# Setup AI Service
echo "--- Setting up AI Service ---"
cd ai-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || true
fi
deactivate
cd ..
echo "✅ AI Service setup complete"
echo ""

# Setup Business Web
echo "--- Setting up Business Web ---"
cd business-web
npm install
if [ ! -f ".env.local" ]; then
    cp .env.example .env.local
    echo "⚠️  business-web/.env.local created from .env.example — please edit with real values"
fi
cd ..
echo "✅ Business Web setup complete"
echo ""

echo "======================================"
echo "  Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your database credentials"
echo "  2. Start PostgreSQL: docker compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres"
echo "  3. Start Backend:    cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  4. Start Web:        cd business-web && npm run dev"
echo ""
echo "See docs/development/DEVELOPMENT_GUIDE.md for full instructions."
