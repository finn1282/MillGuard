"""API contract v1 (MASTER_PLAN section 7). contracts/api.ts mirrors this file."""
from typing import Literal

from pydantic import BaseModel, Field

FaultClass = Literal["worm_wear", "bearing", "gearbox_shaft", "hydraulic_cone",
                     "electrical", "boiler_steam", "boiler_water", "unknown"]
Recommendation = Literal["fix_now", "schedule_next_stop", "monitor"]
AssetStatus = Literal["ok", "watch", "act"]


class Reason(BaseModel):
    text_en: str
    text_ms: str
    signal: str
    direction: Literal["up", "down"]
    contribution: float = Field(ge=0, le=1)


class Action(BaseModel):
    id: str
    asset_id: str
    asset_name: str
    asset_type: Literal["press", "boiler"]
    fault_class: FaultClass
    risk_pct: float
    horizon_h: int
    rm_at_risk: int
    rm_cost_to_act: int
    rm_saved_if_acted: int
    recommendation: Recommendation
    deadline: str
    headline_en: str
    headline_ms: str
    reasons: list[Reason] = Field(min_length=3, max_length=3)
    why_rank_en: str
    why_rank_ms: str
    criticality: Literal["whole_mill", "partial"]


class MillInfo(BaseModel):
    name: str
    throughput_tph: float
    presses: int
    oer: float
    cpo_price_rm: float


class ReplayInfo(BaseModel):
    start: str
    end: str
    step_h: int


class Meta(BaseModel):
    mill: MillInfo
    replay: ReplayInfo
    rm_per_mill_hour: int


class Brief(BaseModel):
    at: str
    shift: Literal["day", "night"]
    actions: list[Action] = Field(max_length=5)
    watching_count: int
    suppressed_count: int


class LineAsset(BaseModel):
    id: str
    name: str
    type: Literal["press", "boiler"]
    stage: Literal["press", "boiler"]
    position: int   # 1-4 for presses, 0 for boiler
    status: AssetStatus
    risk_pct: float
    summary_en: str
    summary_ms: str


class Line(BaseModel):
    at: str
    assets: list[LineAsset]


class Series(BaseModel):
    signal: str
    label_en: str
    label_ms: str
    unit: str
    points: list[tuple[str, float]]


class AlertWindow(BaseModel):
    start: str
    end: str


class FailureEvent(BaseModel):
    t: str
    fault_class: FaultClass


Expected = Literal["up", "down", "unstable", "spike"]


class FingerprintCheck(BaseModel):
    signal: str
    label_en: str
    label_ms: str
    expected: Expected
    observed_en: str
    observed_ms: str
    matches: bool


class Alternative(BaseModel):
    fault_class: FaultClass
    confidence_pct: float


class Diagnosis(BaseModel):
    fault_class: FaultClass
    name_en: str
    name_ms: str
    confidence_pct: float
    plain_en: str
    plain_ms: str
    alternatives: list[Alternative]
    fingerprint: list[FingerprintCheck] = Field(min_length=3, max_length=4)


class Part(BaseModel):
    name_en: str
    name_ms: str
    qty: int


class FixPlan(BaseModel):
    title_en: str
    title_ms: str
    steps_en: list[str]
    steps_ms: list[str]
    parts: list[Part]
    crew: int
    est_hours: float
    needs_stop: bool
    best_window: str


class HistoryItem(BaseModel):
    t: str
    fault_class: FaultClass
    what_en: str
    what_ms: str
    downtime_h: float
    was_predicted: bool


class Sign(BaseModel):
    signal: str
    label_en: str
    label_ms: str
    expected: Expected


class FaultGuide(BaseModel):
    fault_class: FaultClass
    name_en: str
    name_ms: str
    what_en: str
    what_ms: str
    why_en: str
    why_ms: str
    signs: list[Sign]
    fix_steps_en: list[str]
    fix_steps_ms: list[str]
    typical_downtime_h: float
    typical_cost_rm: int
    onset: Literal["gradual", "sudden"]


class AssetDetail(BaseModel):
    asset: LineAsset
    status: AssetStatus
    risk_pct: float
    series: list[Series]
    alert_windows: list[AlertWindow]
    failures: list[FailureEvent]
    action: Action | None
    diagnosis: Diagnosis | None
    fix: FixPlan | None
    history: list[HistoryItem]


PolicyId = Literal["run_to_failure", "fixed_interval", "millguard"]


class PolicyResult(BaseModel):
    id: PolicyId
    total_cost_rm: int
    breakdowns: int
    planned_stops: int
    false_alarms: int
    downtime_h: float
    lost_cpo_t: float


class PolicyCosts(BaseModel):
    run_to_failure: int
    fixed_interval: int
    millguard: int


class BacktestEvent(BaseModel):
    t: str   # exact hourly timestamp
    policy: PolicyId
    type: Literal["breakdown", "planned_fix", "false_alarm"]
    asset_id: str


class TimelinePoint(BaseModel):
    t: str   # daily, 365 points
    cost: PolicyCosts   # cumulative RM


class Backtest(BaseModel):
    threshold: float
    policies: list[PolicyResult]
    timeline: list[TimelinePoint]
    events: list[BacktestEvent]


class Assumption(BaseModel):
    key: str
    label: str
    value: float | str
    unit: str
    source: str
    status: Literal["validated", "assumed"]


class Robustness(BaseModel):
    dataset: str
    failures_total: int
    caught: int
    median_lead_h: float
    false_alarms_per_week: float
    note: str


class Marker(BaseModel):
    t: str
    kind: Literal["bookmark", "alert", "breakdown"]
    label_en: str
    label_ms: str
    asset_id: str | None = None


class FeedbackIn(BaseModel):
    action_id: str
    useful: bool | None = None
    decision: Recommendation | None = None


class FeedbackOut(BaseModel):
    ok: bool
