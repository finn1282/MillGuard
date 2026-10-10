# Contract

- `api.ts`: TypeScript types, mirrors `backend/api/models.py`.
- `fixtures/*.json`: a snapshot of the real API (`make fixtures`, after `make all`). Fixture mode shows true numbers.
  - `meta`, `backtest`, `assumptions`, `robustness`, `faults`, `replay_markers`, `feedback` (POST response) are one file each.
  - Three demo moments, each with `brief`, `line` and `assets_<id>` (ids `press_1..press_4`, `boiler_1`):
    whole-mill (boiler) moment = no suffix (`brief.json`, `line.json`, `assets_press_2.json`), act-now = `_act`, quiet night = `_quiet` (all three, including `assets_<id>_quiet.json`, so the Machine page on the quiet night shows calm data).
  - `bookmarks.json` lists the three `at` values. The stub serves the variant whose date matches `at` (default = the whole-mill moment).
- `fixtures/backtest_grid/` (offline sliders): one `GET /api/backtest` response per slider combination, 81 files, named by value:
  `cpo<price>_miss<mult>_bud<budget>_acc<accuracy>.json`, e.g. `cpo4292.5_miss1_bud5_acc0.5.json`. Values: cpo_price {3800, 4292.5, 5000} x miss_cost_mult {0.5, 1, 3} x alert_budget {3, 5, 10} x inspection_accuracy {0, 0.5, 1}.
  `index.json` has `axes` (the values) and `files` (file plus its four values). Snap each slider to the nearest axis value, build the name with JS `String(x)` (4292.5 -> "4292.5", 1 -> "1", 0.5 -> "0.5"), and fetch that file.
  The default combination equals `backtest.json`. Rebuilt by `make fixtures`.
- Run the stub API: `make api`, then open http://localhost:8000/docs (CORS is open).
- `cpo_price_rm` is the only non-integer money value (RM4,292.5/t). `backtest.timeline[].cost` is cumulative RM, one point per day; events are in the top-level `events` array. `GET /api/backtest` clamps inputs (cpo_price 3800-5000, miss_cost_mult 0.5-3, alert_budget 1-10, inspection_accuracy 0-1, default 0.5).
- Contract changes only via the backend, with a line in `CHANGELOG.md`.
