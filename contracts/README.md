# Contract

- `api.ts`: TypeScript types, mirrors `backend/api/models.py`.
- `fixtures/*.json`: one file per endpoint, generated from the Pydantic models (`make fixtures`).
  - `meta.json`, `brief.json`, `line.json`, `backtest.json`, `assumptions.json`, `robustness.json`, `brief_quiet.json`, `line_quiet.json`, `replay_markers.json`, `feedback.json` (response of POST).
  - `assets_<id>.json` is `GET /api/assets/<id>`; ids: `press_1..press_4`, `boiler_1`.
  - Fixtures are sample data (not pipeline output). `brief.json`/`line.json` are at `at = 2025-01-14T19:00+08:00`; `brief_quiet.json`/`line_quiet.json` are the quiet night (2025-01-11). The stub serves the quiet pair when `at` starts with 2025-01-11. Replay window is 2025-01-01 to 2025-12-31.
- Run the stub API: `make api`, then open http://localhost:8000/docs (CORS is open).
- `cpo_price_rm` is the only non-integer money value (RM4,292.5/t). `backtest.timeline[].cost` is cumulative RM, one point per day; events are in the top-level `events` array. `GET /api/backtest` clamps inputs (cpo_price 3800-5000, miss_cost_mult 0.5-3, alert_budget 1-10).
- Contract changes only via the backend, with a line in `CHANGELOG.md`.
