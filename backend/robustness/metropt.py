"""Robustness check: same alert logic (persistence, hysteresis) on real, unlabeled compressor data (MetroPT-3).
Unsupervised: Isolation Forest fit on healthy Feb 2020, alert threshold set on healthy March 2020,
failures (4 air leaks, UCI report) used only for scoring April-August."""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.features.build import sig_features
from backend.params import load, val
from backend.sim.simulate import DATA

SRC = DATA.parent / "metropt" / "metropt3.parquet"
ART = DATA.parent.parent / "artifacts"
FAILS = [("2020-04-18 00:00", "2020-04-18 23:59"), ("2020-05-29 23:30", "2020-05-30 06:00"),
         ("2020-06-05 10:00", "2020-06-07 14:30"), ("2020-07-15 14:30", "2020-07-15 19:00")]
TRAIN_END, VAL_END = pd.Timestamp("2020-03-01"), pd.Timestamp("2020-04-01")
LEAD_WINDOW_H = 72


def hourly(df):
    ts = [c for c in df.columns if "time" in c.lower()][0]
    df[ts] = pd.to_datetime(df[ts]); df = df.set_index(ts).sort_index()
    num = df.select_dtypes("number")
    analog = [c for c in num.columns if num[c].nunique() > 5]
    h = num[analog].resample("1h").mean()
    for c in ["Motor_current", "TP2", "Oil_temperature"]:
        if c in num:
            h[f"{c}_sd"] = num[c].resample("1h").std()
    digital = [c for c in num.columns if c not in analog]
    for c in digital:
        h[f"{c}_duty"] = num[c].resample("1h").mean()
    return h


def episodes(score, thr, persist, clear_lvl, clear_h):
    out, above, below, cur = [], 0, 0, None
    for i, v in enumerate(score):
        if cur is None:
            above = above + 1 if v > thr else 0
            if above >= persist:
                cur = i; below = 0
        else:
            below = 0 if v >= clear_lvl else below + 1
            if below >= clear_h:
                out.append((cur, i)); cur = None; above = 0
    if cur is not None:
        out.append((cur, len(score) - 1))
    return out


def main():
    p = load()
    persist, hyst, clear_h = (val(p, "alerting", k) for k in ("persistence_h", "hysteresis_ratio", "clear_hours"))
    h = hourly(pd.read_parquet(SRC))
    feats = pd.concat([pd.DataFrame(sig_features(h[c], c)) for c in h.columns], axis=1)
    cols = [c for c in feats.columns if "_rel" in c or "_sd24" in c or "_slope" in c]
    X = feats[cols]
    med = X[X.index < TRAIN_END].median()
    train = X[(X.index < TRAIN_END)].dropna(thresh=len(cols) // 2).fillna(med)
    iso = IsolationForest(n_estimators=200, random_state=0).fit(train)
    raw = -iso.score_samples(X.fillna(med))
    score = pd.Series(raw, index=X.index)
    val_s = score[(score.index >= TRAIN_END) & (score.index < VAL_END)]
    val_weeks = len(val_s) / 168
    base, thr = float(val_s.median()), None
    for q in (0.97, 0.98, 0.99, 0.995, 0.999, 0.9995, 1.0):   # healthy March only: <=0.5 episodes/week, <=2% of hours alerting
        t = float(val_s.quantile(q))
        eps_v = episodes(val_s.values, t, persist, base + hyst * (t - base), clear_h)
        hours = sum(e - s_ for s_, e in eps_v)
        if len(eps_v) / val_weeks <= 0.5 and hours / len(val_s) <= 0.02:
            thr = t; break
    thr = thr if thr is not None else float(val_s.max())
    test = score[score.index >= VAL_END]
    eps = [(test.index[a], test.index[b]) for a, b in episodes(test.values, thr, persist, base + hyst * (thr - base), clear_h)]
    f_start = [pd.Timestamp(a) for a, _ in FAILS]; f_end = [pd.Timestamp(b) for _, b in FAILS]
    leads, caught = [], 0
    for s in f_start:
        opens = [o for o, _ in eps if s - pd.Timedelta(hours=LEAD_WINDOW_H) <= o <= s]
        if opens:
            caught += 1; leads.append((s - min(opens)) / pd.Timedelta(hours=1))
    def is_fa(o):
        return not any(s - pd.Timedelta(hours=LEAD_WINDOW_H) <= o <= e for s, e in zip(f_start, f_end))
    fa = sum(is_fa(o) for o, _ in eps)
    fail_h = sum((e - s) / pd.Timedelta(hours=1) for s, e in zip(f_start, f_end))
    weeks = (len(test) - fail_h - LEAD_WINDOW_H * len(FAILS)) / 168
    late = sum(any(s < o <= e for o, _ in eps) for s, e in zip(f_start, f_end))
    out = dict(dataset="MetroPT-3", failures_total=len(FAILS), caught=caught,
               median_lead_h=round(float(np.median(leads)), 1) if leads else 0.0,
               false_alarms_per_week=round(fa / weeks, 2),
               note=("Real compressor data, unsupervised. Isolation Forest fit on healthy Feb 2020; threshold set on healthy "
                     "March for <=0.5 episodes/week and <=2% of hours alerting; scored on Apr-Aug (4 air-leak failures). Caught = alert opened "
                     f"0-{LEAD_WINDOW_H} h before the failure start; {late} more failure(s) were flagged only after they had started. "
                     "Same persistence and hysteresis rules as the mill pipeline. Threshold was fixed on healthy data, not tuned on the failures."))
    print("episodes:", [(str(a), str(b)) for a, b in eps]); print("score max by failure window:", [round(float(score[(score.index >= s - pd.Timedelta(hours=72)) & (score.index <= e)].max()), 3) for s, e in zip(f_start, f_end)], "thr", round(float(thr), 3))
    (ART / "robustness.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "note"}), "| episodes:", len(eps), "| threshold:", round(float(thr), 4))
    return out


if __name__ == "__main__":
    main()
