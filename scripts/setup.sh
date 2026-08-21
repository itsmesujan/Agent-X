#!/usr/bin/env bash
set -e

echo "Setting up Agent-X Monorepo..."

# Install Node dependencies
echo "1. Installing Node dependencies..."
npm install

# Setup Python Virtual Environment
echo "2. Setting up Python environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

echo "Agent-X setup complete!"
