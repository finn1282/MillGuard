# Changelog

Contract or scope changes, one line each.

- 2026-10-10: repo skeleton created; API contract v1 as in MASTER_PLANv1.1.md section 7.
- 2026-10-10: contract v1 published: Pydantic models, contracts/api.ts, fixtures, stub API. Added params economics.unplanned_repair_multiplier (assumed 1.5).
- 2026-10-10: contract v1.1: /api/replay/markers; backtest timeline daily + top-level events; line stage press|boiler + position; feedback useful?/decision?; backtest inputs clamped.
- 2026-10-10: fixtures aligned to frontend (no contract change): Jan 2025 demo nights, brief_quiet/line_quiet, sample backtest totals, strings in backend/engine/text.py.
- 2026-10-10: real API live (artifacts-backed, still contract v1.1, no contract change); fixtures remain the fallback (MILLGUARD_STUB=1).
- 2026-10-10: contract v1.5 (machine-first): diagnosis + fingerprint, fix plan, history, line summaries, GET /api/faults; money = expected loss, horizon_h = hours to deadline (Press 2 fixture 11 h). v1.4 policy schedule_plus_millguard still to come. Real API for the new fields follows.
- 2026-10-10: contract v1.4: policy schedule_plus_millguard in /api/backtest policies, timeline cost and events (PolicyId, PolicyCosts). Simulator now uses P-F ramps (assumed) and MPOB 2025 crop index; results re-run.
- 2026-10-10: contract v1.6: /api/backtest takes inspection_accuracy (0-1, default 0.5); money rule v1.6 (wait = skip this chance: fix_now window to next stop, schedule window clipped to 168 h); bookmarks re-picked by rule.
- 2026-10-10: contract v1.6 additions: Robustness.extra (RobustnessEntry[], additive, may be empty); risk_pct clipped at 99 everywhere (UI shows >=95 as '>95%'); fingerprint rule v2; whole-mill bookmark replaces both-alerts.
- 2026-10-10: contract v1.7 (additive): FingerprintCheck steady; Action rm_breakdown_cost + deadline/window labels; FixPlan stop + lost_production; asset last_service, next_check and outlook (at-risk/cost for every status; outlook is our additive shape for the ok-status figures); Series limit + summary; Brief rm_protected_total; Robustness.test_mill; backtest compare millguard_only (always 4 policies); abbreviations removed from text; fingerprint 'Not yet:' wording; breakdown-cost lines in /api/assumptions.
- 2026-10-10: contract v1.8 (additive): POST /api/notify {at, kind} -> {ok, sent}; GET /api/notify/status -> {enabled, channel, subscribers}. Telegram bot (make bot); risk_pct rounded once at the source; quiet-night asset fixtures.
