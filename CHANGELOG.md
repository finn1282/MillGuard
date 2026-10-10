# Changelog

Contract or scope changes, one line each.

- 2026-10-10: repo skeleton created; API contract v1 as in MASTER_PLANv1.1.md section 7.
- 2026-10-10: contract v1 published: Pydantic models, contracts/api.ts, fixtures, stub API. Added params economics.unplanned_repair_multiplier (assumed 1.5).
- 2026-10-10: contract v1.1: /api/replay/markers; backtest timeline daily + top-level events; line stage press|boiler + position; feedback useful?/decision?; backtest inputs clamped.
- 2026-10-10: fixtures aligned to frontend (no contract change): Jan 2025 demo nights, brief_quiet/line_quiet, sample backtest totals, strings in backend/engine/text.py.
- 2026-10-10: real API live (artifacts-backed, still contract v1.1): GET /api/brief also accepts alert_budget; fixtures remain the fallback (MILLGUARD_STUB=1).
