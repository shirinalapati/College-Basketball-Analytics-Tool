#!/bin/bash
# Start DevelopmentIQ backend + frontend (macOS/Linux)
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== DevelopmentIQ ==="

# Backend
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
if [ ! -f data/developmentiq.db ]; then
  .venv/bin/python scripts/generate_demo_data.py
  .venv/bin/python scripts/seed_database.py
fi

if lsof -i :8000 >/dev/null 2>&1; then
  echo "Backend already on :8000"
else
  .venv/bin/uvicorn api.main:app --reload --host 127.0.0.1 --port 8000 &
  echo "Backend started → http://127.0.0.1:8000"
fi

# Frontend
cd "$ROOT/frontend"
[ -d node_modules ] || npm install
if lsof -i :5173 >/dev/null 2>&1; then
  echo "Frontend already on :5173"
else
  npm run dev &
  echo "Frontend started → http://localhost:5173"
fi

echo ""
echo "Open http://localhost:5173 in your browser."
echo "Press Ctrl+C to stop (may need: kill \$(lsof -t -i:5173) \$(lsof -t -i:8000))"

wait
