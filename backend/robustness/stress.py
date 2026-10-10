"""Stress test on the unseen mill 10: perturb its inputs, keep the trained models and the fitted thresholds, re-score.
No retraining, no threshold changes. Truth (failures, hidden lives) is never perturbed."""
import json

import joblib
import numpy as np
import pandas as pd

from backend.engine import backtest
from backend.features.build import BOILER_SIGS, PRESS_SIGS, build
from backend.params import load
from backend.sim.simulate import DATA

ART = DATA.parent.parent / "artifacts"
MILL = 10
SCENARIOS = [("baseline", "No perturbation (reference)", None, None),
             ("noise2", "Sensor noise x2", "noise", 2.0), ("noise3", "Sensor noise x3", "noise", 3.0),
             ("miss20", "20% of readings missing", "missing", 0.20), ("miss40", "40% of readings missing", "missing", 0.40),
             ("drift", "Slow sensor drift (+10% over the year on current and vibration)", "drift", 0.10),
             ("wo25", "25% of work orders with the wrong fault class", "wo", 0.25)]
MS = {"baseline": "Tiada gangguan (rujukan)", "noise2": "Hingar penderia 2 kali ganda", "noise3": "Hingar penderia 3 kali ganda",
      "miss20": "20% bacaan hilang", "miss40": "40% bacaan hilang",
      "drift": "Hanyut penderia perlahan (+10% setahun pada arus dan getaran)",
      "wo25": "25% arahan kerja dengan kelas kerosakan salah"}
DRIFT_SIGS = ["motor_current", "current_per_tonne", "vib_rms", "vib_kurtosis"]


def perturb(tel, wo, kind, level, rng):
    tel, wo = tel.copy(), wo.copy()
    sigs = [c for c in PRESS_SIGS + BOILER_SIGS if c in tel.columns and c != "throughput_tph"]
    if kind == "noise":
        for a, g in tel.groupby("asset_id"):
            for s in sigs:
                x = g[s]
                if x.notna().sum() < 100:
                    continue
                d = x.diff().dropna()
                sigma = float(1.4826 * (d - d.median()).abs().median() / np.sqrt(2))   # robust hourly noise (ignores load steps)
                tel.loc[g.index, s] = x + rng.normal(0, np.sqrt(level ** 2 - 1) * sigma, len(x))
    elif kind == "missing":
        for s in sigs:
            tel[s] = tel[s].mask(rng.random(len(tel)) < level)
    elif kind == "drift":
        ramp = ((tel.t - tel.t.min()) / (tel.t.max() - tel.t.min())).values
        for s in DRIFT_SIGS:
            tel[s] = tel[s] * (1 + level * ramp)
    elif kind == "wo":
        press = [c for c in wo.fault_class.unique() if not c.startswith("boiler")]
        pick = (rng.random(len(wo)) < level) & ~wo.fault_class.str.startswith("boiler").values
        wo.loc[pick, "fault_class"] = [rng.choice([c for c in press if c != old]) for old in wo.loc[pick, "fault_class"]]
    return tel, wo


def predict(feat, bundle):
    out = []
    for kind, boiler in (("press", False), ("boiler", True)):
        b, df = bundle[kind], feat[feat.is_boiler == boiler].reset_index(drop=True)
        X = df.reindex(columns=b["cols"])
        o = df[["mill_id", "asset_id", "t", "is_boiler"]].copy()
        for h in (24, 72, 168):
            o[f"p{h}"] = b["calib"][h].predict(b["models"][h].predict_proba(X)[:, 1])
        for c, v in zip(b["clf"].classes_, b["clf"].predict_proba(X).T):
            o[f"cp_{c}"] = v
        out.append(o)
    return pd.concat(out, ignore_index=True)


