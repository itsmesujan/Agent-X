#!/usr/bin/env bash
set -e

echo "Running Agent-X Linters & Typecheckers..."

# Python lint & format check
echo "1. Checking Python with Ruff..."
ruff check .
ruff format --check .

# Python strict typing
echo "2. Checking Python with Mypy..."
mypy .

# TypeScript typecheck
echo "3. Checking TypeScript types..."
npm run typecheck

echo "Linting and typechecking completed with 0 errors!"
