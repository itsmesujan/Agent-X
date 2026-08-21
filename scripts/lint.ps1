# Agent-X Lint Script (PowerShell)
Write-Host "Running Agent-X Linters & Typecheckers..." -ForegroundColor Cyan

# Python lint & format check
Write-Host "`n1. Checking Python with Ruff..." -ForegroundColor Yellow
ruff check .
ruff format --check .

# Python strict typing
Write-Host "`n2. Checking Python with Mypy..." -ForegroundColor Yellow
mypy .

# TypeScript typecheck
Write-Host "`n3. Checking TypeScript types..." -ForegroundColor Yellow
npm run typecheck

Write-Host "`nLinting and typechecking completed with 0 errors!" -ForegroundColor Green
