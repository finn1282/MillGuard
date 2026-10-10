"""Scenarios: full simulated datasets, scored by the trained models with the same pipeline as mill 10
(features -> models.joblib -> decide rules and thresholds -> build_artifacts). Built by `make scenarios`, never hand-written.
Each lives in backend/artifacts/scenarios/<id>/ (same table files the Service reads). The stream replays one hour by hour."""
import json
import os
import time

import joblib
import numpy as np
import pandas as pd

from backend.engine import build_artifacts
from backend.engine.service import ART, Service, files, iso
from backend.features.build import build
from backend.gateway import health
from backend.params import load
from backend.robustness.stress import predict
from backend.sim import simulate

DIR = ART / "scenarios"
T0 = pd.Timestamp("2025-01-01")
GATEWAY = "demo-gw1"
FORCED_H0 = pd.Timestamp("2025-09-15 08:00")

DEFS = {
    "mill10": dict(name=("Mill 10 (held-out mill)", "Kilang 10 (kilang yang tidak dilihat)"),
                   desc=("The unseen demo mill, hour by hour. Starts four days before Press 2's worm wear is flagged.",
                         "Kilang demo yang tidak dilihat, jam demi jam. Bermula empat hari sebelum kehausan worm Penekan 2 ditandakan.")),
    "bearing_p3": dict(name=("Bearing failure on Press 3", "Kerosakan bearing pada Penekan 3"), force=("press_3", "bearing"),
                       desc=("Mill 10 with a bearing failing on Press 3 about 100 running hours after the start; its normal warning ramp comes first.",
                             "Kilang 10 dengan bearing Penekan 3 rosak kira-kira 100 jam larian selepas permulaan; amaran biasa datang dahulu.")),
    "worm_p1": dict(name=("Worm wear on Press 1", "Kehausan worm pada Penekan 1"), force=("press_1", "worm_wear"),
                    desc=("Mill 10 with the screw-press worm wearing out on Press 1 about 100 running hours after the start.",
                          "Kilang 10 dengan worm skru Penekan 1 haus kira-kira 100 jam larian selepas permulaan.")),
    "boiler_water": dict(name=("Feed-water fault on the boiler", "Kerosakan air suapan pada dandang"), force=("boiler_1", "boiler_water"),
                         desc=("Mill 10 with a feed-water quality fault on the boiler about 100 running hours after the start (a whole-mill risk).",
                               "Kilang 10 dengan kerosakan kualiti air suapan pada dandang kira-kira 100 jam larian selepas permulaan (risiko seluruh kilang).")),
    "bad_sensor": dict(name=("Faulty vibration sensor on Press 4", "Penderia getaran rosak pada Penekan 4"),
                       desc=("Press 4's vibration sensor sticks for 12 hours, then spikes. There is no machine fault: expect a sensor alert and no machine alert.",
                             "Penderia getaran Penekan 4 tersekat selama 12 jam, kemudian melonjak. Tiada kerosakan mesin: jangkakan amaran penderia, bukan amaran mesin.")),
}
ORDER = ["mill10", "bearing_p3", "worm_p1", "boiler_water", "bad_sensor"]
_cache = {}


# ---- registry (read side)
def root(sid):
    d = DIR / sid
    return d if (d / "actions.json").exists() else None


def meta(sid):
    d = root(sid)
    return json.loads((d / "meta.json").read_text()) if d and (d / "meta.json").exists() else None


def upload_enabled():
    return os.environ.get("VERCEL") != "1"


def listing():
    out = []
    ids = [s for s in ORDER if root(s)] + sorted(p.name for p in DIR.glob("csv_*") if (p / "actions.json").exists()) if DIR.exists() else []
    for sid in ids:
        m, dfn = meta(sid), DEFS.get(sid)
        name = dfn["name"] if dfn else (sid, sid)
        desc = dfn["desc"] if dfn else ("Your uploaded CSV, scored by the trained models.", "CSV anda, dinilai oleh model terlatih.")
        out.append(dict(id=sid, name_en=name[0], name_ms=name[1], description_en=desc[0], description_ms=desc[1],
                        default_start=m["default_start"], hours=m["hours"], upload_enabled=upload_enabled()))
    return out


