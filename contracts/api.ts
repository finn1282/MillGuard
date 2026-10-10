// Mirrors backend/api/models.py. Do not edit by hand outside a contract change (see CHANGELOG.md).
// Times: ISO 8601 MYT (+08:00). Money: RM, integers (except cpo_price_rm).

export type FaultClass = "worm_wear" | "bearing" | "gearbox_shaft" | "hydraulic_cone"
  | "electrical" | "boiler_steam" | "boiler_water" | "unknown";
export type Recommendation = "fix_now" | "schedule_next_stop" | "monitor";
export type AssetStatus = "ok" | "watch" | "act";
export type PolicyId = "run_to_failure" | "fixed_interval" | "millguard";

export interface Reason {
  text_en: string; text_ms: string; signal: string;
  direction: "up" | "down"; contribution: number; // 0..1
}

export interface Action {
  id: string; asset_id: string; asset_name: string; asset_type: "press" | "boiler";
  fault_class: FaultClass; risk_pct: number; horizon_h: number;
  rm_at_risk: number; rm_cost_to_act: number; rm_saved_if_acted: number;
  recommendation: Recommendation; deadline: string;
  headline_en: string; headline_ms: string;
  reasons: Reason[]; // exactly 3
  why_rank_en: string; why_rank_ms: string;
  criticality: "whole_mill" | "partial";
}

// GET /api/meta
export interface Meta {
  mill: { name: string; throughput_tph: number; presses: number; oer: number; cpo_price_rm: number };
  replay: { start: string; end: string; step_h: number };
  rm_per_mill_hour: number;
}

// GET /api/brief?at=
export interface Brief {
  at: string; shift: "day" | "night";
  actions: Action[]; // <=5, sorted by rm_saved_if_acted desc
  watching_count: number; suppressed_count: number;
}

export interface LineAsset {
  id: string; name: string; type: "press" | "boiler";
  stage: "press" | "boiler"; position: number; // 1-4 for presses, 0 for boiler
  status: AssetStatus; risk_pct: number;
}

// GET /api/line?at=
export interface Line { at: string; assets: LineAsset[] }

export interface Series {
  signal: string; label_en: string; label_ms: string; unit: string;
  points: [string, number][]; // [t, value]
}

// GET /api/assets/{id}?at=&window_h=168
export interface AssetDetail {
  asset: LineAsset;
  series: Series[];
  alert_windows: { start: string; end: string }[];
  failures: { t: string; fault_class: FaultClass }[];
  action: Action | null;
}

export interface PolicyResult {
  id: PolicyId; total_cost_rm: number; breakdowns: number; planned_stops: number;
  false_alarms: number; downtime_h: number; lost_cpo_t: number;
}

export interface TimelinePoint {
  t: string; // daily, 365 points
  cost: { run_to_failure: number; fixed_interval: number; millguard: number }; // cumulative RM
}

export interface BacktestEvent {
  t: string; // exact hourly timestamp
  policy: PolicyId; type: "breakdown" | "planned_fix" | "false_alarm"; asset_id: string;
}

// GET /api/backtest?cpo_price=&miss_cost_mult=&alert_budget=&compare=run_to_failure|fixed_interval
// Inputs are clamped: cpo_price 3800-5000 (default 4292.5), miss_cost_mult 0.5-3 (1), alert_budget 1-10 (5).
export interface Backtest {
  threshold: number; policies: PolicyResult[]; timeline: TimelinePoint[]; events: BacktestEvent[];
}

// GET /api/replay/markers -> Marker[]
export interface Marker {
  t: string; kind: "bookmark" | "alert" | "breakdown";
  label_en: string; label_ms: string; asset_id?: string;
}

// GET /api/assumptions -> Assumption[]
export interface Assumption {
  key: string; label: string; value: number | string; unit: string;
  source: string; status: "validated" | "assumed";
}

// GET /api/robustness
export interface Robustness {
  dataset: string; failures_total: number; caught: number;
  median_lead_h: number; false_alarms_per_week: number; note: string;
}

// POST /api/feedback
export interface FeedbackIn { action_id: string; useful?: boolean; decision?: Recommendation }
export interface FeedbackOut { ok: boolean }
