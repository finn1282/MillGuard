# MillGuard

Predictive-maintenance copilot for palm-oil mills: one night-shift brief of what to fix, why, and what it saves in ringgit.
`MASTER_PLAN.md` is the single source of truth. Backend: `backend/` and `contracts/`. Frontend: `frontend/`.

## Run it (Python 3.11, macOS or Linux)

```sh
make setup      # uv venv + dependencies
make libomp     # macOS only, if LightGBM fails with "libomp.dylib not found" (or: brew install libomp)
make all        # simulate -> train -> tune on training mills -> mill-10 backtest -> artifacts -> MetroPT-3 (about 2 min)
make api        # http://localhost:8000/docs  (CORS open)
```

`make all` prints failures caught, median lead time, false alarms per week and total RM for each policy.
The MetroPT-3 step downloads about 220 MB from UCI the first time (`make fetch-metropt`); if it fails the rest still completes.

Other targets:

| Target | What it does |
| --- | --- |
| `make roi` | Low / base / high ROI table from the same backtest the app uses |
| `make report` | Prints the 3 demo bookmarks with each card's numbers and the 4-policy table (default and strict inspection) |
| `make fixtures` | Re-snapshots `contracts/fixtures/` from the real API (run after `make all`) |
| `MILLGUARD_STUB=1 make api` | Serves the fixtures instead of live artifacts (demo backup) |

## Telegram alerts (optional)

1. In Telegram, message @BotFather, send `/newbot`, and copy the token.
2. `cp backend/.env.example backend/.env` and paste the token after `TELEGRAM_BOT_TOKEN=` (the file is gitignored; never commit or share it).
   Optional: `TELEGRAM_ALLOWED_CHATS=` with comma-separated chat ids.
3. `make bot` (long polling, no public URL). Each person (or a group) sends `/start`; `/en` and `/bm` switch language, `/brief` sends the brief.
4. With `make api` running, the frontend (or `curl -X POST localhost:8000/api/notify -H 'content-type: application/json' -d '{"at":"2025-09-29T15:00:00+08:00","kind":"alert"}'`) sends what the replay clock shows. `GET /api/notify/status` says whether it is enabled.
5. Tapping Fix now / Schedule / Keep watching records feedback through the same code as `POST /api/feedback`.
Without a token everything still runs; `enabled` is false and nothing is sent.

## Demo checklist (`make demo`)

`make demo` starts the API (port 8000) and the Telegram bot together; Ctrl+C stops both.
1. `make all` has been run once on this machine (artifacts exist) and `make fixtures` output is committed.
2. `backend/.env` has the bot token; the demo group has sent `/start` (`GET /api/notify/status` shows `enabled: true`, `subscribers: 1+`).
3. Open the frontend; check the time bar bookmarks: Quiet night, Whole mill, Press 2 act now.
4. At Press 2 act now press "Send to phone"; tap Schedule on the phone.
5. Backup: `MILLGUARD_STUB=1 make demo` serves the real-snapshot fixtures if live artifacts are missing.
6. Slide assets: `make pitch` rewrites `pitch/` (charts, tables, `numbers.md`).

## How it is built

- `backend/sim/` simulator: 10 mills, calendar 2025, hourly; 4 presses + 1 boiler; hidden component lives; assumed P-F warning periods (`params.yaml`).
- `backend/features/`, `backend/models/` rolling features, LightGBM risk at 24/72/168 h (calibrated), Isolation Forest, fault classifier.
- `backend/engine/` decision layer (persistence, hysteresis, shift budget, fix-now vs schedule), cost engine, backtest of 4 policies, SHAP reasons (EN/BM templates), diagnosis and fault fingerprint, fix-plan playbook (`text.py`).
- `backend/api/` FastAPI + Pydantic contract; `contracts/api.ts` mirrors the models.
- `backend/robustness/` MetroPT-3 check. `backend/params.yaml` holds every number with its source and status (validated / assumed).

## Rules we keep

- Train on mills 1-9 before 2025-09-01; test on mill 10 and months 9-12. No random splits. Nothing is tuned on the test mill.
- Never commit `backend/data/`, `.env` or the boiler dataset (CC BY-NC-ND).
- Contract changes: edit the models, regenerate fixtures, one line in `CHANGELOG.md`.

## Honest limits

- Simulated mills; the warning periods and several economics are assumptions (marked `assumed`).
- MetroPT-3 (real compressor data): 0 of 4 failures caught before they started.
