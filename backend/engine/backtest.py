"""Policy backtest: run-to-failure, fixed schedule (published RCM intervals, no tuning), MillGuard, schedule + MillGuard."""
import numpy as np
import pandas as pd

from backend.engine import cost, decide
from backend.params import val

T0 = pd.Timestamp("2025-01-01")
SCHEDULED = ["worm_wear", "bearing", "gearbox_shaft"]   # cone and electrical have no published interval: run to failure


def ev(t, policy, typ, asset, fc, c):
    return dict(t=pd.Timestamp(t), policy=policy, type=typ, asset_id=asset, fault_class=fc, cost=c)


def rtf_events(p, failures, cpo, miss):
    return [ev(r.t, "run_to_failure", "breakdown", r.asset_id, r.fault_class,
               cost.breakdown_cost(p, r.fault_class, cpo, miss)) for r in failures.itertuples()]


def fixed_events(p, mill, failures, lives, hidden, cpo, miss):
    """Counterfactual: worm, bearing and shaft are replaced at the first weekly stop after the published RCM interval
    (running hours); everything else runs to failure."""
    out = []
    interval = {c: val(p, "fixed_schedule", f"interval_h_{c}") for c in SCHEDULED}
    keep = failures[~failures.fault_class.isin(SCHEDULED)]
    out += [ev(r.t, "fixed_interval", "breakdown", r.asset_id, r.fault_class,
               cost.breakdown_cost(p, r.fault_class, cpo, miss)) for r in keep.itertuples()]
    for a in [f"press_{i}" for i in range(1, 5)]:
        h = hidden[(hidden.mill_id == mill) & (hidden.asset_id == a)].sort_values("t")
        times = pd.DatetimeIndex(h.t); C = np.cumsum(h.inc.values)
        stops = np.where((times.dayofweek == 6) & (times.hour == 6))[0]
        for c in SCHEDULED:
            lv = lives[(lives.mill_id == mill) & (lives.asset_id == a) & (lives.comp == c)].sort_values("k")
            life_seq, age0 = lv.life.values, float(lv.age0.iloc[0])
            base, k = -age0, 0
            while True:
                life = life_seq[k % len(life_seq)]
                f_idx = int(np.searchsorted(C, base + life))
                r_idx = int(np.searchsorted(C, base + interval[c]))
                s_pos = np.searchsorted(stops, r_idx)
                s_idx = int(stops[s_pos]) if s_pos < len(stops) else len(C)
                if f_idx >= len(C) and s_idx >= len(C):
                    break
                if f_idx <= s_idx:
                    out.append(ev(times[f_idx], "fixed_interval", "breakdown", a, c, cost.breakdown_cost(p, c, cpo, miss)))
                    base = C[f_idx]
                else:
                    out.append(ev(times[s_idx], "fixed_interval", "planned_fix", a, c, cost.planned_cost(p, c)))
                    base = C[s_idx]
                k += 1
    return out


def millguard_events(p, episodes, failures, cpo, miss):
    out, prevented = [], set()
    for e in episodes.itertuples():
        if e.outcome == "prevented":
            prevented.add((e.asset_id, e.fail_idx))
            c = cost.planned_cost(p, e.fault_class) + (e.rm_cost_to_act - cost.planned_cost(p, e.fault_class))
            out.append(ev(e.t_repair, "millguard", "planned_fix", e.asset_id, e.fault_class, c))
        elif e.outcome in ("false_alarm", "misclassified"):
            stop = e.rm_cost_to_act - cost.planned_cost(p, e.fault_class)
            out.append(ev(e.t_open, "millguard", "false_alarm", e.asset_id, e.fault_class,
                          cost.false_alarm_cost(p) + stop))
    for r in failures.itertuples():
        idx = int((r.t - T0) / pd.Timedelta(hours=1))
        if (r.asset_id, idx) not in prevented:
            out.append(ev(r.t, "millguard", "breakdown", r.asset_id, r.fault_class,
                          cost.breakdown_cost(p, r.fault_class, cpo, miss)))
    return out


