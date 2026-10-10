"""Write the small artifacts the API reads: mill-10 tables, actions (with SHAP reasons), replay markers."""
import json

import joblib
import numpy as np
import pandas as pd

from backend.engine import cost, decide, fingerprint, text
from backend.engine.explain import Explainer
from backend.engine.service import ART, ASSETS, DAY_EN, DAY_MS, NAME, Service, iso
from backend.params import val
from backend.sim.simulate import DATA

MILL = 10


def write_tables():
    ART.mkdir(exist_ok=True)
    for src, dst, col in [("predictions", "mill10_predictions", "mill_id"), ("failures", "mill10_failures", "mill_id"),
                          ("lives", "mill10_lives", "mill_id"), ("hidden", "mill10_hidden", "mill_id"),
                          ("maintenance", "mill10_maintenance", "mill_id"), ("errors", "mill10_errors", "mill_id")]:
        d = pd.read_parquet(DATA / f"{src}.parquet")
        d[d[col] == MILL].reset_index(drop=True).to_parquet(ART / f"{dst}.parquet")
    tel = pd.read_parquet(DATA / "telemetry.parquet")
    tel[tel.mill_id == MILL].reset_index(drop=True).to_parquet(ART / "mill10_telemetry.parquet")


def headline(p, ep):
    fc = ep.fault_class
    nm_en, nm_ms = NAME[ep.asset_id], text.name_ms(NAME[ep.asset_id])
    f_en, f_ms = text.FAULT_LABEL[fc]; ph_en, ph_ms = text.FIX_PHRASE[fc]
    if ep.recommendation == "fix_now":
        return (text.HEADLINE_FIX_EN.format(asset=nm_en, fault=f_en.capitalize(), phrase=ph_en),
                text.HEADLINE_FIX_MS.format(asset=nm_ms, fault=f_ms.capitalize(), phrase=ph_ms))
    d = ep.t_repair
    if d.date() == (ep.t_open + pd.Timedelta(days=1)).date():
        w_en, w_ms = text.WHEN_TOMORROW
    else:
        w_en, w_ms = (text.WHEN_DAY[0].format(day=DAY_EN[d.dayofweek]), text.WHEN_DAY[1].format(day=DAY_MS[d.dayofweek]))
    return (text.HEADLINE_SCHED_EN.format(asset=nm_en, fault=f_en.capitalize(), phrase=ph_en, when=w_en),
            text.HEADLINE_SCHED_MS.format(asset=nm_ms, fault=f_ms.capitalize(), phrase=ph_ms, when=w_ms))


