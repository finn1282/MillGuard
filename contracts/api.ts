// Mirrors backend/api/models.py. Do not edit by hand outside a contract change (see CHANGELOG.md).
// Times: ISO 8601 MYT (+08:00). Money: RM, integers (except cpo_price_rm).

export type FaultClass = "worm_wear" | "bearing" | "gearbox_shaft" | "hydraulic_cone"
  | "electrical" | "boiler_steam" | "boiler_water" | "unknown";
export type Recommendation = "fix_now" | "schedule_next_stop" | "monitor";
export type AssetStatus = "ok" | "watch" | "act";
export type PolicyId = "run_to_failure" | "fixed_interval" | "millguard" | "schedule_plus_millguard";

export interface Reason {
  text_en: string; text_ms: string; signal: string;
  direction: "up" | "down"; contribution: number; // 0..1
}

export interface Action {
  id: string; asset_id: string; asset_name: string; asset_name_ms: string /* v1.9 */; asset_type: "press" | "boiler";
  fault_class: FaultClass; risk_pct: number; horizon_h: number;
  rm_at_risk: number; rm_cost_to_act: number; rm_saved_if_acted: number;
  recommendation: Recommendation; deadline: string;
  headline_en: string; headline_ms: string;
  reasons: Reason[]; // 2 to 3 (v1.12); generic reasons are dropped, not padded
  why_rank_en: string; why_rank_ms: string;
  criticality: "whole_mill" | "partial";
  rm_breakdown_cost: number; // v1.7: full breakdown cost; the UI never divides
  deadline_label_en: string; deadline_label_ms: string;  // e.g. "tomorrow's 06:00 stop"
  window_label_en: string; window_label_ms: string;      // end of the risk window, e.g. "before the next stop, Sunday 06:00"
}

// GET /api/meta
export interface Meta {
  mill: { name: string; throughput_tph: number; presses: number; oer: number; cpo_price_rm: number };
  replay: { start: string; end: string; step_h: number };
  rm_per_mill_hour: number;
}

// GET /api/brief?at=
// v1.14 (additive): a sensor problem. Never a machine alert; it never changes a machine's status.
export interface SensorAlert {
  asset_id: string; signal: string; kind: "out_of_range" | "stuck" | "spike" | "missing";
  t: string; first_t: string; message_en: string; message_ms: string;
}
// v1.14 (additive): a sensor problem, never a machine alert; it never changes a machine's status.
export interface SensorAlert {
  asset_id: string; signal: string; kind: "out_of_range" | "stuck" | "spike" | "missing";
  t: string; first_t: string; // last and first bad reading of this issue
  message_en: string; message_ms: string; // e.g. "Press 4 vibration sensor looks faulty: check the sensor, not the machine"
}

export interface Brief {
  at: string; shift: "day" | "night";
  rm_protected_total: number; // v1.7: sum of rm_saved_if_acted of the actions shown
  actions: Action[]; // <=5, sorted by rm_saved_if_acted desc
  watching_count: number; suppressed_count: number;
  sensor_alerts?: SensorAlert[]; // v1.14
}

export interface LineAsset {
  id: string; name: string; type: "press" | "boiler";
  stage: "press" | "boiler"; position: number; // 1-4 for presses, 0 for boiler
  status: AssetStatus; risk_pct: number;
  summary_en: string; summary_ms: string; // v1.5, e.g. "Worm wearing" / "Normal"
  name_ms: string; // v1.9, e.g. "Penekan 2"
}

// GET /api/line?at=
export interface Line { at: string; assets: LineAsset[]; sensor_alerts?: SensorAlert[] /* v1.14 */ }

export interface Series {
  signal: string; label_en: string; label_ms: string; unit: string;
  points: [string, number][]; // [t, value]
  limit?: number | null; summary_en?: string; summary_ms?: string; // v1.7
  unit_ms?: string; // v1.9: Malay unit where it is a word (hours -> jam), else same as unit
}

// GET /api/assets/{id}?at=&window_h=168
export type Expected = "up" | "down" | "unstable" | "spike" | "steady";

export interface FingerprintCheck {
  signal: string; label_en: string; label_ms: string; expected: Expected;
  observed_en: string; observed_ms: string; matches: boolean;
}

export interface Diagnosis {
  fault_class: FaultClass; name_en: string; name_ms: string; confidence_pct: number;
  plain_en: string; plain_ms: string; // one sentence: what is physically happening
  alternatives: { fault_class: FaultClass; confidence_pct: number }[];
  fingerprint: FingerprintCheck[]; // 3-4 checks
}

