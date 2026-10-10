"""Fault fingerprint: does each signature signal's last 5 days move the way the fault guide expects?"""
import numpy as np
import pandas as pd

from backend.engine import playbook, text

WIN_H, BASE_D = 120, 30
PCT_MIN, Z_MIN, UNSTABLE_X, SPIKE_Z = 2.0, 1.5, 1.5, 4.0


def _clean(tel, aid, t0, t1):
    g = tel[(tel.asset_id == aid) & (tel.t > t0) & (tel.t <= t1)]
    return g[g.throughput_tph > 3] if aid.startswith("press") else g


def _series(tel, aid, sig, t):
    lo = t - pd.Timedelta(hours=WIN_H)
    base = _clean(tel, aid, lo - pd.Timedelta(days=BASE_D), lo).set_index("t")[sig].dropna()
    win = _clean(tel, aid, lo, t).set_index("t")[sig].dropna()
    return base, win


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
    z = (win - mu) / (float(base.std()) or 1e-9)
    n = int((z > SPIKE_Z).sum())
    return n > 0, "spike" if n else "nospike", dict(n=n)


def fingerprint(tel, aid, fault_class, t):
    out = []
    for sig, expected in text.FAULTS[fault_class]["signs"][:4]:
        base, win = _series(tel, aid, sig, t)
        ok, kind, nums = _observe(base, win, expected)
        en, ms = text.OBSERVED[kind]
        out.append(playbook.check(sig, expected, en.format(**nums), ms.format(**nums), bool(ok)))
    return out