def build_actions(p, fit):
    from backend.engine import backtest
    pred = pd.read_parquet(ART / "mill10_predictions.parquet")
    fails = pd.read_parquet(ART / "mill10_failures.parquet")
    thr = {t: decide.risk_threshold(p, t, fit["k"][t]) for t in ("press", "boiler")}
    ep = decide.run_mill(p, pred, fails, thr, 5, None, 1.0, MILL, fit["trigger"])
    ex = Explainer(joblib.load(ART / "models.joblib"), pd.read_parquet(DATA / "features_labeled.parquet"))
    out = []
    for r in ep.itertuples():
        atype = "boiler" if r.asset_id.startswith("boiler") else "press"
        trig = fit["trigger"][atype]
        hts = decide.hours_to_stop(r.t_open, val(p, "alerting", "min_lead_h"))
        if trig == "pstop":
            horizon, risk = min(hts, 168), r.p_stop
        elif trig == "p168":
            horizon, risk = 168, r.risk168
        else:
            horizon, risk = (24, r.risk24) if r.risk24 >= thr[atype] else (72, r.risk72)
        t_close = min(r.t_close, r.t_repair)
        if r.fail_idx is not None and not pd.isna(r.fail_idx):
            t_close = min(t_close, pd.Timestamp("2025-01-01") + pd.Timedelta(hours=int(r.fail_idx)))
        pool = ex.reasons(MILL, r.asset_id, r.t_open, NAME[r.asset_id])
        en, ms = headline(p, r)
        hold = r.t_close   # the decision layer will not re-alert before this (risk must clear, or the would-be failure pass)
        if r.outcome == "prevented":
            hold = pd.Timestamp("2025-01-01") + pd.Timedelta(hours=int(r.fail_idx) + decide.POST_FAIL_H)
        out.append(dict(
            id=f"act_{r.asset_id}_{r.t_open:%Y%m%d%H}", asset_id=r.asset_id, asset_name=NAME[r.asset_id], asset_name_ms=text.name_ms(NAME[r.asset_id]), asset_type=atype,
            fault_class=r.fault_class, risk_pct=round(float(risk * 100), 0),
            horizon_h=int(horizon), rm_at_risk=int(r.rm_at_risk), rm_cost_to_act=int(r.rm_cost_to_act),
            rm_saved_if_acted=int(r.rm_saved), recommendation=r.recommendation, deadline=iso(r.t_repair),
            headline_en=en, headline_ms=ms, reasons=pool[:3],
            criticality="whole_mill" if atype == "boiler" else "partial",
            t_open=iso(r.t_open), t_close=iso(t_close), t_candidate=iso(r.t_candidate),
            internal=dict(reason_pool=pool, t_hold=iso(max(hold, t_close)), outcome=r.outcome, fail_idx=None if r.fail_idx is None or pd.isna(r.fail_idx) else int(r.fail_idx))))
    fails = pd.read_parquet(ART / "mill10_failures.parquet")
    (ART / "test_mill.json").write_text(json.dumps(backtest.test_mill_table(ep, fails), indent=1))
    (ART / "actions.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    return ep


def build_markers(svc: Service, ep):
    M = text.MARKERS
    nights = [t for t in svc.times if t.hour == 19 and t >= pd.Timestamp("2025-02-01")]
    briefs = {t: svc.brief(iso(t)) for t in nights}
    # quiet = no action, and waiting is cheaper for every machine (no outlook saving); prefer nights with something being watched
    quiet = [t for t, b in briefs.items() if not b["actions"]
             and all(svc._outlook(a, ty, None, t)["rm_saved_if_acted"] == 0 for a, _, ty, _ in ASSETS)]
    q = ([t for t in quiet if briefs[t]["watching_count"] and briefs[t]["suppressed_count"]] or
         [t for t in quiet if briefs[t]["watching_count"] or briefs[t]["suppressed_count"]] or quiet)
    print(f"quiet nights: {len(quiet)} (with watching/suppressed: {len([t for t in quiet if briefs[t]['watching_count'] or briefs[t]['suppressed_count']])})")
    q_t = q[len(q) // 3] if q else nights[0]
    gradual = {"worm_wear", "bearing", "gearbox_shaft", "hydraulic_cone"}
    cands = []   # (matches, saved, -hour, t, action): true-positive alerts on gradual faults, every hour of their window
    for a in svc.actions:
        e = ep[(ep.asset_id == a["asset_id"]) & (ep.t_open == a["t_open"])]
        if a["t_open"] < pd.Timestamp("2025-02-01") or a["asset_type"] != "press" or a["fault_class"] not in gradual \
                or not len(e) or e.iloc[0].outcome != "prevented":
            continue
        for t in pd.date_range(a["t_open"], a["t_close"] - pd.Timedelta(hours=1), freq="h"):
            m = sum(c.matches for c in fingerprint.fingerprint(svc.tel, a["asset_id"], a["fault_class"], t))
            sv = svc._money(dict(a), a, t)["rm_saved_if_acted"]
            cands.append((a["asset_id"] == "press_2", m, sv, -t.value, t, a))
    act = max(cands, key=lambda c: c[:4]) if cands else None
    onset = act[4] if act else nights[len(nights) // 2]
    act_asset = act[5] if act else dict(asset_id="press_2", fault_class="worm_wear")
    whole = []   # boiler true-positive alerts (prevented), every hour of their window
    for a in svc.actions:
        e = ep[(ep.asset_id == a["asset_id"]) & (ep.t_open == a["t_open"])]
        if a["asset_id"] != "boiler_1" or a["t_open"] < pd.Timestamp("2025-02-01") or not len(e) or e.iloc[0].outcome != "prevented":
            continue
        for t in pd.date_range(a["t_open"], a["t_close"] - pd.Timedelta(hours=1), freq="h"):
            live = svc._live(t)
            first = bool(live) and live[0][1]["asset_id"] == "boiler_1"
            m = sum(c.matches for c in fingerprint.fingerprint(svc.tel, "boiler_1", a["fault_class"], t))
            whole.append((first, m, svc._money(dict(a), a, t)["rm_saved_if_acted"], -t.value, t))
    both_t = max(whole)[4] if whole else None
    nm = NAME[act_asset["asset_id"]]; f_en, f_ms = text.FAULT_LABEL[act_asset["fault_class"]]
    out = [dict(t=iso(q_t), kind="bookmark", label_en=M["quiet_en"], label_ms=M["quiet_ms"]),
           dict(t=iso(onset), kind="bookmark", asset_id=act_asset["asset_id"],
                label_en=M["act_en"].format(asset=nm, fault=f_en), label_ms=M["act_ms"].format(asset=text.name_ms(nm), fault=f_ms))]
    if both_t is not None:
        out.append(dict(t=iso(both_t), kind="bookmark", label_en=M["both_en"], label_ms=M["both_ms"]))
    for r in ep.itertuples():
        nm = NAME[r.asset_id]
        out.append(dict(t=iso(r.t_open), kind="alert", asset_id=r.asset_id,
                        label_en=M["alert_en"].format(asset=nm), label_ms=M["alert_ms"].format(asset=text.name_ms(nm))))
    for r in svc.fails.itertuples():
        nm = NAME[r.asset_id]
        out.append(dict(t=iso(r.t), kind="breakdown", asset_id=r.asset_id,
                        label_en=M["breakdown_en"].format(asset=nm), label_ms=M["breakdown_ms"].format(asset=text.name_ms(nm))))
    out.sort(key=lambda m: m["t"])
    (ART / "markers.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print("bookmarks:", [(m["t"], m["label_en"]) for m in out if m["kind"] == "bookmark"],
          "" if both_t is not None else "\nWARNING: no prevented boiler alert")


def main():
    from backend.params import load
    p = load()
    fit = json.loads((ART / "policy_fit.json").read_text())
    write_tables()
    ep = build_actions(p, fit)
    build_markers(Service(), ep)


if __name__ == "__main__":
    main()