def service(sid):
    """The scenario's Service, loaded once per process."""
    if sid not in _cache:
        d = root(sid)
        if d is None:
            return None
        _cache[sid] = Service(d, "")
    return _cache[sid]


def hours(sid, start, n):
    """The next n hours of gateway payloads (n hours x 5 assets, oldest first), straight from the scenario's raw readings."""
    svc = service(sid)
    t0 = pd.Timestamp(start).tz_localize(None) if pd.Timestamp(start).tzinfo is None else pd.Timestamp(start).tz_convert("Asia/Kuala_Lumpur").tz_localize(None)
    t0 = t0.floor("h")
    tel = svc.tel[(svc.tel.t >= t0) & (svc.tel.t < t0 + pd.Timedelta(hours=n))].sort_values(["t", "asset_id"])
    out = []
    for r in tel.to_dict("records"):
        sigs = health.BOILER_SIGNALS if r["asset_id"].startswith("boiler") else health.PRESS_SIGNALS
        out.append(dict(gateway_id=GATEWAY, source=f"scenario:{sid}", asset_id=r["asset_id"], t=iso(r["t"]),
                        readings={s: None if pd.isna(r[s]) else round(float(r[s]), 4) for s in sigs}))
    return out


# ---- build side
HOLD_H = 24   # after the last bad reading, the rolling features need a day to recover


def hold_during_quarantine(pred, issues):
    """While a sensor is quarantined (a frozen, spiking or out-of-range reading was masked), the machine's risk is held at its last
    trusted value: the models are not asked to judge a machine from a sensor we do not trust."""
    cols = [c for c in pred.columns if c.startswith(("p24", "p72", "p168", "cp_"))]
    pred = pred.sort_values(["asset_id", "t"]).reset_index(drop=True)
    bad = issues[issues.kind != "missing"]
    for aid, g in bad.groupby("asset_id"):
        idx = pred.index[pred.asset_id == aid]
        t = pred.t[idx]
        held = pd.Series(False, index=idx)
        for tf in g.t:
            held |= (t >= tf) & (t <= tf + pd.Timedelta(hours=HOLD_H))
        starts = [i for i in idx if held[i] and (i == idx[0] or not held[i - 1])]
        for i0 in starts:
            j = i0
            while j in held.index and held[j]:
                j += 1
            if i0 > idx[0]:
                pred.loc[i0:j - 1, cols] = pred.loc[i0 - 1, cols].values
    return pred


def _write_dataset(sid, telemetry, errors, maintenance, failures, lives, hidden, default_start, extra=None):
    tel, err, wo, fails = telemetry, errors, maintenance, failures
    p = load()
    fit = json.loads((ART / "policy_fit.json").read_text())
    bundle = joblib.load(ART / "models.joblib")
    masked, issues = health.scan(tel)                         # flagged readings are masked before scoring
    feats = build(save=False, tel=masked, err=err, wo=wo)
    pred = hold_during_quarantine(predict(feats, bundle), issues)
    d = DIR / sid
    d.mkdir(parents=True, exist_ok=True)
    for name, df in dict(predictions=pred, failures=fails, telemetry=tel, lives=lives, hidden=hidden, maintenance=wo, errors=err).items():
        df.reset_index(drop=True).to_parquet(d / f"{name}.parquet")
    f = files(d, "")
    ep = build_artifacts.build_actions(p, fit, f, feats)
    (d / "meta.json").write_text(json.dumps(dict(default_start=default_start, hours=int(tel.t.nunique()), sensor_issues_found=len(issues), **(extra or {}))))
    return ep, issues


def _tables(out):
    return {k: out[k].reset_index(drop=True) for k in ("telemetry", "errors", "maintenance", "failures", "lives", "hidden")}


def _mill10_tables():
    rd = lambda n: (lambda x: x[x.mill_id == 10].reset_index(drop=True))(pd.read_parquet(simulate.DATA / f"{n}.parquet"))
    return dict(telemetry=rd("telemetry"), errors=rd("errors"), maintenance=rd("maintenance"), failures=rd("failures"),
                lives=rd("lives"), hidden=rd("hidden"))


