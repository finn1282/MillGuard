"""Hourly features per (mill, asset): rolling 6/24/72 h stats relative to a 30-day baseline,
errors, load, and hours/tonnes since logged service."""
import numpy as np
import pandas as pd

from backend.sim.simulate import DATA, H

PRESS_SIGS = ["motor_current", "current_per_tonne", "cone_pressure", "gearbox_oil_temp",
              "vib_rms", "vib_kurtosis", "fibre_oil_loss"]
BOILER_SIGS = ["steam_temp", "steam_pressure", "feedwater_flow", "feedwater_cond"]
PRESS_CLASSES = ["worm_wear", "bearing", "gearbox_shaft", "hydraulic_cone", "electrical", "unknown"]
BOILER_CLASSES = ["boiler_steam", "boiler_water"]


def sig_features(s: pd.Series, name: str) -> dict:
    base = s.rolling(720, min_periods=168).median()
    out = {}
    m = {w: s.rolling(w, min_periods=max(2, w // 4)).mean() for w in (6, 24, 72)}
    for w in (6, 24, 72):
        out[f"{name}_rel{w}"] = m[w] / base - 1
    out[f"{name}_abs24"] = m[24]
    out[f"{name}_sd24"] = s.rolling(24, min_periods=6).std() / base
    out[f"{name}_slope"] = out[f"{name}_rel24"] - out[f"{name}_rel72"]
    return out


SERVICE_OF = {"current_per_tonne": "worm_wear", "motor_current": "worm_wear", "fibre_oil_loss": "worm_wear",
              "vib_rms": "bearing", "vib_kurtosis": "bearing", "gearbox_oil_temp": "gearbox_shaft",
              "cone_pressure": "hydraulic_cone"}


def post_service_rel(x: pd.Series, m24: pd.Series, m72: pd.Series, wo_h) -> tuple:
    """Signal relative to its own level in the 24-192 h after the last logged service of its component."""
    n = len(x)
    if len(wo_h) == 0:
        return np.full(n, np.nan), np.full(n, np.nan)
    v = x.values
    ref = np.array([np.nanmedian(v[h + 24: h + 192]) if h + 192 <= n else np.nan for h in wo_h])
    idx = np.arange(n)
    j_ref = np.searchsorted(wo_h + 192, idx, side="right") - 1      # last service whose reference window is complete
    j_last = np.searchsorted(wo_h, idx, side="right") - 1           # last service so far
    ok = (j_ref >= 0) & (j_ref == j_last)
    r = np.where(ok, ref[np.maximum(j_ref, 0)], np.nan)
    return m24.values / r - 1, m72.values / r - 1


def since_wo(h_idx, wo_h, ct):
    """Hours and tonnes since the last logged work order (NaN before the first one)."""
    j = np.searchsorted(wo_h, h_idx, side="right") - 1
    last = np.where(j >= 0, wo_h[np.maximum(j, 0)], np.nan)
    hrs = h_idx - last
    tonnes = np.where(j >= 0, ct[h_idx] - ct[np.nan_to_num(last).astype(int)], np.nan)
    return hrs, tonnes


def build(save=True) -> pd.DataFrame:
    tel = pd.read_parquet(DATA / "telemetry.parquet")
    err = pd.read_parquet(DATA / "errors.parquet")
    wo = pd.read_parquet(DATA / "maintenance.parquet")
    t0 = tel.t.min()
    rows = []
    for mill, mt in tel.groupby("mill_id"):
        tph_mill = mt[mt.asset_id.str.startswith("press")].groupby("t").throughput_tph.sum().reindex(
            pd.date_range(t0, periods=H, freq="h")).fillna(0)
        for asset, g in mt.groupby("asset_id"):
            g = g.sort_values("t").set_index("t")
            is_press = asset.startswith("press")
            sigs = PRESS_SIGS if is_press else BOILER_SIGS
            x = g[sigs].copy()
            if is_press:
                running = g.throughput_tph > 0.5
                x = x.where(running)
                x["fibre_oil_loss"] = g.fibre_oil_loss.ffill(limit=36).where(running)
                load = g.throughput_tph.fillna(0)
            else:
                load = tph_mill.values
                load = pd.Series(load, index=g.index)
            f = {}
            for s in sigs:
                f.update(sig_features(x[s], s))
            if is_press:
                w_all = wo[(wo.mill_id == mill) & (wo.asset_id == asset)]
                for s, cls in SERVICE_OF.items():
                    hh = np.sort(((w_all[w_all.fault_class == cls].t - t0) / pd.Timedelta(hours=1)).astype(int).clip(0, H - 1).values)
                    f[f"{s}_ps24"], f[f"{s}_ps72"] = post_service_rel(x[s], x[s].rolling(24, min_periods=6).mean(),
                                                                        x[s].rolling(72, min_periods=18).mean(), hh)
            f["load24"] = load.rolling(24, min_periods=1).mean()
            f["run_frac24"] = (load > 0.5).astype(float).rolling(24, min_periods=1).mean()
            e = err[(err.mill_id == mill) & (err.asset_id == asset)]
            ec = pd.Series(0.0, index=g.index)
            ec.loc[ec.index.intersection(pd.DatetimeIndex(e.t))] = 1.0
            f["errors24"] = ec.rolling(24, min_periods=1).sum()
            w = wo[(wo.mill_id == mill) & (wo.asset_id == asset)]
            h_idx = np.arange(len(g))
            ct = np.cumsum(load.fillna(0).values)
            def hrs_of(df):
                return np.sort(((df.t - t0) / pd.Timedelta(hours=1)).astype(int).clip(0, H - 1).values)
            ha, ta = since_wo(h_idx, hrs_of(w), ct)
            f["h_since_wo"], f["t_since_wo"] = ha, ta
            if is_press:
                hw, tw = since_wo(h_idx, hrs_of(w[w.fault_class == "worm_wear"]), ct)
                f["h_since_worm"], f["t_since_worm"] = hw, tw
            df = pd.DataFrame(f, index=g.index)
            df.insert(0, "asset_id", asset); df.insert(0, "mill_id", mill)
            rows.append(df.reset_index())
    feat = pd.concat(rows, ignore_index=True)
    feat["is_boiler"] = feat.asset_id.eq("boiler_1")
    if save:
        feat.to_parquet(DATA / "features.parquet")
    return feat


if __name__ == "__main__":
    f = build(); print(f.shape)
