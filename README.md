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
