"""NASA/IMS run-to-failure bearings -> measured warning period and normalised vibration ramp (backend/artifacts/ims_bearings.json).
Data: Qiu, Lee, Lin, Yu (2006), J. Sound and Vibration 289; NASA PCoE data repository (IMS.zip, put in backend/data/ims/).
Failed bearings: set 1 bearing 3 (inner race) and 4 (roller), set 2 bearing 1 (outer race), set 3 bearing 3 (outer race).
Per 1-second snapshot (20 kHz): RMS and kurtosis of the bearing's channels; mean over the channels, then hourly means.
Onset = first hour where RMS or kurtosis exceeds its own first-48-h baseline (median + 4 robust SD) for 3 hours in a row."""
import json
import re
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kurtosis

RAW = Path(__file__).resolve().parents[1] / "data" / "ims"
OUT = Path(__file__).resolve().parents[1] / "artifacts" / "ims_bearings.json"
# (set folder, bearing label, failure mode, 0-based channel columns of the bearing)
BEARINGS = [("1st_test", "set1_b3", "inner race", [4, 5]), ("1st_test", "set1_b4", "roller element", [6, 7]),
            ("2nd_test", "set2_b1", "outer race", [0]), ("3rd_test", "set3_b3", "outer race", [2])]
BASE_H, SD_K, HOLD_H, GRID = 48, 4.0, 3, 101


def unpack():
    z = RAW / "IMS.zip"
    if z.exists() and not list(RAW.glob("*test*")):
        with zipfile.ZipFile(z) as f:
            f.extractall(RAW)
    for r in sorted(p for p in RAW.rglob("*.rar") if not p.name.startswith("._") and "__MACOSX" not in p.parts):
        d = RAW / r.stem
        if not d.exists():
            d.mkdir()   # remove a half-extracted folder to retry
            subprocess.run(["unrar", "x", "-inul", str(r), str(d)], check=True)


def snapshot_stats(set_dir, cols):
    files = sorted(p for p in set_dir.rglob("*") if p.is_file() and re.fullmatch(r"\d{4}\.\d\d\.\d\d\.\d\d\.\d\d\.\d\d", p.name))
    rows = []
    for p in files:
        x = np.loadtxt(p)[:, cols]
        rows.append((pd.to_datetime(p.name, format="%Y.%m.%d.%H.%M.%S"), float(np.sqrt((x ** 2).mean(axis=0)).mean()),
                     float(kurtosis(x, axis=0, fisher=False).mean())))
    return pd.DataFrame(rows, columns=["t", "rms", "kur"]).set_index("t")


def onset_hour(h):
    base = h.iloc[:BASE_H]
    thr = {c: base[c].median() + SD_K * 1.4826 * (base[c] - base[c].median()).abs().median() for c in ("rms", "kur")}
    over = ((h.rms > thr["rms"]) | (h.kur > thr["kur"])).astype(int)
    run = over.rolling(HOLD_H).sum().eq(HOLD_H)
    first = run[BASE_H:].idxmax() if run[BASE_H:].any() else None
    return None if first is None else first - pd.Timedelta(hours=HOLD_H - 1), thr


def curve(h, onset, base):
    """Normalised ramp from onset (0) to failure (1) on GRID points, per signal, from a 6-hour rolling median."""
    out = {}
    seg = h[h.index >= onset]
    x = np.linspace(0, 1, GRID)
    pos = (seg.index - onset) / (h.index[-1] - onset)
    for c in ("rms", "kur"):
        s = seg[c].rolling(6, min_periods=1).median()
        lo, hi = base[c], float(s.iloc[-3:].median())
        if hi - lo < 0.2 * lo:   # this signal does not rise for this bearing (e.g. kurtosis of the roller): no ramp to normalise
            continue
        y = np.clip((s.values - lo) / max(hi - lo, 1e-9), 0, None)
        out[c] = np.interp(x, np.asarray(pos, dtype=float), y)
    return out


def main():
    unpack()
    res, curves = [], {"rms": [], "kur": []}
    for folder, label, mode, cols in BEARINGS:
        h = snapshot_stats(RAW / folder, cols).resample("1h").mean().dropna()
        fail = h.index[-1]
        onset, thr = onset_hour(h)
        base = {c: float(h[c].iloc[:BASE_H].median()) for c in ("rms", "kur")}
        warn = None if onset is None else float((fail - onset) / pd.Timedelta(hours=1)) + 1
        res.append(dict(bearing=label, failure_mode=mode, hours_recorded=len(h), warning_h=warn,
                        onset=None if onset is None else str(onset), failure_time=str(fail),
                        rms_baseline=round(base["rms"], 4), rms_at_failure=round(float(h.rms.iloc[-3:].median()), 4),
                        kurt_baseline=round(base["kur"], 3), kurt_at_failure=round(float(h.kur.iloc[-3:].median()), 3)))
        if onset is not None:
            c = curve(h, onset, base)
            for k in c:
                curves[k].append(c[k])
            res[-1]["curves_used"] = sorted(c)
        print(res[-1])
    ok = [r["warning_h"] for r in res if r["warning_h"]]
    final = {}
    for k in curves:
        m = np.maximum.accumulate(np.mean(curves[k], axis=0))   # averaged, non-decreasing
        m = (m - m[0]) / (m[-1] - m[0])
        final[k] = [round(float(v), 4) for v in m]
    OUT.write_text(json.dumps(dict(
        source="NASA/IMS bearing data (Qiu, Lee, Lin, Yu 2006, J. Sound and Vibration 289; NASA PCoE data repository)",
        method=f"hourly means of per-snapshot RMS and kurtosis; onset = first hour outside own first-{BASE_H} h baseline "
               f"(median + {SD_K} robust SD) for {HOLD_H} h; curves are 0 at onset, 1 at failure, averaged over the failed bearings",
        median_warning_h=float(np.median(ok)), bearings=res, grid_points=GRID, curve_rms=final["rms"], curve_kurtosis=final["kur"]), indent=1))
    print("median warning period (h):", np.median(ok), "from", ok)


if __name__ == "__main__":
    main()
