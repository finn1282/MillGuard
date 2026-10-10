# Contract

- `api.ts`: TypeScript types, mirrors `backend/api/models.py`.
- `fixtures/*.json`: one file per endpoint, generated from the Pydantic models (`make fixtures`).
  - `meta.json`, `brief.json`, `line.json`, `backtest.json`, `assumptions.json`, `robustness.json`, `feedback.json` (response of POST).
  - `assets_<id>.json` is `GET /api/assets/<id>`; ids: `press_1..press_4`, `boiler_1`.
  - Fixtures are demo data at `at = 2025-10-18T19:00+08:00`. Replay window is 2025-01-01 to 2025-12-31.
- Run the stub API: `make api`, then open http://localhost:8000/docs (CORS is open).
- `cpo_price_rm` is the only non-integer money value (RM4,292.5/t). `backtest.timeline[].cost` is cumulative RM, one point per day.
- Contract changes only via the backend, with a line in `CHANGELOG.md`.
