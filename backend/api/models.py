"""API contract v1 (MASTER_PLAN section 7). contracts/api.ts mirrors this file."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

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
    asset_name_ms: str   # v1.9
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
    reasons: list[Reason] = Field(min_length=2, max_length=3)   # v1.12
    why_rank_en: str
    why_rank_ms: str
    criticality: Literal["whole_mill", "partial"]
    rm_breakdown_cost: int   # v1.7: full breakdown cost, explicit (the UI never divides)
    deadline_label_en: str
    deadline_label_ms: str
    window_label_en: str     # end of the v1.6 risk window, e.g. "before the next stop, Sunday 06:00"
    window_label_ms: str


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
    rm_protected_total: int   # v1.7: sum of rm_saved_if_acted over the actions shown
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
    name_ms: str   # v1.9


class Line(BaseModel):
    at: str
    assets: list[LineAsset]


class Series(BaseModel):
    signal: str
    label_en: str
    label_ms: str
    unit: str
    unit_ms: str = ""            # v1.9: unit in Malay where it is a word (hours -> jam)
    points: list[tuple[str, float]]
    limit: float | None = None   # v1.7: alarm line, if the signal has one
    summary_en: str = ""         # v1.7: e.g. "4.1 to 4.6 A/t over 7 days"
    summary_ms: str = ""


class AlertWindow(BaseModel):
    start: str
    end: str


class FailureEvent(BaseModel):
    t: str
    fault_class: FaultClass


Expected = Literal["up", "down", "unstable", "spike", "steady"]


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
    stop: Literal["none", "machine", "whole_mill"]   # v1.7
    lost_production: bool


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


class LastService(BaseModel):
    t: str
    what_en: str
    what_ms: str
    hours_since: float


class NextCheck(BaseModel):
    t: str
    label_en: str
    label_ms: str


class Outlook(BaseModel):
    """At-risk and cost figures for the most likely fault, present for every status (including ok)."""
    fault_class: FaultClass
    risk_pct: float
    horizon_h: int
    rm_breakdown_cost: int
    rm_at_risk: int
    rm_cost_to_act: int
    rm_saved_if_acted: int
    window_label_en: str
    window_label_ms: str
    note_en: str = ""   # v1.9: why a non-alert machine shows a saving, or that it was just repaired
    note_ms: str = ""
    handled_at: str | None = None   # v1.9b: time of the repair that closed the last alert (machine reads ok after it)


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
    last_service: LastService | None = None   # v1.7
    next_check: NextCheck | None = None
    outlook: Outlook | None = None


PolicyId = Literal["run_to_failure", "fixed_interval", "millguard", "schedule_plus_millguard"]


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
    schedule_plus_millguard: int


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


class RobustnessEntry(BaseModel):
    dataset: str
    task_en: str
    task_ms: str
    lead_min: int
    events_total: int
    events_caught: int
    precision_pct: float
    false_alarms_per_day: float
    split: str
    note: str


class ClassCatch(BaseModel):
    fault_class: FaultClass
    total: int
    caught: int
    median_lead_h: float


class TestMill(BaseModel):
    id: int
    by_fault_class: list[ClassCatch]
    false_alarms_per_week: float


class Robustness(BaseModel):
    dataset: str
    failures_total: int
    caught: int
    median_lead_h: float
    false_alarms_per_week: float
    note: str
    test_mill: TestMill | None = None   # v1.7: unseen mill 10, per fault class
    extra: list[RobustnessEntry] = []   # v1.6 additive: other real-data checks (may be empty)


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


class NotifyIn(BaseModel):
    at: str | None = None
    kind: Literal["alert", "brief", "schedule"]
    action_id: str | None = None   # v1.13: required when kind == "schedule"

    @model_validator(mode="after")
    def _need_action(self):
        if self.kind == "schedule" and not self.action_id:
            raise ValueError("action_id is required when kind is 'schedule'")
        return self


class NotifyOut(BaseModel):
    ok: bool
    sent: int


class NotifyStatus(BaseModel):
    enabled: bool
    channel: str
    subscribers: int


class AdviceIn(BaseModel):   # v1.10
    asset_id: str
    at: str | None = None
    lang: Literal["en", "ms"] = "en"


class AdviceSection(BaseModel):
    heading: str
    items: list[str]


class AdviceSource(BaseModel):
    label: str
    url: str | None = None


class AdviceOut(BaseModel):
    """Sections in order: Check first, Step by step, Safety, Parts and tools, Call the manufacturer if."""
    title: str
    sections: list[AdviceSection]
    sources: list[AdviceSource]
    disclaimer: str
    generated_at: str
    cached: bool          # true when served from the cache or a fixture; false when fresh or unavailable
    model: str
    message: str | None = None   # friendly text when advice is unavailable (no key, no network, no fault); sections is then empty
