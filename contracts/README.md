# Contract

- `api.ts`: TypeScript types, mirrors `backend/api/models.py`.
- `fixtures/*.json`: a snapshot of the real API (`make fixtures`, after `make all`). Fixture mode shows true numbers.
  - `meta`, `backtest`, `assumptions`, `robustness`, `faults`, `replay_markers`, `feedback` (POST response) are one file each.
  - Three demo moments, each with `brief`, `line` and `assets_<id>` (ids `press_1..press_4`, `boiler_1`):
    both-alerts night = no suffix (`brief.json`, `line.json`, `assets_press_2.json`), act-now = `_act`, quiet night = `_quiet` (brief and line only).
  - `bookmarks.json` lists the three `at` values. The stub serves the variant whose date matches `at` (default = both-alerts night).
- Run the stub API: `make api`, then open http://localhost:8000/docs (CORS is open).
- `cpo_price_rm` is the only non-integer money value (RM4,292.5/t). `backtest.timeline[].cost` is cumulative RM, one point per day; events are in the top-level `events` array. `GET /api/backtest` clamps inputs (cpo_price 3800-5000, miss_cost_mult 0.5-3, alert_budget 1-10, inspection_accuracy 0-1, default 0.5).
- Contract changes only via the backend, with a line in `CHANGELOG.md`.
