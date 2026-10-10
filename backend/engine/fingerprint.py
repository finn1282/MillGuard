"""Fault fingerprint: does each signature signal's last 5 days move the way the fault guide expects?

Rule v2 (checked on training mills only, backend/scripts/fingerprint_check.py):
- up/down: z-score of the last 48 h vs the machine's own 30 days before the window (daily-mean spread), plus a 0.5% floor;
  the old 2% floor of the absolute value made no sense for degC or bar readings.
- only hours when the plant is running are compared (press: throughput > 3 t/h; boiler: steam temperature > 500 degC), so
  start-up and stop hours do not pollute the baseline.
- feedwater flow is compared per tonne of fruit pressed, because it follows the mill load and the crop season.
- unstable: ratio 1.3 (was 1.5); step-to-step spread of a 120 h window is noisy.
"""
import numpy as np
import pandas as pd

from backend.engine import playbook, text

WIN_H, BASE_D = 120, 30
PCT_MIN, Z_MIN, UNSTABLE_X, SPIKE_Z = 0.5, 1.5, 1.3, 4.0
BOILER_UP_C = 500.0   # steam above this = boiler firing (stopped hours read about 10% lower)


def running_signal(tel, aid, sig):
    g = tel[tel.asset_id == aid].set_index("t")
    if aid.startswith("press"):
        return g[sig].where(g.throughput_tph > 3).dropna()
    s = g[sig].where(g.steam_temp > BOILER_UP_C)
    if sig == "feedwater_flow":
        tph = tel[tel.asset_id.str.startswith("press")].groupby("t").throughput_tph.sum()
        s = (s / tph.reindex(s.index).where(lambda x: x > 3))
    return s.dropna()


def _series(tel, aid, sig, t):
    s = running_signal(tel, aid, sig)
    lo = t - pd.Timedelta(hours=WIN_H)
    return s[(s.index > lo - pd.Timedelta(days=BASE_D)) & (s.index <= lo)], s[(s.index > lo) & (s.index <= t)]


def _observe(base, win, expected):
    """-> (matches, kind, numbers) from a baseline series and the last-5-days series."""
    if len(base) < 24 or len(win) < 3:
        return False, "nodata", {}
    mu = float(base.mean())
    if expected in ("up", "down"):
        recent = float(win.iloc[-max(3, min(len(win), 48)):].mean())
        pct = (recent - mu) / abs(mu) * 100 if mu else 0.0
        sd_d = float(base.resample("D").mean().std()) or 1e-9
        z = (recent - mu) / sd_d
        slope = np.polyfit(np.arange(len(win)), win.values, 1)[0]
        sign = 1 if expected == "up" else -1
        ok = sign * pct >= PCT_MIN and sign * z >= Z_MIN and sign * slope > 0
        kind = "up" if pct >= PCT_MIN else "down" if pct <= -PCT_MIN else "flat"
        return ok, kind, dict(pct=abs(pct) if kind != "flat" else pct)
    if expected == "unstable":
        x = float(win.diff().std() / (base.diff().std() or 1e-9))
        return x >= UNSTABLE_X, "unstable" if x >= UNSTABLE_X else "steady", dict(x=x)
    if expected == "steady":
        pct = (float(win.mean()) - mu) / abs(mu) * 100 if mu else 0.0
        return abs(pct) < PCT_MIN * 4, "steady_pct", dict(pct=pct)
    z = (win - mu) / (float(base.std()) or 1e-9)
    n = int((z > SPIKE_Z).sum())
    return n > 0, "spike" if n else "nospike", dict(n=n)


def compare(tel, aid, sig, t):
    """(direction, pct) of the last 48 h against the machine's own 30-day normal; the one comparison the app quotes for a signal."""
    base, win = _series(tel, aid, sig, t)
    _, kind, nums = _observe(base, win, "up")
    return (kind, abs(nums["pct"])) if kind in ("up", "down", "flat") else (None, None)


def fingerprint(tel, aid, fault_class, t):
    out = []
    for sig, expected in text.FAULTS[fault_class]["signs"][:4]:
        base, win = _series(tel, aid, sig, t)
        ok, kind, nums = _observe(base, win, expected)
        en, ms = text.STEADY_OBS if kind == "steady_pct" else text.OBSERVED[kind]
        en, ms = en.format(**nums), ms.format(**nums)
        if not ok and (kind in ("flat", "steady", "nospike") or kind == expected):   # fault has not progressed that far yet
            en, ms = text.NOT_YET[0] + en[0].lower() + en[1:], text.NOT_YET[1] + ms[0].lower() + ms[1:]
        out.append(playbook.check(sig, expected, en, ms, bool(ok)))
    return out
