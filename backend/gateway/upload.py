"""CSV upload (local only): asset_id, t, one column per reading -> a scored scenario "csv_<name>" through the same pipeline."""
import io
import re
from email.parser import BytesParser
from email.policy import default

import numpy as np
import pandas as pd

from backend.gateway import health, scenarios
from backend.gateway.health import BOILER_SIGNALS, PRESS_SIGNALS

ASSET_IDS = ["press_1", "press_2", "press_3", "press_4", "boiler_1"]
MIN_HOURS = 400   # the features need a 30-day baseline


def read_body(raw, content_type, name):
    if content_type.startswith("multipart/form-data"):
        msg = BytesParser(policy=default).parsebytes(b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + raw)
        for part in msg.iter_parts():
            if part.get_filename():
                return name or part.get_filename(), part.get_payload(decode=True)
        raise ValueError("no file in the upload")
    return name or "upload", raw


def build_from_csv(fname, data):
    try:
        df = pd.read_csv(io.BytesIO(data))
    except Exception:
        raise ValueError("could not read the file as CSV")
    if not {"asset_id", "t"} <= set(df.columns):
        raise ValueError("the CSV needs the columns asset_id and t, then one column per reading")
    issues = []
    df["t"] = pd.to_datetime(df["t"], utc=False, errors="coerce")
    if df.t.dt.tz is not None:
        df["t"] = df.t.dt.tz_convert("Asia/Kuala_Lumpur").dt.tz_localize(None)
    bad = df.t.isna() | ~df.asset_id.isin(ASSET_IDS)
    if bad.any():
        issues.append(f"{int(bad.sum())} rows skipped (unknown asset_id or unreadable t)")
    df = df[~bad].copy()
    df["t"] = df.t.dt.floor("h")
    df = df.drop_duplicates(["asset_id", "t"])
    sigs = sorted(set(PRESS_SIGNALS + BOILER_SIGNALS) & set(df.columns))
    if not sigs:
        raise ValueError("no reading columns found (for example motor_current, vib_rms, steam_temp)")
    short = [a for a, g in df.groupby("asset_id") if len(g) < MIN_HOURS]
    if short or df.asset_id.nunique() == 0:
        raise ValueError(f"each asset needs at least {MIN_HOURS} hourly rows; too short: {', '.join(short) or 'all'}")
    # full hourly grid per asset on the 2025 calendar the models know; missing hours stay missing
    t0 = pd.Timestamp("2025-01-01")
    grid = pd.date_range(t0, periods=8760, freq="h")
    frames = []
    for a in ASSET_IDS:
        g = df[df.asset_id == a].set_index("t").reindex(grid)
        cols = BOILER_SIGNALS if a == "boiler_1" else PRESS_SIGNALS
        out = pd.DataFrame({c: g[c] if c in g.columns else np.nan for c in cols}, index=grid)
        out.insert(0, "t", grid); out.insert(0, "asset_id", a); out.insert(0, "mill_id", 10)
        if a != "boiler_1":
            out["current_per_tonne"] = np.where(out.throughput_tph > 3, out.motor_current / np.maximum(out.throughput_tph, 1e-9), np.nan)
        frames.append(out.reset_index(drop=True))
    for a in ASSET_IDS:
        if a not in set(df.asset_id):
            issues.append(f"{a} has no rows; its readings are treated as missing")
    tel = pd.concat(frames, ignore_index=True)
    sid = "csv_" + re.sub(r"[^a-z0-9]+", "_", fname.lower().rsplit(".", 1)[0]).strip("_")[:24]
    empty_f = pd.DataFrame({"failure_id": [], "mill_id": [], "asset_id": [], "t": pd.to_datetime([]), "fault_class": [], "downtime_h": []})
    # no work-order history is uploaded: one placeholder "logged service" per asset at the start of the calendar keeps the service-age features defined
    empty_wo = pd.DataFrame({"failure_id": [f"csv_{a}" for a in ASSET_IDS], "mill_id": 10, "asset_id": ASSET_IDS, "t": t0,
                             "fault_class": ["worm_wear"] * 4 + ["boiler_steam"], "downtime_h": 0.0, "parts_cost_rm": 0, "kind": "planned"})
    empty_err = pd.DataFrame({"mill_id": [], "asset_id": [], "t": pd.to_datetime([]), "error_code": []})
    lives = pd.DataFrame({"mill_id": [], "asset_id": [], "comp": [], "k": [], "life": [], "amp": [], "unk": [], "age0": []})
    hidden = pd.DataFrame({"mill_id": [], "asset_id": [], "t": pd.to_datetime([]), "inc": []})
    start = scenarios.iso(max(df.t.min() + pd.Timedelta(hours=720), t0))
    try:
        scenarios._write_dataset(sid, tel, empty_err, empty_wo, empty_f, lives, hidden, start)
    except Exception as e:
        raise ValueError(f"could not score this file ({type(e).__name__}); check the columns and hourly timestamps")
    scenarios._cache.pop(sid, None)
    return dict(scenario_id=sid, rows=int(len(df)), assets=int(df.asset_id.nunique()), issues=issues)
