"""One command: simulate -> features -> train -> tune policies on training mills -> evaluate mill 10."""
import json
import sys

import numpy as np
import pandas as pd

from backend.engine import backtest, fit_policy
from backend.models import train
from backend.params import load
from backend.sim import simulate
from backend.sim.simulate import DATA

ART = DATA.parent.parent / "artifacts"
MILL = 10


def load_mill10():
    pred = pd.read_parquet(DATA / "predictions.parquet")
    fails = pd.read_parquet(DATA / "failures.parquet")
    return (pred[pred.mill_id == MILL], fails[fails.mill_id == MILL],
            pd.read_parquet(DATA / "lives.parquet"), pd.read_parquet(DATA / "hidden.parquet"))


def evaluate(p, fit, verbose=True, **kw):
    pred, fails, lives, hidden = load_mill10()
    ep, events, thr = backtest.run_all_policies(p, MILL, pred, fails, lives, hidden, fit["k"],
                                                fit["fixed_interval_frac"], trigger=fit["trigger"], **kw)
    pols = [backtest.summarize(p, events, k) for k in ("run_to_failure", "fixed_interval", "millguard")]
    return ep, events, thr, pols, fails


def headline(ep, pols, fails, thr):
    weeks = 365 / 7
    prev = ep[ep.outcome == "prevented"]
    missed = ep[ep.outcome.isin(["late", "misclassified"])]
    fa = ep[ep.outcome.isin(["false_alarm", "misclassified"])]
    t0 = pd.Timestamp("2025-01-01")
    lead = [(t0 + pd.Timedelta(hours=int(r.fail_idx)) - r.t_open) / pd.Timedelta(hours=1) for r in prev.itertuples()]
    print("\n== Mill 10 (unseen), full year 2025 ==  thresholds:", {k: round(v, 3) for k, v in thr.items()})
    print(f"failures: {len(fails)}   caught (prevented): {len(prev)}   alerted but missed (late/wrong class): {len(missed)}")
    print(f"median lead time: {np.median(lead) if lead else float('nan'):.1f} h   "
          f"false alarms/week: {len(fa) / weeks:.2f}   alerts/week: {len(ep) / weeks:.2f}")
    for r in pols:
        print(f"  {r['id']:15s} RM {r['total_cost_rm']:>10,}  breakdowns {r['breakdowns']:3d}  planned {r['planned_stops']:3d}  "
              f"false alarms {r['false_alarms']:3d}  downtime {r['downtime_h']:.0f} h")


def main(skip_sim=False):
    if not skip_sim:
        out = simulate.simulate_all(); simulate.summary(out)
        train.main()
    p = load()
    fit = fit_policy.fit(p)
    ep, events, thr, pols, fails = evaluate(p, fit)
    headline(ep, pols, fails, thr)
    ART.mkdir(exist_ok=True)
    pred = pd.read_parquet(DATA / "predictions.parquet")
    pred[pred.mill_id == MILL].to_parquet(ART / "mill10_predictions.parquet")
    ep.to_parquet(ART / "episodes.parquet")


if __name__ == "__main__":
    main(skip_sim="--skip-sim" in sys.argv)
