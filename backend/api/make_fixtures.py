"""Generate contracts/fixtures/*.json from the Pydantic models (demo data, not model output)."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from backend.api.models import (Action, Marker, Assumption, AssetDetail, Backtest, Brief, FeedbackOut,
                                Line, LineAsset, Meta, Reason, Robustness)
from backend.engine import cost, text
from backend.params import load, val

OUT = Path(__file__).resolve().parents[2] / "contracts" / "fixtures"
MYT = timezone(timedelta(hours=8))
AT = datetime(2025, 1, 14, 19, 0, tzinfo=MYT)   # boiler + press night; markers use 11, 13, 14 Jan
START, END = datetime(2025, 1, 1, tzinfo=MYT), datetime(2025, 12, 31, 23, tzinfo=MYT)
TARGET = {"run_to_failure": 1_240_000, "fixed_interval": 780_000, "millguard": 412_000}   # plan v1.3 sample totals
ASSETS = [("press_1", "Press 1", "press"), ("press_2", "Press 2", "press"),
          ("press_3", "Press 3", "press"), ("press_4", "Press 4", "press"),
          ("boiler_1", "Boiler 1", "boiler")]
RISK = {"press_1": 4.0, "press_2": 41.0, "press_3": 7.0, "press_4": 33.0, "boiler_1": 28.0}
STATUS = {"press_1": "ok", "press_2": "act", "press_3": "ok", "press_4": "watch", "boiler_1": "act"}
iso = lambda d: d.isoformat()


def reason(en, ms, signal, d, c):
    return Reason(text_en=en, text_ms=ms, signal=signal, direction=d, contribution=c)


def build_action(aid, asset_id, name, atype, fc, risk, horizon, at_risk, cost_to_act, rec, deadline, crit, t):
    reasons = [Reason(text_en=en, text_ms=ms, signal=sig, direction=d, contribution=c)
               for sig, d, c, en, ms in t["reasons"]]
    return Action(id=aid, asset_id=asset_id, asset_name=name, asset_type=atype, fault_class=fc,
                  risk_pct=risk, horizon_h=horizon, rm_at_risk=at_risk, rm_cost_to_act=cost_to_act,
                  rm_saved_if_acted=at_risk - cost_to_act, recommendation=rec, deadline=iso(deadline),
                  headline_en=t["headline_en"], headline_ms=t["headline_ms"], reasons=reasons,
                  why_rank_en=t["why_rank_en"], why_rank_ms=t["why_rank_ms"], criticality=crit)


def actions(p):
    """Fixture numbers are hand-set samples (plan v1.3); real values come from the pipeline."""
    return [
        build_action("act_boiler_1_0001", "boiler_1", "Boiler 1", "boiler", "boiler_steam", 28.0, 24,
                     61000, 3000, "fix_now", AT.replace(hour=23), "whole_mill", text.BOILER_1),
        build_action("act_press_2_0001", "press_2", "Press 2", "press", "worm_wear", 41.0, 48,
                     21000, 3000, "schedule_next_stop", (AT + timedelta(days=1)).replace(hour=6),
                     "partial", text.PRESS_2_WORM)]


def line_assets():
    return [LineAsset(id=i, name=n, type=t, stage=t, position=0 if t == "boiler" else int(i[-1]),
                      status=STATUS[i], risk_pct=RISK[i]) for i, n, t in ASSETS]


def series(asset_id, window_h=168):
    rng = np.random.default_rng(7 if asset_id == "press_2" else 11)
    ts = [AT - timedelta(hours=window_h - 1 - k) for k in range(window_h)]
    x = np.linspace(0, 1, window_h)
    sick = STATUS[asset_id] != "ok"
    n = lambda s: rng.normal(0, s, window_h)
    pts = lambda v: [(iso(t), round(float(a), 3)) for t, a in zip(ts, v)]
    if asset_id == "boiler_1":
        ramp = np.clip((x - 0.8) / 0.2, 0, 1)
        vals = {"steam_temp": 538 - 16 * ramp + n(1.0), "steam_pressure": 21 + n(0.15 + 0.5 * ramp),
                "feedwater_flow": 38 - 4 * ramp + n(0.5)}
    else:
        up = x ** 2 if asset_id == "press_2" else np.zeros(window_h)
        vals = {"current_per_tonne": 4.2 * (1 + 0.09 * up) + n(0.04),
                "vibration_kurtosis": 3.0 + (1.2 * x if asset_id == "press_4" else 0) + n(0.12),
                "gearbox_oil_temp": 62 + (2 * x if sick else 0) + n(0.4)}
    defs = [(k, *text.SERIES[k], v) for k, v in vals.items()]
    from backend.api.models import Series
    return [Series(signal=s, label_en=en, label_ms=ms, unit=u, points=pts(v)) for s, en, ms, u, v in defs]


def asset_detail(asset_id, acts):
    from backend.api.models import AlertWindow, FailureEvent
    a = next(x for x in line_assets() if x.id == asset_id)
    action = next((x for x in acts if x.asset_id == asset_id), None)
    windows = [AlertWindow(start=iso(AT - timedelta(hours=9)), end=iso(AT))] if action else []
    fails = [FailureEvent(t=iso(AT - timedelta(days=41, hours=3)), fault_class="bearing")] if asset_id == "press_2" else []
    return AssetDetail(asset=a, series=series(asset_id), alert_windows=windows, failures=fails, action=action)


def backtest(p, cpo_price=None, miss_mult=1.0):
    from backend.api.models import (PolicyCosts, PolicyResult, BacktestEvent, TimelinePoint)
    rng = np.random.default_rng(42)
    classes = ["worm_wear", "bearing", "gearbox_shaft", "hydraulic_cone", "electrical"]
    w = [0.35, 0.20, 0.12, 0.13, 0.20]
    fails = []   # (day, asset_id, fault_class)
    for pid in range(1, 5):
        for d in sorted(rng.choice(365, 9, replace=False)):
            fails.append((int(d), f"press_{pid}", str(rng.choice(classes, p=w))))
    fails += [(118, "boiler_1", "boiler_steam"), (271, "boiler_1", "boiler_water")]
    fails.sort()
    ev = {k: [] for k in ("run_to_failure", "fixed_interval", "millguard")}   # (day, type, asset, fc)
    for d, a, fc in fails:
        ev["run_to_failure"].append((d, "breakdown", a, fc))
        prevented = rng.random() < (0.6 if fc == "worm_wear" else 0.1) and a != "boiler_1"
        ev["fixed_interval"].append((d, "planned_fix" if prevented else "breakdown", a, fc))
        caught = rng.random() < (0.9 if a == "boiler_1" else 0.74)
        ev["millguard"].append((max(d - 2, 0), "planned_fix" if caught else "breakdown", a, fc))
    for pid in range(1, 5):   # fixed schedule: worm change every ~1000 h per press
        for d in range(20 + 6 * pid, 365, 42):
            ev["fixed_interval"].append((d, "planned_fix", f"press_{pid}", "worm_wear"))
    for d in sorted(rng.choice(365, 22, replace=False)):
        ev["millguard"].append((int(d), "false_alarm", f"press_{rng.integers(1, 5)}", "unknown"))
    price = cpo_price or val(p, "economics", "cpo_price_rm_per_t")
    price_cost = {"breakdown": lambda fc: cost.breakdown_cost(p, fc, price, miss_mult),
                  "planned_fix": lambda fc: cost.planned_cost(p, fc),
                  "false_alarm": lambda fc: cost.false_alarm_cost(p)}
    cum = {k: np.zeros(365) for k in ev}
    res, events = [], []
    for k, lst in ev.items():
        daily = np.zeros(365)
        bd = pf = fa = 0
        dt = lost = 0.0
        for d, typ, a, fc in lst:
            daily[d] += price_cost[typ](fc)
            hour = (d * 7 + int(a[-1]) * 5) % 24
            events.append(BacktestEvent(t=iso(START + timedelta(days=d, hours=hour)), policy=k, type=typ, asset_id=a))
            if typ == "breakdown":
                at_ = cost.asset_type(fc)
                bd += 1
                dt += cost.downtime_h(p, at_)
                lost += cost.lost_cpo_t(p, at_)
            pf += typ == "planned_fix"
            fa += typ == "false_alarm"
        cum[k] = np.cumsum(daily)
        cum[k] = np.floor(cum[k] * TARGET[k] / cum[k][-1]) if not cpo_price and miss_mult == 1.0 else cum[k]
        if not cpo_price and miss_mult == 1.0:
            cum[k][-1] = TARGET[k]
        res.append(dict(id=k, total_cost_rm=int(cum[k][-1]), breakdowns=bd, planned_stops=int(pf),
                        false_alarms=int(fa), downtime_h=dt, lost_cpo_t=round(lost, 1)))
    from backend.api.models import PolicyResult
    timeline = [TimelinePoint(t=iso(START + timedelta(days=d)),
                              cost=PolicyCosts(**{k: int(cum[k][d]) for k in cum}))
                for d in range(365)]
    return Backtest(threshold=0.30, policies=[PolicyResult(**r) for r in res], timeline=timeline,
                    events=sorted(events, key=lambda e: e.t))


def markers(bt):
    M, names = text.MARKERS, {a: n for a, n, _ in ASSETS}
    day = lambda d: iso(datetime(2025, 1, d, 19, tzinfo=MYT))
    out = [Marker(t=day(11), kind="bookmark", label_en=M["quiet_en"], label_ms=M["quiet_ms"]),
           Marker(t=day(13), kind="bookmark", asset_id="press_2", label_en=M["onset_en"], label_ms=M["onset_ms"]),
           Marker(t=day(14), kind="bookmark", label_en=M["both_en"], label_ms=M["both_ms"])]
    for e in bt.events:
        nm = names[e.asset_id]
        if e.policy == "millguard" and e.type != "breakdown":
            out.append(Marker(t=e.t, kind="alert", asset_id=e.asset_id,
                              label_en=M["alert_en"].format(asset=nm), label_ms=M["alert_ms"].format(asset=nm)))
        if e.policy == "run_to_failure":
            out.append(Marker(t=e.t, kind="breakdown", asset_id=e.asset_id,
                              label_en=M["breakdown_en"].format(asset=nm), label_ms=M["breakdown_ms"].format(asset=nm)))
    return sorted(out, key=lambda m: m.t)


def assumptions(p):
    out = []
    for sec, items in p.items():
        for k, e in items.items():
            v = e["value"]
            out.append(Assumption(key=f"{sec}.{k}", label=k.replace("_", " ").capitalize(),
                                  value=v if isinstance(v, (int, float)) else ", ".join(map(str, v)),
                                  unit=e["unit"], source=e["source"],
                                  status="validated" if e["status"] == "validated" else "assumed"))
    return out


def meta(p):
    return Meta(mill={"name": "Demo Mill (mill 10)", "throughput_tph": val(p, "economics", "throughput_tph"),
                      "presses": 4, "oer": val(p, "economics", "oer"),
                      "cpo_price_rm": val(p, "economics", "cpo_price_rm_per_t")},
                replay={"start": iso(START), "end": iso(END), "step_h": 1},
                rm_per_mill_hour=round(cost.rm_per_mill_hour(p)))


def write(name, model):
    data = model.model_dump(mode="json") if hasattr(model, "model_dump") else [m.model_dump(mode="json") for m in model]
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p = load()
    acts = actions(p)
    write("meta", meta(p))
    write("brief", Brief(at=iso(AT), shift="night", actions=acts, watching_count=1, suppressed_count=3))
    write("line", Line(at=iso(AT), assets=line_assets()))
    for aid, _, _ in ASSETS:
        write(f"assets_{aid}", asset_detail(aid, acts))
    bt = backtest(p)
    write("backtest", bt)
    write("replay_markers", markers(bt))
    write("assumptions", assumptions(p))
    write("robustness", Robustness(dataset="MetroPT-3", failures_total=4, caught=3, median_lead_h=11.0,
                                   false_alarms_per_week=0.8,
                                   note="PLACEHOLDER until the real MetroPT-3 run (plan step 8)."))
    write("feedback", FeedbackOut(ok=True))
    write("brief_quiet", Brief(at=iso(AT.replace(day=11)), shift="night", actions=[], watching_count=1,
                               suppressed_count=3))
    quiet = [a.model_copy(update={"status": "ok", "risk_pct": 3.0}) for a in line_assets()]
    write("line_quiet", Line(at=iso(AT.replace(day=11)), assets=quiet))
    for a in acts:
        assert a.reasons[0].signal in {x.signal for x in series(a.asset_id)}, a.id
    print("fixtures written to", OUT)


if __name__ == "__main__":
    main()
