# Agent-X Local Setup & Development Guide

Follow this guide to set up, run, and test Agent-X locally on your machine.

---

## 🛠️ Prerequisites

- **Python**: `3.12+`
- **uv**: Modern, fast Python package manager (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Node.js**: `20.x` or `22.x LTS`
- **npm**: `10.x+`
- **Git**

---

## 🚀 Quickstart Installation

### 1. Clone the Repository
```bash
git clone https://github.com/itsmesujan/Agent-X.git
cd Agent-X
```

### 2. Set Up Python Backend
```bash
# Sync and install all Python dependencies in virtualenv
uv sync

# Configure environment variables
cp .env.example .env
# Optional: Set your GEMINI_API_KEY in .env (if testing against live Gemini API)
```

### 3. Set Up Next.js Frontend
```bash
# Install root and workspace dependencies
npm install

# Verify Next.js build
npm run build
```

---

## 🧪 Running the Test Suite

Agent-X includes a comprehensive automated test suite with **162 passing tests**:

```bash
# Run all unit and integration tests
uv run pytest

# Run with coverage report
uv run pytest --cov=agentx --cov-report=term-missing

# Run code linter
uv run ruff check .

# Run TypeScript typecheck
npm run typecheck
```

---

## 💻 Running Locally

### Start Backend API Server
```bash
uv run uvicorn agentx.main:app --host 0.0.0.0 --port 8000 --reload
```
- OpenAPI Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/healthz`

### Start Mission Control PWA
```bash
npm run dev
```
- Mission Control Cockpit: `http://localhost:3000`
