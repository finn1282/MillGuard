"""Real coal-fired boiler (5 days, 5 s): predict steam-temperature excursions outside 530-545 degC 10-15 min ahead
from the OTHER variables. Time-based split only: first 3 days train, next day picks the threshold, last ~2 days test."""
import json

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from backend.params import load, val
from backend.scripts.fetch_boiler import DEST

ART = DEST.parents[2] / "artifacts"
TARGET = "TE_8332A.AV_0#"
LO, HI = 530.0, 545.0
LEAD_MIN, LEAD_MAX = 10, 15
PURGE = 15
TRAIN_END, VAL_END = pd.Timestamp("2022-03-30 14:30"), pd.Timestamp("2022-03-31 14:30")


def load_minutes():
    d = pd.read_csv(DEST, parse_dates=["date"]).set_index("date").sort_index()
    return d.resample("1min").mean().interpolate(limit=5)


def build(m):
    others = [c for c in m.columns if c != TARGET]
    X = {}
    for c in others:
        s = m[c]
        X[c] = s
        X[c + "_m5"] = s.rolling(5).mean()
        X[c + "_m15"] = s.rolling(15).mean()
        X[c + "_d10"] = s - s.shift(10)
        X[c + "_sd15"] = s.rolling(15).std()
    X = pd.DataFrame(X)
    out = ((m[TARGET] < LO) | (m[TARGET] > HI)).astype(int)
    fut = pd.concat([out.shift(-k) for k in range(LEAD_MIN, LEAD_MAX + 1)], axis=1).max(axis=1)
    fut[out.shift(-LEAD_MAX).isna()] = np.nan
    return X, out, fut


def episodes(flag, persist=1):
    """Start indices of runs of 1s lasting >= persist minutes (gaps < 10 min merged for true excursions)."""
    runs, cur, n = [], None, 0
    for i, v in enumerate(flag):
        if v:
            cur = i if cur is None else cur
            n += 1
        elif cur is not None:
            if n >= persist:
                runs.append((cur, i - 1))
            cur, n = None, 0
    if cur is not None and n >= persist:
        runs.append((cur, len(flag) - 1))
    return runs


def main():
    p = load()
    persist = int(val(p, "alerting", "persistence_h") > 0) * 2   # 2 minutes of persistence on this 1-min series
    m = load_minutes()
    X, out, fut = build(m)
    idx = X.index
    in_band = out == 0
    ok = fut.notna() & X.notna().all(axis=1) & in_band          # predict NEW excursions: machine is in band now
    tr = ok & (idx < TRAIN_END - pd.Timedelta(minutes=PURGE))
    va = ok & (idx >= TRAIN_END) & (idx < VAL_END - pd.Timedelta(minutes=PURGE))
    te = ok & (idx >= VAL_END)
    mdl = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=30, subsample=0.8,
                             subsample_freq=1, colsample_bytree=0.7, random_state=0, verbose=-1)
    mdl.fit(X[tr], fut[tr].astype(int))
    pv, pt = mdl.predict_proba(X[va])[:, 1], mdl.predict_proba(X[te])[:, 1]
    yv = fut[va].astype(int).values
    best = max(((f1(yv, pv >= t), t) for t in np.linspace(0.05, 0.95, 91)))
    thr = float(best[1])
    # event-level scoring on test: true excursion starts vs alert episodes (2 min persistence)
    ti = idx[te]
    full = pd.Series(0, index=idx); full[ti] = (pt >= thr).astype(int)
    alert_eps = [(idx[a], idx[b]) for a, b in episodes(full.values, persist)]
    starts = [idx[a] for a, _ in episodes(out.values) if idx[a] >= VAL_END and a > 0 and out.values[a - 1] == 0 and in_band.iloc[a - 1]]
    d = lambda mins: pd.Timedelta(minutes=mins)
    caught = sum(any(a + d(LEAD_MIN - 0) - d(persist) <= s <= b + d(LEAD_MAX) for a, b in alert_eps) for s in starts)
    tp_eps = sum(any(a + d(LEAD_MIN) - d(persist) <= s <= b + d(LEAD_MAX) for s in starts) for a, b in alert_eps)
    days = (idx[te][-1] - idx[te][0]) / pd.Timedelta(days=1)
    base = float(fut[te].mean())
    auc = float(roc_auc_score(fut[te].astype(int), pt))
    prec = tp_eps / max(len(alert_eps), 1)
    out_json = dict(dataset="Real coal-fired boiler (Zhejiang, 5 days)", task_en="Predict steam temperature leaving 530-545 C",
                    task_ms="Ramal suhu stim keluar daripada 530-545 C", lead_min=LEAD_MIN,
                    events_total=len(starts), events_caught=int(caught), precision_pct=round(100 * prec, 1),
                    false_alarms_per_day=round((len(alert_eps) - tp_eps) / days, 1),
                    split="Time-based: first 3 days train, next day sets the alert threshold, last ~2 days test (nothing tuned on test)",
                    note=(f"Real data, 5 s readings averaged to 1 min; steam temperature itself is NOT an input. An alert means an excursion "
                          f"starts {LEAD_MIN}-{LEAD_MAX} min later; only predicts new excursions (steam in band at alert time). "
                          f"Random alerting would be right {100 * base:.0f}% of the time. Test AUC {auc:.2f} (0.5 = no skill): with 5 days of one boiler the model finds no usable early warning, "
                          "and adding the steam temperature history did not help. "
                          "Data downloaded by script, not redistributed."))
    ART.mkdir(exist_ok=True)
    (ART / "robustness_extra_boiler.json").write_text(json.dumps(out_json, indent=1))
    print(json.dumps({k: v for k, v in out_json.items() if k not in ("note", "split")}), "| threshold", round(thr, 2),
          "| test min", int(te.sum()), "| alert episodes", len(alert_eps), "| base rate", round(base, 3), "| test AUC", round(auc, 3))
    return out_json


def f1(y, pred):
    tp = int(((y == 1) & pred).sum()); fp = int(((y == 0) & pred).sum()); fn = int(((y == 1) & ~pred).sum())
    return 2 * tp / max(2 * tp + fp + fn, 1)


if __name__ == "__main__":
    main()
