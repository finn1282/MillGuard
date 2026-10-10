"""Training mills (1-9) only: per fault class, how many fingerprint checks match on true-positive alerts?
Used to check the fingerprint RULES (signal, direction, window, tolerance). Never reads mill 10."""
import json
from collections import defaultdict

import pandas as pd

from backend.engine import decide, fingerprint
from backend.engine.service import ART
from backend.models.train import CUT, EVAL_START
from backend.params import load
from backend.sim.simulate import DATA


def main(verbose=True):
    p, fit = load(), json.loads((ART / "policy_fit.json").read_text())
    pred = pd.read_parquet(DATA / "predictions.parquet")
    fails = pd.read_parquet(DATA / "failures.parquet")
    tel = pd.read_parquet(DATA / "telemetry.parquet")
    thr = {a: decide.risk_threshold(p, a, fit["k"][a]) for a in fit["k"]}
    best = defaultdict(list)      # class -> best matches anywhere in the alert window (sampled every 3 h)
    res = defaultdict(list)       # class -> (matches, n_checks) at alert open
    per_sig = defaultdict(list)   # (class, signal, expected) -> matches
    for m in range(1, 10):
        pm, fm = pred[(pred.mill_id == m) & (pred.t < CUT)], fails[(fails.mill_id == m) & (fails.t < CUT)]
        ep = decide.run_mill(p, pm, fm, thr, 5, None, 1.0, m, fit["trigger"])
        ep = ep[(ep.t_open >= EVAL_START) & (ep.outcome == "prevented")] if len(ep) else ep
        tm = tel[tel.mill_id == m]
        for r in ep.itertuples():
            fp = fingerprint.fingerprint(tm, r.asset_id, r.fault_class, r.t_open)
            res[r.fault_class].append((sum(c.matches for c in fp), len(fp)))
            end = min(r.t_close if r.t_close is not None and not pd.isna(r.t_close) else r.t_open, r.t_repair)
            hrs = pd.date_range(r.t_open, max(end, r.t_open), freq="3h")
            best[r.fault_class].append(max(sum(c.matches for c in fingerprint.fingerprint(tm, r.asset_id, r.fault_class, t)) for t in hrs))
            for c in fp:
                per_sig[(r.fault_class, c.signal, c.expected)].append(c.matches)
    out = {}
    for fc, v in sorted(res.items()):
        out[fc] = dict(alerts=len(v), avg_matches=round(sum(a for a, _ in v) / len(v), 2), checks=v[0][1])
        if verbose:
            print(f"{fc:15s} alerts {len(v):3d}  avg {out[fc]['avg_matches']:.2f} of {v[0][1]}  "
                  f"(best hour in window: {sum(best[fc]) / len(best[fc]):.2f})")
            for (c, s, e), x in per_sig.items():
                if c == fc:
                    print(f"      {s:18s} {e:9s} matches {sum(x) / len(x):.0%}")
    return out


if __name__ == "__main__":
    main()
