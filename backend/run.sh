#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
pip install -q -r requirements.txt
[ -f data/developmentiq.db ] || python scripts/seed_database.py
exec uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
