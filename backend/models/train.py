"""Train risk (24/72/168 h), Isolation Forest and fault classifier. Time-based split only.

Train: mills 1-9, t < 2025-09-01 (purged 168 h before the cut). Test: mill 10 (all year) and months 9-12.
Predictions on training rows are out-of-fold by mill, so they can be used to pick thresholds honestly.
"""
import json

import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.ensemble import IsolationForest
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold

from backend.features.build import BOILER_CLASSES, PRESS_CLASSES, build
from backend.sim.simulate import AUG, DATA, H

ART = DATA.parent.parent / "artifacts"
CUT = pd.Timestamp("2025-09-01")
EVAL_START = pd.Timestamp("2025-02-01")   # burn-in: 30-day baselines need history
HORIZONS = (24, 72, 168)
META = ["mill_id", "asset_id", "t", "is_boiler"]
LGB = dict(n_estimators=250, learning_rate=0.05, num_leaves=15, min_child_samples=100, subsample=0.8,
           subsample_freq=1, colsample_bytree=0.8, reg_lambda=5.0, verbose=-1, n_jobs=4)
LGB_BOILER = dict(LGB, num_leaves=5, min_child_samples=60, n_estimators=150)


def add_labels(feat, fail, wo):
    t0 = pd.Timestamp("2025-01-01")
    for h in HORIZONS:
        feat[f"y{h}"] = 0
    feat["next_logged_class"] = None
    logged = wo.set_index("failure_id").fault_class
    for (mill, asset), idx in feat.groupby(["mill_id", "asset_id"]).groups.items():
        f = fail[(fail.mill_id == mill) & (fail.asset_id == asset)].copy()
        f["h"] = ((f.t - t0) / pd.Timedelta(hours=1)).astype(int)
        f = f.sort_values("h")
        hrs = ((feat.loc[idx, "t"] - t0) / pd.Timedelta(hours=1)).astype(int).values
        pos = np.searchsorted(f.h.values, hrs, side="right")
        ok = pos < len(f)
        nxt = np.where(ok, f.h.values[np.minimum(pos, max(len(f) - 1, 0))] - hrs, 10 ** 6) if len(f) else np.full(len(hrs), 10 ** 6)
        for h in HORIZONS:
            feat.loc[idx, f"y{h}"] = (nxt <= h).astype(int)
        cls = np.where(ok & (nxt <= 72), logged.reindex(f.failure_id.values[np.minimum(pos, len(f) - 1)]).values if len(f) else None, None)
        feat.loc[idx, "next_logged_class"] = cls
    return feat


def fit_group(df, boiler):
    """Fit risk models (OOF-calibrated), IF and classifier for presses or the boiler."""
    cols = [c for c in df.columns if c not in META + ["next_logged_class"] + [f"y{h}" for h in HORIZONS]
            and not df[c].isna().all()]
    params = LGB_BOILER if boiler else LGB
    train = df[((df.mill_id <= 9) | (df.mill_id > 100)) & (df.t <= CUT - pd.Timedelta(hours=168))]   # 101-109 = augmented copies
    out = df[META].copy()
    models, calib = {}, {}
    gkf = GroupKFold(n_splits=3)
    for h in HORIZONS:
        y = train[f"y{h}"].values
        oof = np.zeros(len(train))
        for tr, va in gkf.split(train, y, train.mill_id % 100):
            m = lgb.LGBMClassifier(**params).fit(train.iloc[tr][cols], y[tr])
            oof[va] = m.predict_proba(train.iloc[va][cols])[:, 1]
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(oof, y)
        models[h] = lgb.LGBMClassifier(**params).fit(train[cols], y)
        calib[h] = iso
        raw = models[h].predict_proba(df[cols])[:, 1]
        p = iso.predict(raw)
        p[train.index.map(df.index.get_loc)] = iso.predict(oof)   # OOF for training rows
        out[f"p{h}"] = p
    rel = [c for c in cols if "_rel" in c or "_sd24" in c or "_slope" in c]
    healthy = train[train.y168 == 0][rel].dropna(thresh=len(rel) // 2)
    med = healthy.median()
    iforest = IsolationForest(n_estimators=150, contamination="auto", random_state=0).fit(healthy.fillna(med))
    score = -iforest.score_samples(df[rel].fillna(med))
    ref = np.sort(-iforest.score_samples(healthy.fillna(med)))
    out["anomaly"] = np.searchsorted(ref, score) / len(ref)           # percentile vs healthy training rows
    classes = BOILER_CLASSES if boiler else PRESS_CLASSES
    pos = train[train.next_logged_class.isin(classes)]
    clf = lgb.LGBMClassifier(**dict(params, n_estimators=150, min_child_samples=20)).fit(pos[cols], pos.next_logged_class)
    cp = clf.predict_proba(df[cols])
    for i, c in enumerate(clf.classes_):
        out[f"cp_{c}"] = cp[:, i]
    out = out[out.mill_id < 100]
    return out, dict(cols=cols, models=models, calib=calib, iforest=iforest, rel=rel, med=med, clf=clf)


def evaluate(pred, label):
    res = {}
    masks = {"mill10_all": pred.mill_id == 10,
             "mill10_months9_12": (pred.mill_id == 10) & (pred.t >= CUT),
             "mills1_9_months9_12": (pred.mill_id <= 9) & (pred.t >= CUT),
             "train_oof": (pred.mill_id <= 9) & (pred.t < CUT)}
    for name, m in masks.items():
        m = m & (pred.t >= EVAL_START)
        for h in HORIZONS:
            y = label.loc[m, f"y{h}"]
            if y.nunique() < 2:
                continue
            res[f"{name}/{h}h"] = dict(auc=round(roc_auc_score(y, pred.loc[m, f"p{h}"]), 3),
                                     ap=round(average_precision_score(y, pred.loc[m, f"p{h}"]), 3),
                                     base_rate=round(float(y.mean()), 4))
    return res


def main(augment=False):
    ART.mkdir(exist_ok=True)
    feat = add_labels(build(), pd.read_parquet(DATA / "failures.parquet"), pd.read_parquet(DATA / "maintenance.parquet"))
    aug = None
    if augment:
        rd = lambda n: pd.read_parquet(AUG / f"{n}.parquet")
        aug = add_labels(build(save=False, tel=rd("telemetry"), err=rd("errors"), wo=rd("maintenance")), rd("failures"), rd("maintenance"))
        print(f"Augmented training copies: {aug.mill_id.nunique()} mills at noise_mult 2, {len(aug):,} rows added")
    preds, metrics, bundle = [], {}, {}
    for boiler in (False, True):
        df = feat[feat.is_boiler == boiler]
        if aug is not None:
            df = pd.concat([df, aug[aug.is_boiler == boiler]], ignore_index=True)
        df = df.reset_index(drop=True)
        out, b = fit_group(df, boiler)
        preds.append(out)
        bundle["boiler" if boiler else "press"] = b
        metrics["boiler" if boiler else "press"] = evaluate(out, df[df.mill_id < 100].reset_index(drop=True))
    pred = pd.concat(preds, ignore_index=True)
    pred.to_parquet(DATA / "predictions.parquet")
    feat.to_parquet(DATA / "features_labeled.parquet")
    joblib.dump(bundle, ART / "models.joblib")
    (ART / "model_metrics.json").write_text(json.dumps(metrics, indent=1))
    for g, m in metrics.items():
        print(g)
        for k, v in m.items():
            print(f"  {k:28s} {v}")


if __name__ == "__main__":
    main()
