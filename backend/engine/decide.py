"""Decision layer: persistence, hysteresis, per-shift budget, fix-now vs schedule, outcome matching.

Inputs are hourly calibrated risks. Outcomes are matched to true failures only for accounting (backtest);
no decision ever looks at the future.
"""
import numpy as np
import pandas as pd

from backend.engine import cost
from backend.params import val

T0 = pd.Timestamp("2025-01-01")
POST_FAIL_H = 6


def shift_id(t: pd.Timestamp) -> int:
    """Day shift 07-19, night 19-07; night after midnight belongs to the previous night."""
    d = (t - pd.Timedelta(hours=7)).floor("12h") if False else None
    shifted = t - pd.Timedelta(hours=7)
    return int((shifted - T0).total_seconds() // (12 * 3600))


def hours_to_stop(t: pd.Timestamp, min_lead: float) -> int:
    """Hours until the next weekly planned stop (Sunday 06:00), at least min_lead away."""
    h = ((6 - t.dayofweek) % 7) * 24 + (6 - t.hour)
    while h < min_lead:
        h += 168
    return int(h)


def p_before(p24, p72, p168, hrs) -> float:
    cum = np.maximum.accumulate([0.0, p24, p72, p168])
    return float(np.interp(min(hrs, 168), [0, 24, 72, 168], cum))


def risk_threshold(p, atype, k, cpo=None, miss=1.0) -> float:
    """Cost-optimal threshold C_FP/(C_FP+C_FN) with an effective false-alarm multiplier k fitted on training mills."""
    fc = "boiler_steam" if atype == "boiler" else "worm_wear"
    c_fp = k * cost.false_alarm_cost(p)
    c_fn = cost.saved_if_acted(p, fc, cpo, miss)
    return c_fp / (c_fp + c_fn)


def run_mill(p, pred, failures, thr, budget=5, cpo=None, miss=1.0, mill_id=None, trigger="p72"):
    """pred: hourly predictions of one mill (all assets). failures: true failures of the mill.
    thr: {"press": x, "boiler": y}. Returns episodes DataFrame."""
    persist = val(p, "alerting", "persistence_h")
    hyst = val(p, "alerting", "hysteresis_ratio")
    clear_h = val(p, "alerting", "clear_hours")
    min_lead = val(p, "alerting", "min_lead_h")
    resp = val(p, "alerting", "fix_now_response_h")
    pred = pred.sort_values("t")
    times = pd.DatetimeIndex(sorted(pred.t.unique()))
    H = len(times)
    assets = sorted(pred.asset_id.unique())
    A = {}
    for a in assets:
        g = pred[pred.asset_id == a].set_index("t").reindex(times)
        cp_cols = [c for c in g.columns if c.startswith("cp_")]
        fh = failures[failures.asset_id == a].copy()
        fh["idx"] = ((fh.t - times[0]) / pd.Timedelta(hours=1)).astype(int)
        A[a] = dict(p24=g.p24.fillna(0).values, p72=g.p72.fillna(0).values, p168=g.p168.fillna(0).values,
                    cp=g[cp_cols].fillna(0).values, cls=[c[3:] for c in cp_cols],
                    atype="boiler" if a.startswith("boiler") else "press",
                    fidx=fh.idx.values, fcls=fh.fault_class.values, ft=fh.t.values,
                    st=dict(above=0, below=0, active=None, mute=-1, pending=None))
    hts_all = np.array([hours_to_stop(t, min_lead) for t in times])
    for d in A.values():
        cum = np.maximum.accumulate(np.vstack([np.zeros(H), d["p24"], d["p72"], d["p168"]]), axis=0)
        h = np.minimum(hts_all, 168)
        lo = np.searchsorted([0, 24, 72, 168], h, side="right") - 1
        lo = np.minimum(lo, 2)
        x0, x1 = np.array([0, 24, 72, 168])[lo], np.array([0, 24, 72, 168])[lo + 1]
        ar = np.arange(H)
        d["pstop"] = cum[lo, ar] + (cum[lo + 1, ar] - cum[lo, ar]) * (h - x0) / (x1 - x0)
        tr = trigger[d["atype"]] if isinstance(trigger, dict) else trigger
        d["trig"] = {"p72": d["p72"], "p168": d["p168"], "pstop": d["pstop"]}[tr]
    shift_count, episodes = {}, []
    for h in range(H):
        t = times[h]
        cands = []
        for a, d in A.items():
            s, pv, th = d["st"], d["trig"][h], thr[d["atype"]]
            if h < s["mute"]:
                s["above"] = 0
                continue
            ep = s["active"]
            if ep is not None:
                s["below"] = 0 if pv >= hyst * th else s["below"] + 1
                if s["below"] >= clear_h or (ep["fail_idx"] is not None and h >= ep["fail_idx"] + POST_FAIL_H):
                    ep["t_close"] = t; s["active"] = None; s["below"] = 0
                continue
            s["above"] = s["above"] + 1 if pv > th else 0
            if s["above"] >= persist:
                cands.append(a)
                if s["pending"] is None:
                    s["pending"] = h
            else:
                s["pending"] = None
        if not cands:
            continue
        scored = []
        for a in cands:
            d = A[a]
            fc = d["cls"][int(np.argmax(d["cp"][h]))]
            scored.append((cost.saved_if_acted(p, fc, cpo, miss), a, fc))
        for _, a, fc in sorted(scored, reverse=True):
            sid = shift_id(t)
            if shift_count.get(sid, 0) >= budget:
                continue
            shift_count[sid] = shift_count.get(sid, 0) + 1
            d = A[a]; s = d["st"]
            atype = d["atype"]
            hts = hours_to_stop(t, min_lead)
            p24, p72, p168 = d["p24"][h], d["p72"][h], d["p168"][h]
            p_stop = p_before(p24, p72, p168, hts)
            at_risk = cost.breakdown_cost(p, fc, cpo, miss)
            planned = cost.planned_cost(p, fc)
            stop_c = cost.fix_now_stop_cost(p, atype, cpo)
            c_now, c_wait = stop_c + planned, p_stop * at_risk + (1 - p_stop) * planned
            rec = "fix_now" if c_now < c_wait else "schedule_next_stop"
            to_act = planned + (stop_c if rec == "fix_now" else 0)
            rep_idx = h + (resp if rec == "fix_now" else hts)
            # accounting only: next true failure of this asset after the alert
            nxt = np.where(d["fidx"] > h)[0]
            f_i = nxt[0] if len(nxt) and d["fidx"][nxt[0]] - h <= 168 else None
            if f_i is None:
                outcome, fail_idx, fail_cls = "false_alarm", None, None
            else:
                fail_idx, fail_cls = int(d["fidx"][f_i]), d["fcls"][f_i]
                found = fail_cls == fc or np.random.default_rng([mill_id or 0, h, len(a)]).random() < val(p, "alerting", "inspection_finds_wrong_class")
                outcome = ("misclassified" if not found else "late" if fail_idx <= rep_idx else "prevented")
            ep = dict(mill_id=mill_id, asset_id=a, t_candidate=times[s["pending"]], t_open=t, t_close=None,
                      fault_class=fc, risk24=p24, risk72=p72, risk168=p168, p_stop=p_stop, recommendation=rec,
                      t_repair=times[min(rep_idx, H - 1)], rm_at_risk=at_risk, rm_cost_to_act=to_act,
                      rm_saved=at_risk - to_act, outcome=outcome, fail_idx=fail_idx, fail_class_true=fail_cls,
                      row=h)
            episodes.append(ep)
            s["pending"] = None; s["below"] = 0
            if outcome == "prevented":
                ep["t_close"] = times[min(rep_idx, H - 1)]
                s["mute"] = fail_idx + POST_FAIL_H
                s["above"] = 0
            else:
                s["active"] = ep
    for d in A.values():
        ep = d["st"]["active"]
        if ep is not None and ep["t_close"] is None:
            ep["t_close"] = times[-1]
    return pd.DataFrame(episodes)