export interface FixPlan {
  title_en: string; title_ms: string; steps_en: string[]; steps_ms: string[];
  parts: { name_en: string; name_ms: string; qty: number }[];
  crew: number; est_hours: number; needs_stop: boolean;
  stop: "none" | "machine" | "whole_mill"; lost_production: boolean; // v1.7
  best_window: string; // ISO: next planned stop if the plan is to schedule, else now
}

export interface HistoryItem {
  t: string; fault_class: FaultClass; what_en: string; what_ms: string;
  downtime_h: number; was_predicted: boolean;
}

// GET /api/faults -> FaultGuide[] (static)
export interface FaultGuide {
  fault_class: FaultClass; name_en: string; name_ms: string;
  what_en: string; what_ms: string; why_en: string; why_ms: string;
  signs: { signal: string; label_en: string; label_ms: string; expected: Expected }[];
  fix_steps_en: string[]; fix_steps_ms: string[];
  typical_downtime_h: number; typical_cost_rm: number; onset: "gradual" | "sudden";
}

// Money (v1.6): "wait" = skip this chance to fix it. fix_now: window = now -> next planned stop;
// schedule_next_stop: window = now -> the stop after the next (clipped to 168 h, the model horizon).
// horizon_h = that window; risk_pct = P(fail within it); rm_at_risk = risk x full breakdown cost
// (full = round(rm_at_risk / (risk_pct/100))); rm_saved_if_acted = max(0, rm_at_risk - rm_cost_to_act).
export interface AssetDetail {
  asset: LineAsset;
  status: AssetStatus; risk_pct: number;
  series: Series[];
  alert_windows: { start: string; end: string }[];
  failures: { t: string; fault_class: FaultClass }[];
  action: Action | null;
  diagnosis: Diagnosis | null; fix: FixPlan | null;
  history: HistoryItem[]; // last 12 months for this machine
  last_service?: { t: string; what_en: string; what_ms: string; hours_since: number } | null; // v1.7
  next_check?: { t: string; label_en: string; label_ms: string } | null;
  outlook?: Outlook | null; // v1.7: at-risk and cost figures for every status, including ok
}
export interface Outlook {
  fault_class: FaultClass; risk_pct: number; horizon_h: number; rm_breakdown_cost: number;
  rm_at_risk: number; rm_cost_to_act: number; rm_saved_if_acted: number;
  window_label_en: string; window_label_ms: string;
  handled_at?: string | null; /* v1.9b: repair time that closed the last alert; fade the chart after it */ note_en?: string; note_ms?: string; // v1.9: why a non-alert machine shows a saving, or that it was just repaired
}

export interface PolicyResult {
  id: PolicyId; total_cost_rm: number; breakdowns: number; planned_stops: number;
  false_alarms: number; downtime_h: number; lost_cpo_t: number;
}

export interface TimelinePoint {
  t: string; // daily, 365 points
  cost: { run_to_failure: number; fixed_interval: number; millguard: number; schedule_plus_millguard: number }; // cumulative RM
}

export interface BacktestEvent {
  t: string; // exact hourly timestamp
  policy: PolicyId; type: "breakdown" | "planned_fix" | "false_alarm"; asset_id: string;
}

// GET /api/backtest?cpo_price=&miss_cost_mult=&alert_budget=&compare=run_to_failure|fixed_interval|millguard_only&inspection_accuracy=
// inspection_accuracy (v1.6): 0-1, default 0.5 = chance a crew inspection finds the real fault when the predicted class was wrong.
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
export interface RobustnessEntry {
  dataset: string; task_en: string; task_ms: string;
  lead_min: number;                 // how far ahead the excursion is predicted
  events_total: number; events_caught: number;
  precision_pct: number; false_alarms_per_day: number;
  split: string; note: string;
}
export interface Robustness {
  dataset: string; failures_total: number; caught: number;
  median_lead_h: number; false_alarms_per_week: number; note: string;
  test_mill?: { id: number; by_fault_class: { fault_class: FaultClass; total: number; caught: number; median_lead_h: number }[];
                false_alarms_per_week: number } | null; // v1.7
  extra: RobustnessEntry[]; // v1.6, additive; may be empty
}

// POST /api/feedback
export interface FeedbackIn { action_id: string; useful?: boolean; decision?: Recommendation }
export interface FeedbackOut { ok: boolean }

