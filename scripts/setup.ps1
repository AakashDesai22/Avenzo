# =============================================================================
# AVENZO — Development Setup Script (Windows PowerShell)
# Run this script once to set up your local development environment.
# Usage: .\scripts\setup.ps1
# =============================================================================

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AVENZO - Development Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
function Test-Command($cmd) {
    $null = Get-Command $cmd -ErrorAction SilentlyContinue
    return $?
}

if (-not (Test-Command "git")) { Write-Error "git not found. Install git first."; exit 1 }
if (-not (Test-Command "python")) { Write-Error "python not found. Install Python 3.11+."; exit 1 }
if (-not (Test-Command "node")) { Write-Error "node not found. Install Node.js 18+."; exit 1 }

Write-Host "✅ Prerequisites found" -ForegroundColor Green
Write-Host ""

# Setup Backend
Write-Host "--- Setting up Backend ---" -ForegroundColor Yellow
Set-Location backend
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  backend\.env created - please edit with real values" -ForegroundColor Yellow
}
Set-Location ..
Write-Host "✅ Backend setup complete" -ForegroundColor Green
Write-Host ""

# Setup AI Service
Write-Host "--- Setting up AI Service ---" -ForegroundColor Yellow
Set-Location ai-service
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
Set-Location ..
Write-Host "✅ AI Service setup complete" -ForegroundColor Green
Write-Host ""

# Setup Business Web
Write-Host "--- Setting up Business Web ---" -ForegroundColor Yellow
Set-Location business-web
cmd /c "npm install"
if (-not (Test-Path ".env.local")) {
    Copy-Item ".env.example" ".env.local"
    Write-Host "⚠️  business-web\.env.local created - please edit with real values" -ForegroundColor Yellow
}
Set-Location ..
Write-Host "✅ Business Web setup complete" -ForegroundColor Green
Write-Host ""

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Edit backend\.env with your database credentials" -ForegroundColor Gray
Write-Host "  2. Install Docker Desktop for PostgreSQL" -ForegroundColor Gray
Write-Host "  3. Start Backend: cd backend; .\venv\Scripts\uvicorn.exe app.main:app --reload" -ForegroundColor Gray
Write-Host "  4. Start Web: cd business-web; cmd /c npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "See docs\development\DEVELOPMENT_GUIDE.md for full instructions." -ForegroundColor Gray
