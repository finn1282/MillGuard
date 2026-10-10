#!/bin/sh
# API + Telegram bot + frontend dev server (live API, no fixtures); Ctrl+C stops all.
PY=${1:-.venv/bin/python}
sh backend/scripts/demo.sh "$PY" &
DEMO=$!
trap 'kill $DEMO 2>/dev/null; pkill -P $DEMO 2>/dev/null' EXIT INT TERM
cd frontend && npm i --no-audit --no-fund && VITE_USE_FIXTURES=false VITE_API_URL=http://localhost:8000 npm run dev -- --host
