#!/bin/sh
# Start the API and the Telegram bot together; Ctrl+C stops both.
PY=${1:-.venv/bin/python}
$PY -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &
API=$!
trap 'kill $API 2>/dev/null' EXIT INT TERM
$PY -m backend.notify.telegram_bot
# bot disabled (no token): keep the API running
wait $API