def run(p, fit, tel, err, wo, bundle, fails, lives, hidden):
    pred = predict(build(save=False, tel=tel, err=err, wo=wo), bundle)
    ep, events, thr = backtest.run_all_policies(p, MILL, pred, fails, lives, hidden, fit["k"],
                                                trigger=fit["trigger"], plus=fit["schedule_plus"])
    tm = backtest.test_mill_table(ep, fails)
    caught = sum(r["caught"] for r in tm["by_fault_class"])
    total = sum(r["total"] for r in tm["by_fault_class"])
    leads = [(r.t - e.t_open) / pd.Timedelta(hours=1) for e in ep[ep.outcome == "prevented"].itertuples()
             for r in fails[(fails.asset_id == e.asset_id)].itertuples() if int((r.t - pd.Timestamp("2025-01-01")) / pd.Timedelta(hours=1)) == e.fail_idx]
    cost = {k: backtest.summarize(p, events, k)["total_cost_rm"] for k in backtest.POLICIES}
    tp = int((ep.outcome == "prevented").sum())
    return dict(caught=caught, total=total, fa_week=tm["false_alarms_per_week"], alerts=len(ep), tp_alerts=tp,
                median_lead_h=float(np.median(leads)) if leads else 0.0, cost=cost)


def main():
    p, fit = load(), json.loads((ART / "policy_fit.json").read_text())
    bundle = joblib.load(ART / "models.joblib")
    tel = pd.read_parquet(DATA / "telemetry.parquet"); tel = tel[tel.mill_id == MILL].reset_index(drop=True)
    err = pd.read_parquet(DATA / "errors.parquet"); err = err[err.mill_id == MILL]
    wo = pd.read_parquet(DATA / "maintenance.parquet"); wo = wo[wo.mill_id == MILL].reset_index(drop=True)
    rd = lambda n: (lambda d: d[d.mill_id == MILL].reset_index(drop=True))(pd.read_parquet(DATA / f"{n}.parquet"))
    fails, lives, hidden = rd("failures"), pd.read_parquet(DATA / "lives.parquet"), pd.read_parquet(DATA / "hidden.parquet")
    rows = []
    print(f"{'scenario':64s} {'catch':>9s} {'FA/wk':>6s} {'lead h':>7s} {'Sched+MG RM':>12s} {'fixed RM':>10s} {'MG alone':>10s}")
    for key, label, kind, level in SCENARIOS:
        t2, w2 = (tel, wo) if kind is None else perturb(tel, wo, kind, level, np.random.default_rng(42))
        r = run(p, fit, t2, err, w2, bundle, fails, lives, hidden)
        r.update(key=key, label=label)
        rows.append(r)
        print(f"{label:64s} {r['caught']:>4d}/{r['total']:<4d} {r['fa_week']:6.2f} {r['median_lead_h']:7.1f} "
              f"{r['cost']['schedule_plus_millguard']:12,d} {r['cost']['fixed_interval']:10,d} {r['cost']['millguard']:10,d}")
    for f in ART.glob("robustness_extra_stress_*.json"):
        f.unlink()
    for r in rows:
        if r["key"] == "baseline":
            continue
        better = r["cost"]["schedule_plus_millguard"] < r["cost"]["fixed_interval"]
        (ART / f"robustness_extra_stress_{r['key']}.json").write_text(json.dumps(dict(
            dataset="Mill 10 stress test", task_en=f"{r['label']}: same models, same thresholds, no retraining",
            task_ms=f"{MS[r['key']]}: model dan ambang yang sama, tanpa latihan semula",
            lead_min=int(round(r["median_lead_h"] * 60)), events_total=r["total"], events_caught=r["caught"],
            precision_pct=round(100 * r["tp_alerts"] / max(r["alerts"], 1), 1),
            false_alarms_per_day=round(r["fa_week"] / 7, 2),
            split="Unseen mill 10, full year 2025; only the inputs are perturbed, the failures are the real ones",
            note=(f"Catch {r['caught']} of {r['total']}, {r['fa_week']} false alarms per week, median lead {r['median_lead_h']:.0f} hours. "
                  f"Schedule + MillGuard RM{r['cost']['schedule_plus_millguard']:,} vs fixed interval RM{r['cost']['fixed_interval']:,} "
                  f"({'better' if better else 'worse'}); MillGuard alone RM{r['cost']['millguard']:,}. "
                  "Alert counts and cost use the same backtest as the app; lead_min is the median warning in minutes.")), indent=1))
    (ART / "stress_table.json").write_text(json.dumps(rows, indent=1, default=float))
    return rows


if __name__ == "__main__":
    main()
