"""Three-policy backtest: run-to-failure, fixed interval (swept on training mills), MillGuard."""
import numpy as np
import pandas as pd

from backend.engine import cost, decide
from backend.params import val

T0 = pd.Timestamp("2025-01-01")
WEAR_OUT = ["worm_wear", "bearing", "gearbox_shaft", "hydraulic_cone"]
MEAN_LIFE = {"worm_wear": 1350.0, "bearing": 11500.0, "gearbox_shaft": 21000.0, "hydraulic_cone": 9500.0}


def ev(t, policy, typ, asset, fc, c):
    return dict(t=pd.Timestamp(t), policy=policy, type=typ, asset_id=asset, fault_class=fc, cost=c)


def rtf_events(p, failures, cpo, miss):
    return [ev(r.t, "run_to_failure", "breakdown", r.asset_id, r.fault_class,
               cost.breakdown_cost(p, r.fault_class, cpo, miss)) for r in failures.itertuples()]


def fixed_events(p, mill, failures, lives, hidden, frac, cpo, miss, t_end=None):
    """Counterfactual: wear-out parts are replaced at the first weekly stop after age >= frac*mean life."""
    out = []
    keep = failures[~failures.fault_class.isin(WEAR_OUT)]
    out += [ev(r.t, "fixed_interval", "breakdown", r.asset_id, r.fault_class,
               cost.breakdown_cost(p, r.fault_class, cpo, miss)) for r in keep.itertuples()]
    for a in [f"press_{i}" for i in range(1, 5)]:
        h = hidden[(hidden.mill_id == mill) & (hidden.asset_id == a)].sort_values("t")
        times = pd.DatetimeIndex(h.t); C = np.cumsum(h.inc.values)
        stops = np.where((times.dayofweek == 6) & (times.hour == 6))[0]
        for c in WEAR_OUT:
            lv = lives[(lives.mill_id == mill) & (lives.asset_id == a) & (lives.comp == c)].sort_values("k")
            life_seq, age0 = lv.life.values, float(lv.age0.iloc[0])
            base, k = -age0, 0
            while True:
                life = life_seq[k % len(life_seq)]
                f_idx = int(np.searchsorted(C, base + life))
                r_idx = int(np.searchsorted(C, base + frac * MEAN_LIFE[c]))
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
    for pol in ("run_to_failure", "fixed_interval", "millguard"):
        daily = np.zeros(days)
        for x in events:
            if x["policy"] == pol:
                d = int((x["t"] - T0).days)
                if 0 <= d < days:
                    daily[d] += x["cost"]
        cols[pol] = np.cumsum(daily).astype(int)
    return [dict(t=idx[i], cost={k: int(v[i]) for k, v in cols.items()}) for i in range(days)]


def run_all_policies(p, mill, pred, failures, lives, hidden, k, frac, budget=5, cpo=None, miss=1.0, trigger="p72"):
    thr = {t: decide.risk_threshold(p, t, k[t], cpo, miss) for t in ("press", "boiler")}
    episodes = decide.run_mill(p, pred, failures, thr, budget, cpo, miss, mill, trigger)
    events = rtf_events(p, failures, cpo, miss) + fixed_events(p, mill, failures, lives, hidden, frac, cpo, miss) \
        + millguard_events(p, episodes, failures, cpo, miss)
    return episodes, events, thr
