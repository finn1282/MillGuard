"""Tune on training mills only: fixed-interval fraction and the false-alarm multiplier k (threshold)."""
import json

import numpy as np
import pandas as pd

from backend.engine import backtest, cost, decide
from backend.models.train import CUT, EVAL_START
from backend.params import load
from backend.sim.simulate import DATA

GRID = [0.02, 0.03, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.5]
FRACS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2]


def window(df, col="t"):
    return df[(df[col] >= EVAL_START) & (df[col] < CUT)]


def fit(p=None, verbose=True, triggers=("p72", "pstop", "p168")):
    p = p or load()
    pred = pd.read_parquet(DATA / "predictions.parquet")
    fails = pd.read_parquet(DATA / "failures.parquet")
    lives = pd.read_parquet(DATA / "lives.parquet")
    hidden = pd.read_parquet(DATA / "hidden.parquet")
    mills = range(1, 10)
    # fixed interval sweep (cost within the training window)
    fi = {}
    for f in FRACS:
        tot = 0
        for m in mills:
            fm = fails[fails.mill_id == m]
            e = backtest.fixed_events(p, m, fm, lives, hidden, f, None, 1.0)
            tot += sum(x["cost"] for x in e if EVAL_START <= x["t"] < CUT)
        fi[f] = tot
    frac = min(fi, key=fi.get)
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
    out = dict(fixed_interval_frac=frac, fixed_sweep={str(a): int(b) for a, b in fi.items()},
               best_threshold={a: b[0] for a, b in best.items()}, trigger={a: b[2] for a, b in best.items()}, k=k,
               threshold_sweep={a: {str(t): int(c) for t, c in b[1].items()} for a, b in best.items()})
    (DATA.parent.parent / "artifacts" / "policy_fit.json").write_text(json.dumps(out, indent=1))
    if verbose:
        print("fixed-interval sweep (RM, training mills):", out["fixed_sweep"], "-> frac", frac)
        for a, (t, r, tr) in best.items():
            print(f"{a}: best trigger {tr}, threshold {t}, k = {k[a]:.1f}")
    return out


if __name__ == "__main__":
    fit()