// v1.8 (additive). POST /api/notify sends what the replay clock shows at `at` to Telegram subscribers.
// v1.13 (additive): kind "schedule" + action_id (required, else 422; 404 if the action is not in the brief at `at`) tells every subscriber
// the supervisor scheduled that action and records feedback "schedule_next_stop". Ignores alert dedupe and the shift budget.
export interface NotifyIn { at?: string; kind: "alert" | "brief" | "schedule"; action_id?: string }
export interface NotifyOut { ok: boolean; sent: number } // ok=false, sent=0 when the bot is not configured
// GET /api/notify/status. The "Send to phone" button is shown only when enabled.
export interface NotifyStatus { enabled: boolean; channel: string; subscribers: number }

// POST /api/advice (v1.10, LLM provider v1.11). Sections in order: Check first, Step by step, Safety, Parts and tools, Call the manufacturer if.
export interface AdviceIn { asset_id: string; at?: string | null; lang: "en" | "ms" }
export interface AdviceSection { heading: string; items: string[] }
export interface AdviceSource { label: string; url?: string | null }
export interface AdviceOut {
  title: string; sections: AdviceSection[]; sources: AdviceSource[]; disclaimer: string; generated_at: string;
  cached: boolean; // true = cache or fixture; false = fresh, or unavailable
  model: string;
  message?: string | null; // friendly text when unavailable (no key, no network, no fault); sections is then []
}

// ---- v1.14 gateway (additive). Write endpoints need header X-Demo-Key when the server has DEMO_KEY set (401 otherwise): ingest, live/start, live/stop, upload, notify, feedback.
// The client is the gateway: the Gateway page (or backend/scripts/stream.py) fetches hours and POSTs them to /api/ingest at its own pace.
// One hourly payload per asset, as a real ESP32 / Raspberry Pi / PLC gateway would send (vibration RMS and kurtosis computed at the edge).
// press_N readings: motor_current (A), throughput_tph, vib_rms (mm/s), vib_kurtosis, gearbox_oil_temp (C), cone_pressure (bar), fibre_oil_loss (%, daily lab value, null otherwise).
// boiler_1 readings: steam_temp (C), steam_pressure (bar), feedwater_flow (t/h), feedwater_cond (uS/cm). A null or missing field is allowed (counts as missing).
export interface ReadingIn {
  gateway_id: string; source: string; // "scenario:<id>" | "csv:<name>" | ...
  asset_id: "press_1" | "press_2" | "press_3" | "press_4" | "boiler_1";
  t: string; readings: Record<string, number | null>;
}
// POST /api/ingest  body: ReadingIn | ReadingIn[]   (bad payload: 422)
// Sensor-health checks per reading: out of physical range, stuck (identical 6+ h while running), spike (> 6 robust SD from the last 72 h), missing (3+ h).
// A bad reading raises a SensorAlert, never a machine alert.
export interface IngestOut { accepted: number; rejected: number; sensor_issues: SensorAlert[]; live_at: string | null }
// GET /api/live. live_at = latest hour for which all 5 assets were ingested in this session.
export interface LiveStatus {
  enabled: boolean; session_id: string | null; source: string | null; gateway_id: string | null; live_at: string | null;
  readings_ingested: number; seconds_since_last: number | null; sensor_issues: SensorAlert[];
}
// POST /api/live/start (replaces any running session), POST /api/live/stop (body empty, returns LiveStatus with enabled=false)
export interface LiveStartIn { scenario_id: string; start?: string | null; speed_s_per_h?: number } // speed: seconds of wall clock per simulated hour, used by the client to pace
export interface LiveSession { session_id: string; scenario_id: string; start_t: string; speed_s_per_h: number; started_wallclock: string }
// While a session is active, /api/brief, /api/line, /api/assets/{id} and /api/meta serve the session's scenario at live_at (the `at` argument is ignored; /api/backtest stays on mill 10);
// sensor_alerts are merged into brief and line. With no session nothing changes (mill10, replay clock).
// GET /api/scenarios, GET /api/scenarios/{id}/hours?from=<iso>&n=<int> -> ReadingIn[] (n hours x 5 assets, oldest first, n <= 168)
export interface Scenario {
  id: string; name_en: string; name_ms: string; description_en: string; description_ms: string;
  default_start: string; hours: number; upload_enabled: boolean; // upload_enabled false on Vercel
}
// POST /api/upload (multipart file, or a raw text/csv body with ?name=; CSV columns asset_id, t, then one column per reading; 422 if unreadable or under 400 hourly rows per asset). Local only: 501 on Vercel. Builds scenario "csv_<name>".
// POST /api/telegram/webhook (Telegram -> server, header X-Telegram-Bot-Api-Secret-Token; not for the frontend).
export interface UploadOut { scenario_id: string; rows: number; assets: number; issues: string[] }