def schedule_plus_events(p, mill, failures, lives, hidden, episodes, catch, cpo, miss):
    """The same published schedule plus MillGuard alerts for what fails in between.
    A breakdown of the schedule is caught if MillGuard prevented that same failure in its own run;
    breakdowns that only exist because the schedule changed the part's life are caught at the training-mill catch rate."""
    prevented = {(e.asset_id, e.fail_idx): e for e in episodes.itertuples() if e.outcome == "prevented"}
    original = {(r.asset_id, int((r.t - T0) / pd.Timedelta(hours=1))) for r in failures.itertuples()}
    rng = np.random.default_rng([mill or 0, 4])
    out = []
    for x in fixed_events(p, mill, failures, lives, hidden, cpo, miss):
        x = dict(x, policy="schedule_plus_millguard")
        if x["type"] == "breakdown":
            key = (x["asset_id"], int((x["t"] - T0) / pd.Timedelta(hours=1)))
            atype = cost.asset_type(x["fault_class"])
            if key in prevented:
                e = prevented[key]
                x.update(type="planned_fix", t=pd.Timestamp(e.t_repair), cost=e.rm_cost_to_act)
            elif key not in original and rng.random() < catch[atype]:
                x.update(type="planned_fix", t=x["t"] - pd.Timedelta(hours=24), cost=cost.planned_cost(p, x["fault_class"]))
        out.append(x)
    for e in episodes.itertuples():
        if e.outcome in ("false_alarm", "misclassified"):
            stop = e.rm_cost_to_act - cost.planned_cost(p, e.fault_class)
            out.append(ev(e.t_open, "schedule_plus_millguard", "false_alarm", e.asset_id, e.fault_class,
                          cost.false_alarm_cost(p) + stop))
    return out


POLICIES = ("run_to_failure", "fixed_interval", "millguard", "schedule_plus_millguard")


def summarize(p, events, policy):
    e = [x for x in events if x["policy"] == policy]
    bd = [x for x in e if x["type"] == "breakdown"]
    return dict(id=policy, total_cost_rm=int(sum(x["cost"] for x in e)), breakdowns=len(bd),
                planned_stops=sum(x["type"] == "planned_fix" for x in e),
                false_alarms=sum(x["type"] == "false_alarm" for x in e),
                downtime_h=float(sum(cost.downtime_h(p, cost.asset_type(x["fault_class"])) for x in bd)),
                lost_cpo_t=round(sum(cost.lost_cpo_t(p, cost.asset_type(x["fault_class"])) for x in bd), 1))


def timeline(events, days=365):
    idx = pd.date_range(T0, periods=days, freq="D")
    cols = {}
    for pol in POLICIES:
        daily = np.zeros(days)
        for x in events:
            if x["policy"] == pol:
                d = int((x["t"] - T0).days)
                if 0 <= d < days:
                    daily[d] += x["cost"]
        cols[pol] = np.cumsum(daily).astype(int)
    return [dict(t=idx[i], cost={k: int(v[i]) for k, v in cols.items()}) for i in range(days)]


def run_all_policies(p, mill, pred, failures, lives, hidden, k, budget=5, cpo=None, miss=1.0, trigger="p72",
                     plus=None):
    thr = {t: decide.risk_threshold(p, t, k[t], cpo, miss) for t in ("press", "boiler")}
    episodes = decide.run_mill(p, pred, failures, thr, budget, cpo, miss, mill, trigger)
    events = rtf_events(p, failures, cpo, miss) + fixed_events(p, mill, failures, lives, hidden, cpo, miss) \
        + millguard_events(p, episodes, failures, cpo, miss)
    if plus:
        events += schedule_plus_events(p, mill, failures, lives, hidden, episodes, plus["catch"], cpo, miss)
    return episodes, events, thr


def test_mill_table(ep, failures, mill=10):
    """Per fault class: failures, caught (prevented by an alert) and median lead time; plus false alarms per week."""
    prevented = {(e.asset_id, e.fail_idx): e for e in ep.itertuples() if e.outcome == "prevented"}
    rows = {}
    for r in failures.itertuples():
        idx = int((r.t - T0) / pd.Timedelta(hours=1))
        row = rows.setdefault(r.fault_class, dict(fault_class=r.fault_class, total=0, caught=0, leads=[]))
        row["total"] += 1
        e = prevented.get((r.asset_id, idx))
        if e is not None:
            row["caught"] += 1
            row["leads"].append((r.t - e.t_open) / pd.Timedelta(hours=1))
    by = [dict(fault_class=v["fault_class"], total=v["total"], caught=v["caught"],
               median_lead_h=round(float(np.median(v["leads"])), 1) if v["leads"] else 0.0)
          for v in sorted(rows.values(), key=lambda v: -v["total"])]
    fa = int(ep.outcome.isin(["false_alarm", "misclassified"]).sum()) if len(ep) else 0
    return dict(id=mill, by_fault_class=by, false_alarms_per_week=round(fa / (365 / 7), 2))
