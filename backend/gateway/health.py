"""Sensor-health checks on incoming readings: out of range, stuck, spike, missing. A bad reading is a SENSOR problem,
never a machine alert, and is masked before the models score it."""
import numpy as np
import pandas as pd

from backend.engine import text

PRESS_SIGNALS = ["motor_current", "throughput_tph", "vib_rms", "vib_kurtosis", "gearbox_oil_temp", "cone_pressure", "fibre_oil_loss"]
BOILER_SIGNALS = ["steam_temp", "steam_pressure", "feedwater_flow", "feedwater_cond"]
RANGE = {"motor_current": (0, 400), "throughput_tph": (0, 40), "vib_rms": (0, 25), "vib_kurtosis": (0, 40),
         "gearbox_oil_temp": (-10, 150), "cone_pressure": (0, 120), "fibre_oil_loss": (0, 20),
         "steam_temp": (300, 650), "steam_pressure": (0, 40), "feedwater_flow": (-5, 120), "feedwater_cond": (0, 500)}
SENSOR_OF = {"motor_current": "current", "vib_rms": "vibration", "vib_kurtosis": "vibration", "gearbox_oil_temp": "oil_temp",
             "cone_pressure": "cone_pressure", "steam_temp": "steam_temp", "steam_pressure": "steam_pressure",
             "feedwater_flow": "feedwater_flow", "feedwater_cond": "feedwater_cond", "fibre_oil_loss": "fibre", "throughput_tph": "throughput"}
CHECKED = [s for s in SENSOR_OF if s not in ("fibre_oil_loss", "throughput_tph")]   # fibre is a daily lab value; throughput is the load, not a sensor we judge
STUCK_H, SPIKE_SD, MISSING_H, HISTORY_H, MIN_HISTORY = 6, 6.0, 3, 72, 24


def running(asset_id, readings):
    if asset_id.startswith("boiler"):
        flow = _num(readings.get("feedwater_flow"))   # the boiler idles with the mill: no flow, nothing to judge
        return flow is None or flow > 5
    tph = _num(readings.get("throughput_tph"))
    if tph is None:   # load unreadable: a dead motor current says the press is off
        mc = _num(readings.get("motor_current"))
        if mc is None:   # no load, no current: dead-zero vibration or cone pressure says the press is off
            return not any(_num(readings.get(k)) == 0.0 for k in ("vib_rms", "cone_pressure"))
        return mc > 5
    return tph > 0.5


def _num(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)


def check(asset_id, readings, history):
    """readings: the new hourly reading dict. history: previous hourly readings of this asset, oldest first (dicts, at most 72).
    -> list of (signal, kind)."""
    out = []
    run = running(asset_id, readings)
    for sig in CHECKED:
        if sig not in RANGE or (sig in PRESS_SIGNALS) == asset_id.startswith("boiler"):
            continue
        v = _num(readings.get(sig))
        lo, hi = RANGE[sig]
        if v is None:
            if run:
                past = [h for h in history if running(asset_id, h)][-(MISSING_H - 1):]
                if len(past) == MISSING_H - 1 and all(_num(h.get(sig)) is None for h in past):
                    out.append((sig, "missing"))
            continue
        if not lo <= v <= hi:
            out.append((sig, "out_of_range")); continue
        if not run:
            continue
        past = [_num(h.get(sig)) for h in history if running(asset_id, h)]
        past = [x for x in past if x is not None]
        if len(past) >= STUCK_H - 1 and all(x == v for x in past[-(STUCK_H - 1):]):
            out.append((sig, "stuck")); continue
        base = past[-HISTORY_H:]
        if len(base) >= MIN_HISTORY:
            med = float(np.median(base))
            sd = max(1.4826 * float(np.median(np.abs(np.asarray(base) - med))), 0.02 * abs(med), 1e-6)
            margin = max(SPIKE_SD * sd, 0.5 * abs(med))   # a step after a repair is not a spike: must also clear the 72 h range
            recent = float(np.median(base[-3:]))   # a wear ramp moves gradually; a sensor spike jumps away from the last few readings
            jump = abs(v - recent) > margin
            up = jump and v > max(base) + margin and v - med > SPIKE_SD * sd
            down = jump and v < min(base) - margin and med - v > SPIKE_SD * sd and v < 0.2 * abs(med)   # a drop to a fraction of normal; a repaired part reads lower but not that low
            if up or down:
                out.append((sig, "spike"))
    return out


def alert(asset_id, signal, kind, t, first_t=None):
    name = text.name_ms  # Malay asset names come from text.py
    asset_en = asset_id.replace("_", " ").title().replace(" 1", " 1")
    asset_en = {"press_1": "Press 1", "press_2": "Press 2", "press_3": "Press 3", "press_4": "Press 4", "boiler_1": "Boiler 1"}[asset_id]
    sen = text.SENSOR_NAME[SENSOR_OF[signal]]
    msg = text.SENSOR_MSG[kind]
    return dict(asset_id=asset_id, signal=signal, kind=kind, t=t, first_t=first_t or t,
                message_en=msg[0].format(asset=asset_en, sensor=sen[0]), message_ms=msg[1].format(asset=name(asset_en), sensor=sen[1]))


def scan(tel):
    """Offline check of a telemetry table (mill_id, asset_id, t, signals). -> (masked copy, issues DataFrame asset_id/signal/kind/t).
    Flagged readings become NaN, which is how the models already treat a missing reading."""
    tel = tel.copy()
    rows = []
    for aid, g in tel.groupby("asset_id"):
        g = g.sort_values("t")
        sigs = [s for s in (BOILER_SIGNALS if aid.startswith("boiler") else PRESS_SIGNALS) if s in g.columns]
        vals = g[sigs].to_dict("records")
        for i, (idx, t) in enumerate(zip(g.index, g.t)):
            for sig, kind in check(aid, vals[i], vals[max(0, i - HISTORY_H):i]):
                rows.append((aid, sig, kind, t))
                if kind != "missing":
                    tel.loc[idx, [s for s in sigs if SENSOR_OF.get(s) == SENSOR_OF[sig]]] = np.nan
    return tel, pd.DataFrame(rows, columns=["asset_id", "signal", "kind", "t"])
