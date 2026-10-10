"""SHAP top-3 reasons -> plain sentences (EN, BM) from templates in text.py. No LLM."""
import numpy as np
import pandas as pd
import shap

from backend.engine import text
from backend.sim.simulate import DATA

SERVICE_FEATS = {"h_since_wo", "t_since_wo", "h_since_worm", "t_since_worm"}


def group_of(feat: str):
    if feat in SERVICE_FEATS:
        return "hours_since_service"
    if feat == "errors24":
        return "alarms"
    if feat in ("load24", "run_frac24"):
        return "load"
    for s in sorted(text.SIGNAL_LABEL, key=len, reverse=True):
        if feat.startswith(s + "_"):
            return s
    return None


class Explainer:
    def __init__(self, bundle, feats: pd.DataFrame):
        self.b, self.feats = bundle, feats.set_index(["mill_id", "asset_id", "t"]).sort_index()
        self.expl = {k: shap.TreeExplainer(v["models"][72]) for k, v in bundle.items()}

    def reasons(self, mill, asset, t, asset_name):
        kind = "boiler" if asset.startswith("boiler") else "press"
        cols = self.b[kind]["cols"]
        row = self.feats.loc[(mill, asset, t)][cols]
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sv = self.expl[kind].shap_values(row.to_frame().T.astype(float))
        sv = np.asarray(sv[1] if isinstance(sv, list) else sv).reshape(-1)[: len(cols)]
        score = {}
        for f, v in zip(cols, sv):
            g = group_of(f)
            if g and v > 0:
                score[g] = score.get(g, 0) + v
        ranked = sorted(score, key=score.get, reverse=True)
        telemetry = [g for g in ranked if g in text.SIGNAL_LABEL]
        order = telemetry[:1] + [g for g in ranked if g not in telemetry[:1]]
        res = []
        for g in order:
            sent = self.sentence(g, row, asset_name)
            if sent:   # a reason whose change rounds to 0% says nothing: skip it and use the next one
                res.append((g, score[g], sent))
            if len(res) == 3:
                break
        total = sum(v for _, v, _ in res) or 1.0
        return [dict(text_en=en, text_ms=ms, signal=g, direction=d, contribution=round(float(v / total), 3))
                for g, v, (en, ms, d) in res]

    def sentence(self, g, row, asset):
        asset_ms = text.name_ms(asset)
        if g == "hours_since_service":
            h = row.get("h_since_worm", np.nan)
            h = row.get("h_since_wo", np.nan) if pd.isna(h) else h
            h = 0 if pd.isna(h) else h
            return (text.REASON_SERVICE_EN.format(h=h, asset=asset), text.REASON_SERVICE_MS.format(h=h, asset=asset_ms), "up")
        if g == "alarms":
            n = row.get("errors24", 0)
            if round(n) == 0:
                return None
            return text.REASON_ALARMS_EN.format(n=n, asset=asset), text.REASON_ALARMS_MS.format(n=n, asset=asset_ms), "up"
        if g == "load":
            return text.REASON_LOAD_EN.format(asset=asset), text.REASON_LOAD_MS.format(asset=asset_ms), "up"
        lab_en, lab_ms = text.SIGNAL_LABEL[g]
        rel = row.get(f"{g}_ps24", np.nan)
        if pd.isna(rel):
            rel = row.get(f"{g}_rel24", 0.0)
        rel = 0.0 if pd.isna(rel) else float(rel)
        d = "up" if rel >= 0 else "down"
        if g == "fibre_oil_loss":
            v = float(row.get("fibre_oil_loss_abs24", np.nan))
            if not np.isnan(v):
                return text.REASON_FIBRE_EN.format(v=v), text.REASON_FIBRE_MS.format(v=v), d
        pct = abs(rel) * 100
        if round(pct) == 0:
            return None
        return (text.REASON_REL_EN.format(label=lab_en, pct=pct, word=text.WORD_EN[d], asset=asset),
                text.REASON_REL_MS.format(label=lab_ms, pct=pct, word=text.WORD_MS[d], asset=asset_ms), d)
