#!/bin/sh
# Last-resort demo: the frontend built in fixture mode and served from local files. No API, no bot, no network.
cd frontend && npm i --no-audit --no-fund >/dev/null && VITE_USE_FIXTURES=true npm run build && echo "Open http://localhost:4173" && npx vite preview --host --port 4173