def build_one(sid):
    t = time.time()
    if sid == "mill10":
        tb = _mill10_tables()
        act = next(m for m in json.loads((ART / "markers.json").read_text()) if m["kind"] == "bookmark" and m["label_en"].endswith("act now"))
        start = iso(pd.Timestamp(act["t"]).tz_localize(None) - pd.Timedelta(hours=96))
        ep, issues = _write_dataset(sid, **tb, default_start=start)
    elif sid == "bad_sensor":
        for skip in range(6):   # the stream must raise a sensor alert and no machine alert on Press 4
            tb = _mill10_tables()
            tb["telemetry"], start, extra = inject_sensor_fault(tb["telemetry"], tb["failures"], tb["maintenance"], skip)
            ep, issues = _write_dataset(sid, **tb, default_start=start, extra=extra)
            w0 = pd.Timestamp(extra["fault_window"]["stuck_from"]).tz_localize(None)
            if not ((ep.asset_id == "press_4") & (ep.t_open >= w0 - pd.Timedelta(hours=24)) & (ep.t_open <= w0 + pd.Timedelta(hours=96))).any():
                break
        else:
            raise SystemExit("bad_sensor: every candidate window raised a Press 4 machine alert")
    else:
        asset, comp = DEFS[sid]["force"]
        h0 = int((FORCED_H0 - T0) / pd.Timedelta(hours=1))
        tb = _tables(simulate.simulate_all(mills=[10], write=False, force_spec=(asset, comp, h0, 100)))
        ep, issues = _write_dataset(sid, **tb, default_start=iso(FORCED_H0), extra=dict(forced=dict(asset_id=asset, fault_class=comp)))
        fail_t = tb["failures"][(tb["failures"].asset_id == asset) & (tb["failures"].t > FORCED_H0)].t.min()
        hit = ep[(ep.asset_id == asset) & (ep.t_open < fail_t) & (ep.t_open > fail_t - pd.Timedelta(hours=300))]
        if len(hit):   # start the stream a day before the alert so the viewer sees it arrive
            start = iso(max(hit.t_open.min() - pd.Timedelta(hours=24), FORCED_H0 - pd.Timedelta(hours=300)))
            m = json.loads((DIR / sid / "meta.json").read_text()); m["default_start"] = start
            (DIR / sid / "meta.json").write_text(json.dumps(m))
        else:
            print(f"WARNING {sid}: the forced failure was not alerted")
    print(f"scenario {sid}: built in {time.time() - t:.0f} s; {len(ep)} alerts, {len(issues)} sensor issues")
    return ep


def inject_sensor_fault(tel, fails, wo, skip=0):
    """Mill 10, Press 4: the vibration sensor freezes for 12 running hours, then spikes for 2. No machine fault is added: we take a
    stretch in which Press 4 has no failure, no logged work and no mill-10 alert within 10 days. `skip` takes the next candidate."""
    tel = tel.copy()
    p4 = tel[tel.asset_id == "press_4"].sort_values("t")
    acts = json.loads((ART / "actions.json").read_text())
    busy = pd.concat([fails[fails.asset_id == "press_4"].t, wo[wo.asset_id == "press_4"].t,
                      pd.Series([pd.Timestamp(a["t_open"]).tz_localize(None) for a in acts if a["asset_id"] == "press_4"])])
    found = 0
    for i in p4[(p4.t >= "2025-06-01") & (p4.throughput_tph > 0.5)].index:
        win = p4.loc[i - 1: i + 14]
        if len(win) == 16 and (win.throughput_tph.iloc[1:15] > 0.5).all() and ((busy - p4.t[i]).abs() > pd.Timedelta(days=10)).all():
            if found == skip:
                break
            found += 1
    stuck = list(range(i, i + 12)); spike = [i + 12, i + 13]
    for col, k in (("vib_rms", 6.0), ("vib_kurtosis", 3.0)):
        base = float(np.nanmedian(tel.loc[i: i + 13, col]))   # the sensor freezes at a normal running value
        tel.loc[stuck, col] = base
        tel.loc[spike, col] = base * k
    start = iso(p4.t[i] - pd.Timedelta(hours=24))
    return tel, start, dict(fault_window=dict(stuck_from=iso(p4.t[i]), spike_at=iso(p4.t[i + 12])))


def main(ids=None):
    t = time.time()
    for sid in ids or ORDER:
        build_one(sid)
    print(f"all scenarios built in {time.time() - t:.0f} s")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:] or None)
