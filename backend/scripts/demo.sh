#!/bin/sh
# Start the API and the Telegram bot together; Ctrl+C stops both.
PY=${1:-.venv/bin/python}
export MILLGUARD_STATE_FILE=backend/data/state.json   # API and bot are two processes: share state through a file
export LIVE_AUTONOTIFY=${LIVE_AUTONOTIFY:-1}
$PY -m backend.scripts.reset_demo_state   # a fresh demo may send the same alerts again; subscribers stay
$PY -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &
API=$!
trap 'kill $API 2>/dev/null' EXIT INT TERM
# restart the bot if it dies (network drop); it exits at once when there is no token
while kill -0 $API 2>/dev/null; do
    $PY -m backend.notify.telegram_bot
    case $? in 3|4) wait $API;; esac   # 3 = no token, 4 = another bot has the token: keep only the API
    sleep 5
done
