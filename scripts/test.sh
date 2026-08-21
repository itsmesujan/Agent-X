#!/usr/bin/env bash
set -e

echo "Running Agent-X Test Suites..."

# Run Python Tests
echo "1. Running Python tests..."
pytest tests/ --cov=agentx --cov=agentx_common --cov-report=term-missing

# Run Frontend Typecheck
echo "2. Running TypeScript typecheck..."
npm run typecheck

echo "All test suites passed successfully!"
