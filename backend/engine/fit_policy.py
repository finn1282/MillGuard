"""Tune on training mills only: the false-alarm multiplier k (threshold)."""
import json

import numpy as np
import pandas as pd

from backend.engine import backtest, cost, decide
from backend.models.train import CUT, EVAL_START
from backend.params import load
from backend.sim.simulate import DATA

GRID = [0.02, 0.03, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.5, 0.65, 0.8]


def window(df, col="t"):
    return df[(df[col] >= EVAL_START) & (df[col] < CUT)]


def fit(p=None, verbose=True, triggers=("p72", "pstop", "p168")):
    p = p or load()
    pred = pd.read_parquet(DATA / "predictions.parquet")
    fails = pd.read_parquet(DATA / "failures.parquet")
    lives = pd.read_parquet(DATA / "lives.parquet")
    hidden = pd.read_parquet(DATA / "hidden.parquet")
    mills = range(1, 10)
    fixed = sum(x["cost"] for m in mills for x in backtest.fixed_events(p, m, fails[fails.mill_id == m], lives, hidden, None, 1.0)
                if EVAL_START <= x["t"] < CUT)   # published RCM intervals, no tuning
    best, all_res = {}, {}
    for atype in ("press", "boiler"):
        for trig in triggers:
            res = {}
            for thr in GRID:
                tot = 0
                for m in mills:
                    pm = pred[(pred.mill_id == m) & (pred.t < CUT) & (pred.is_boiler == (atype == "boiler"))]
                    fm = fails[(fails.mill_id == m) & (fails.t < CUT) & (fails.asset_id.str.startswith(atype))]
                    ep = decide.run_mill(p, pm, fm, {"press": thr, "boiler": thr}, 5, None, 1.0, m, trig)
                    fw = window(fm)
                    ep = ep[ep.t_open >= EVAL_START] if len(ep) else ep
                    if len(ep):
                        ev = backtest.millguard_events(p, ep, fw, None, 1.0)
                    else:
                        ev = backtest.rtf_events(p, fw, None, 1.0)
                        for x in ev: x["policy"] = "millguard"
                    tot += sum(x["cost"] for x in ev if EVAL_START <= x["t"] < CUT)
                res[thr] = tot
            all_res[(atype, trig)] = res
            if verbose:
                print(atype, trig, {str(a): int(b) for a, b in res.items()})
        trig, res = min(((tr, all_res[(atype, tr)]) for tr in triggers), key=lambda x: min(x[1].values()))
        best[atype] = (min(res, key=res.get), res, trig)
    c_fp = cost.false_alarm_cost(p)
    k = {}
    for atype, (thr, _, _) in best.items():
        fc = "boiler_steam" if atype == "boiler" else "worm_wear"
        k[atype] = thr / (1 - thr) * cost.saved_if_acted(p, fc) / c_fp
    thr_fit = {a: decide.risk_threshold(p, a, k[a]) for a in k}
    trig_fit = {a: b[2] for a, b in best.items()}
    eps, catch_n, catch_d = {}, {"press": 0, "boiler": 0}, {"press": 0, "boiler": 0}
    for m in mills:
        pm, fm = pred[(pred.mill_id == m) & (pred.t < CUT)], fails[(fails.mill_id == m) & (fails.t < CUT)]
        ep = decide.run_mill(p, pm, fm, thr_fit, 5, None, 1.0, m, trig_fit)
        eps[m] = ep[ep.t_open >= EVAL_START] if len(ep) else ep
        for r in window(fm).itertuples():
            at = cost.asset_type(r.fault_class)
            catch_d[at] += 1
            catch_n[at] += int(len(eps[m]) and ((eps[m].asset_id == r.asset_id) & (eps[m].outcome == "prevented")
                                                & (eps[m].fail_idx == int((r.t - pd.Timestamp("2025-01-01")) / pd.Timedelta(hours=1)))).any())
    catch = {a: catch_n[a] / max(catch_d[a], 1) for a in catch_n}
    plus = sum(x["cost"] for m in mills for x in backtest.schedule_plus_events(p, m, fails[fails.mill_id == m], lives, hidden, eps[m], catch, None, 1.0)
               if EVAL_START <= x["t"] < CUT)
    oof = {a: int(b[1][b[0]]) for a, b in best.items()}
    oof["millguard_total"] = sum(oof.values())
    oof["fixed_interval"] = int(fixed); oof["schedule_plus_millguard"] = int(plus)
    out = dict(train_oof_cost_rm=oof, schedule_plus=dict(catch=catch),
               best_threshold={a: b[0] for a, b in best.items()}, trigger={a: b[2] for a, b in best.items()}, k=k,
               threshold_sweep={a: {str(t): int(c) for t, c in b[1].items()} for a, b in best.items()})
    (DATA.parent.parent / "artifacts" / "policy_fit.json").write_text(json.dumps(out, indent=1))
    if verbose:
        print(f"TRAINING-mill out-of-fold policy cost (mills 1-9, Feb-Aug, RM): MillGuard {oof['millguard_total']:,} "
              f"(press {oof['press']:,}, boiler {oof['boiler']:,}); schedule+MillGuard {oof['schedule_plus_millguard']:,}; "
              f"fixed interval {oof['fixed_interval']:,}")
        print("catch rate (training mills)", {a: round(v, 2) for a, v in catch.items()})
        for a, (t, r, tr) in best.items():
            print(f"{a}: best trigger {tr}, threshold {t}, k = {k[a]:.1f}")
    return out


if __name__ == "__main__":
    fit()
