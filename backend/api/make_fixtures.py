"""Generate contracts/fixtures/*.json from the Pydantic models (demo data, not model output)."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from backend.api.models import (Action, Assumption, AssetDetail, Backtest, Brief, FeedbackOut,
                                Line, LineAsset, Meta, Reason, Robustness)
from backend.engine import cost
from backend.params import load, val

OUT = Path(__file__).resolve().parents[2] / "contracts" / "fixtures"
MYT = timezone(timedelta(hours=8))
AT = datetime(2025, 10, 18, 19, 0, tzinfo=MYT)   # Saturday night; Sunday 06:00 is the planned stop
START, END = datetime(2025, 1, 1, tzinfo=MYT), datetime(2025, 12, 31, 23, tzinfo=MYT)
ASSETS = [("press_1", "Press 1", "press"), ("press_2", "Press 2", "press"),
          ("press_3", "Press 3", "press"), ("press_4", "Press 4", "press"),
          ("boiler_1", "Boiler 1", "boiler")]
RISK = {"press_1": 4.0, "press_2": 41.0, "press_3": 7.0, "press_4": 33.0, "boiler_1": 58.0}
STATUS = {"press_1": "ok", "press_2": "act", "press_3": "ok", "press_4": "watch", "boiler_1": "act"}
iso = lambda d: d.isoformat()


def reason(en, ms, signal, d, c):
    return Reason(text_en=en, text_ms=ms, signal=signal, direction=d, contribution=c)


def actions(p):
    price = val(p, "economics", "cpo_price_rm_per_t")
    mk = lambda fc: (cost.breakdown_cost(p, fc), cost.planned_cost(p, fc), cost.saved_if_acted(p, fc))
    b, pl, sv = mk("boiler_steam")
    boiler = Action(
        id="act_boiler_1_0001", asset_id="boiler_1", asset_name="Boiler 1", asset_type="boiler",
        fault_class="boiler_steam", risk_pct=58.0, horizon_h=24, rm_at_risk=b, rm_cost_to_act=pl,
        rm_saved_if_acted=sv, recommendation="fix_now", deadline=iso(AT + timedelta(hours=2)),
        headline_en="Boiler 1: steam temperature anomaly. Inspect now.",
        headline_ms="Dandang 1: anomali suhu stim. Periksa sekarang.",
        reasons=[
            reason("Steam temperature has run 18 °C below its normal band for 4 hours",
                   "Suhu stim 18 °C di bawah julat biasa selama 4 jam", "steam_temp", "down", 0.47),
            reason("Steam pressure is swinging twice as much as usual",
                   "Tekanan stim berayun dua kali ganda daripada biasa", "steam_pressure", "up", 0.33),
            reason("Feedwater flow is falling while the mill load is steady",
                   "Aliran air suapan menurun walaupun beban kilang stabil", "feedwater_flow", "down", 0.20)],
        why_rank_en=f"Boiler stops the whole mill: about RM{round(cost.rm_per_mill_hour(p)):,} of CPO at risk every hour",
        why_rank_ms=f"Dandang menghentikan seluruh kilang: kira-kira RM{round(cost.rm_per_mill_hour(p)):,} CPO berisiko setiap jam",
        criticality="whole_mill")
    b, pl, sv = mk("worm_wear")
    worm = Action(
        id="act_press_2_0001", asset_id="press_2", asset_name="Press 2", asset_type="press",
        fault_class="worm_wear", risk_pct=41.0, horizon_h=48, rm_at_risk=b, rm_cost_to_act=pl,
        rm_saved_if_acted=sv, recommendation="schedule_next_stop", deadline=iso(AT + timedelta(hours=11)),
        headline_en="Press 2: worm wear. Change the worm at tomorrow's 06:00 stop.",
        headline_ms="Penekan 2: haus skru cacing. Tukar skru pada henti terancang esok jam 06:00.",
        reasons=[
            reason("Motor current per tonne is 9% above Press 2's normal for 5 days",
                   "Arus motor setiap tan 9% lebih tinggi daripada biasa bagi Penekan 2 selama 5 hari",
                   "current_per_tonne", "up", 0.46),
            reason("Oil lost in fibre rose to 3.6% (alarm line is 4%)",
                   "Kehilangan minyak dalam serabut meningkat kepada 3.6% (garis amaran 4%)",
                   "fibre_oil_loss", "up", 0.31),
            reason("Worm has run 1,310 h since the last change; typical life is about 1,200 h",
                   "Skru cacing telah beroperasi 1,310 jam sejak penggantian terakhir; hayat biasa kira-kira 1,200 jam",
                   "hours_since_service", "up", 0.23)],
        why_rank_en="Costs less than the boiler alert, but the fix is cheap and fits the planned stop",
        why_rank_ms="Kos lebih rendah daripada amaran dandang, tetapi pembaikan murah dan muat dalam henti terancang",
        criticality="partial")
    b, pl, sv = mk("bearing")
    bearing = Action(
        id="act_press_4_0001", asset_id="press_4", asset_name="Press 4", asset_type="press",
        fault_class="bearing", risk_pct=33.0, horizon_h=72, rm_at_risk=b, rm_cost_to_act=pl,
        rm_saved_if_acted=sv, recommendation="monitor", deadline=iso(AT + timedelta(hours=36)),
        headline_en="Press 4: early bearing signs. Keep watching.",
        headline_ms="Penekan 4: tanda awal galas. Teruskan pemantauan.",
        reasons=[
            reason("Vibration kurtosis has risen for 3 days while RMS is still normal",
                   "Kurtosis getaran meningkat selama 3 hari manakala RMS masih normal", "vibration_kurtosis", "up", 0.58),
            reason("Gearbox oil temperature is 2 °C above its usual level",
                   "Suhu minyak gear 2 °C lebih tinggi daripada biasa", "gearbox_oil_temp", "up", 0.24),
            reason("Bearing has run 1,850 h since service",
                   "Galas telah beroperasi 1,850 jam sejak servis", "hours_since_service", "up", 0.18)],
        why_rank_en="One press is a quarter of the mill, so this ranks below the boiler and Press 2",
        why_rank_ms="Satu penekan ialah suku kilang, jadi ia berada di bawah dandang dan Penekan 2",
        criticality="partial")
    return [boiler, worm, bearing]


def line_assets():
    return [LineAsset(id=i, name=n, type=t, stage="utilities" if t == "boiler" else "pressing",
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
        defs = [("steam_temp", "Steam temperature", "Suhu stim", "°C", 420 - 18 * ramp + n(1.2)),
                ("steam_pressure", "Steam pressure", "Tekanan stim", "bar", 21 + n(0.15 + 0.5 * ramp)),
                ("feedwater_flow", "Feedwater flow", "Aliran air suapan", "t/h", 38 - 4 * ramp + n(0.5))]
    else:
        up = x ** 2 if asset_id == "press_2" else np.zeros(window_h)
        defs = [("current_per_tonne", "Motor current per tonne", "Arus motor setiap tan", "A/t",
                 4.2 * (1 + 0.09 * up) + n(0.04)),
                ("vibration_kurtosis", "Vibration kurtosis", "Kurtosis getaran", "",
                 3.0 + (1.2 * x if asset_id == "press_4" else 0) + n(0.12)),
                ("gearbox_oil_temp", "Gearbox oil temperature", "Suhu minyak gear", "°C",
                 62 + (2 * x if sick else 0) + n(0.4))]
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
    from backend.api.models import (PolicyCosts, PolicyResult, TimelineEvent, TimelinePoint)
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
    res, tl_events = [], {d: [] for d in range(365)}
    for k, lst in ev.items():
        daily = np.zeros(365)
        bd = pf = fa = 0
        dt = lost = 0.0
        for d, typ, a, fc in lst:
            daily[d] += price_cost[typ](fc)
            tl_events[d].append(TimelineEvent(policy=k, type=typ, asset_id=a))
            if typ == "breakdown":
                at_ = cost.asset_type(fc)
                bd += 1
                dt += cost.downtime_h(p, at_)
                lost += cost.lost_cpo_t(p, at_)
            pf += typ == "planned_fix"
            fa += typ == "false_alarm"
        cum[k] = np.cumsum(daily)
        res.append(dict(id=k, total_cost_rm=int(cum[k][-1]), breakdowns=bd, planned_stops=int(pf),
                        false_alarms=int(fa), downtime_h=dt, lost_cpo_t=round(lost, 1)))
    from backend.api.models import PolicyResult
    timeline = [TimelinePoint(t=iso(START + timedelta(days=d)),
                              cost=PolicyCosts(**{k: int(cum[k][d]) for k in cum}), events=tl_events[d])
                for d in range(365)]
    return Backtest(threshold=0.30, policies=[PolicyResult(**r) for r in res], timeline=timeline)


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
    write("backtest", backtest(p))
    write("assumptions", assumptions(p))
    write("robustness", Robustness(dataset="MetroPT-3", failures_total=4, caught=3, median_lead_h=11.0,
                                   false_alarms_per_week=0.8,
                                   note="PLACEHOLDER until the real MetroPT-3 run (plan step 8)."))
    write("feedback", FeedbackOut(ok=True))
    print("fixtures written to", OUT)


if __name__ == "__main__":
    main()
