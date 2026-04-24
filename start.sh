#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v python >/dev/null 2>&1; then
  echo "Python is required but was not found."
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required but was not found."
  exit 1
fi

echo "Python version: $(python --version 2>&1)"
echo "Node version: $(node --version)"

if ! compgen -G "backend/models/*.pkl" >/dev/null; then
  echo "No trained model artifacts found. Running backend/train.py..."
  (cd backend && python train.py --data-dir ../data)
fi

cleanup() {
  if [[ -n "${FLASK_PID:-}" ]]; then
    kill "${FLASK_PID}" 2>/dev/null || true
    wait "${FLASK_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

(
  cd backend
  FLASK_ENV=development FLASK_PORT=5000 python app.py
) &
FLASK_PID=$!

echo "Started Flask backend with PID ${FLASK_PID}"

cd frontend
npm run dev
