# Agent-X Setup Script (PowerShell)
Write-Host "Setting up Agent-X Monorepo..." -ForegroundColor Cyan

# Install Node dependencies
Write-Host "`n1. Installing Node dependencies..." -ForegroundColor Yellow
npm install

# Setup Python Virtual Environment
Write-Host "`n2. Setting up Python environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e ".[dev]"

Write-Host "`nAgent-X setup complete!" -ForegroundColor Green
