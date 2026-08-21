# Agent-X Test Script (PowerShell)
Write-Host "Running Agent-X Test Suites..." -ForegroundColor Cyan

# Run Python Tests
Write-Host "`n1. Running Python tests..." -ForegroundColor Yellow
pytest tests/ --cov=agentx --cov=agentx_common --cov-report=term-missing

# Run Frontend Typecheck
Write-Host "`n2. Running TypeScript typecheck..." -ForegroundColor Yellow
npm run typecheck

Write-Host "`nAll test suites passed successfully!" -ForegroundColor Green
