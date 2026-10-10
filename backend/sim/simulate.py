"""Physics-based mill simulator: 10 mills x calendar 2025, hourly, 4 presses + 1 boiler.

Hidden state per component = age vs a random life. Failure when age >= life (then a fresh component).
Outputs Azure PdM-style tables (telemetry, errors, maintenance, failures) plus hidden lives for backtests.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from backend.params import load, val

DATA = Path(__file__).resolve().parents[1] / "data" / "sim"
START = "2025-01-01"
H = 8760
PRESS_COMPS = ["worm_wear", "bearing", "gearbox_shaft", "hydraulic_cone", "electrical", "unknown"]
BOILER_COMPS = ["boiler_steam", "boiler_water"]
PRECURSOR_H = {"electrical": 24, "unknown": 36, "boiler_steam": 36, "boiler_water": 72}   # remaining-time shaped
SHAPE_POW = {"worm_wear": 2, "bearing": 3, "gearbox_shaft": 2, "hydraulic_cone": 2}        # age/life shaped
UNK_SIGNALS = ["motor_current", "cone_pressure", "gearbox_oil_temp", "vib_rms"]


def draw_life(rng, comp, p):
    lo, hi = val(p, "simulator", "worm_life_h_min"), val(p, "simulator", "worm_life_h_max")
    return {"worm_wear": lambda: rng.uniform(lo, hi),
            "bearing": lambda: rng.uniform(7000, 16000),
            "gearbox_shaft": lambda: rng.uniform(12000, 30000),
            "hydraulic_cone": lambda: rng.uniform(5000, 14000),
            "electrical": lambda: rng.exponential(9000) + 200,
            "unknown": lambda: rng.exponential(20000) + 200,
            "boiler_steam": lambda: rng.exponential(7000) + 200,
            "boiler_water": lambda: rng.exponential(8000) + 200}[comp]()


def new_component(rng, comp, p):
    return draw_life(rng, comp, p), rng.uniform(0.4, 1.2), int(rng.integers(len(UNK_SIGNALS)))


def effect(comp, age, life):
    """Wear effect 0..1 (grows to 1 at failure)."""
    if comp in PRECURSOR_H:
        return float(np.clip(1 - (life - age) / PRECURSOR_H[comp], 0, 1))
    return float(min(age / life, 1.0) ** SHAPE_POW[comp])


def run_dynamics(rng, p, mill):
    """Hour loop: throughput, wear, failures. Returns arrays and records."""
    crop = np.array(val(p, "simulator", "crop_index_2025"))
    t = pd.date_range(START, periods=H, freq="h")
    month_idx = t.month.values - 1
    c_idx = crop[month_idx]
    day_len = np.clip(np.round(14 + 8 * c_idx / crop.max()), 12, 22)
    base_run = ((t.hour.values - 6) % 24) < day_len
    planned = (t.dayofweek.values == 6) & (t.hour.values >= 6) & (t.hour.values < 12)
    base_run &= ~planned
    shift_f = np.where((t.hour.values >= 19) | (t.hour.values < 7), 0.95, 1.0)
    tph_nom = 15 * (0.85 + 0.15 * c_idx / crop.max()) * shift_f

    comps = {f"press_{i}": PRESS_COMPS for i in range(1, 5)} | {"boiler_1": BOILER_COMPS}
    state = {}
    lives_log = []
    for a, cl in comps.items():
        for c in cl:
            life, amp, unk = new_component(rng, c, p)
            age0 = rng.uniform(0, 0.8) * life
            state[(a, c)] = dict(age=age0, life=life, amp=amp, unk=unk, k=0)
            lives_log.append(dict(mill_id=mill, asset_id=a, comp=c, k=0, life=life, amp=amp, unk=unk, age0=age0))
    P = 4
    tph = np.zeros((H, P)); inc = np.zeros((H, P))
    eff = {k: np.zeros(H, np.float32) for k in state}
    amp_t = {k: np.zeros(H, np.float32) for k in state}
    unk_t = {k: np.zeros(H, np.int8) for k in state}
    press_down = np.zeros(P, int); mill_down = 0
    boiler_on = np.zeros(H, bool)
    failures = []
    down_h = {"press": val(p, "economics", "unplanned_press_stop_h"), "boiler": val(p, "economics", "unplanned_boiler_stop_h")}
    stress = rng.gamma(4, 0.25, size=(H, P))
    noise_t = rng.normal(0, 0.03, size=(H, P))

    for h in range(H):
        mill_up = base_run[h] and h >= mill_down
        boiler_on[h] = mill_up
        for pi in range(P):
            a = f"press_{pi + 1}"
            running = mill_up and h >= press_down[pi]
            if running:
                tph[h, pi] = tph_nom[h] * (1 + noise_t[h, pi])
                inc[h, pi] = tph[h, pi] / 15 * stress[h, pi]
            for c in PRESS_COMPS:
                s = state[(a, c)]
                if running:
                    s["age"] += inc[h, pi]
                eff[(a, c)][h] = effect(c, s["age"], s["life"])
                amp_t[(a, c)][h] = s["amp"]; unk_t[(a, c)][h] = s["unk"]
                if s["age"] >= s["life"]:
                    failures.append((h, a, c))
                    press_down[pi] = h + 1 + int(down_h["press"])
                    s["life"], s["amp"], s["unk"] = new_component(rng, c, p)
                    s["age"] = 0.0; s["k"] += 1
                    lives_log.append(dict(mill_id=mill, asset_id=a, comp=c, k=s["k"], life=s["life"], amp=s["amp"], unk=s["unk"], age0=0.0))
                    running = False
        for c in BOILER_COMPS:
            s = state[("boiler_1", c)]
            if mill_up:
                s["age"] += 1
            eff[("boiler_1", c)][h] = effect(c, s["age"], s["life"])
            amp_t[("boiler_1", c)][h] = s["amp"]
            if s["age"] >= s["life"]:
                failures.append((h, "boiler_1", c))
                mill_down = h + 1 + int(down_h["boiler"])
                s["life"], s["amp"], s["unk"] = new_component(rng, c, p)
                s["age"] = 0.0; s["k"] += 1
                lives_log.append(dict(mill_id=mill, asset_id="boiler_1", comp=c, k=s["k"], life=s["life"], amp=s["amp"], unk=0, age0=0.0))
    return dict(t=t, tph=tph, inc=inc, eff=eff, amp=amp_t, unk=unk_t, boiler_on=boiler_on, planned=planned,
                failures=failures, lives=lives_log)


def drift(rng, n, scale):
    """Slow random drift (fraction), smooth over the year."""
    x = np.cumsum(rng.normal(0, 1, n)); x -= np.linspace(x[0], x[-1], n) * rng.uniform(0, 1)
    return scale * x / (np.abs(x).max() + 1e-9)


def build_telemetry(rng, p, mill, d, noise_mult, offset):
    t = d["t"]; frames = []
    hr = t.hour.values; doy = t.dayofyear.values
    ambient = 3 * np.sin(2 * np.pi * (doy / 365 - 0.3))
    miss = val(p, "simulator", "missing_reading_rate")
    for pi in range(4):
        a = f"press_{pi + 1}"
        tph = d["tph"][:, pi]; run = tph > 0.5; load = tph / 15
        e = {c: d["eff"][(a, c)].astype(float) * d["amp"][(a, c)] for c in PRESS_COMPS}
        nz = lambda s: rng.normal(0, s * noise_mult, H)
        dr_i = 1 + drift(rng, H, 0.04) + offset
        unk = d["unk"][(a, "unknown")]
        u = lambda sig: np.where(unk == UNK_SIGNALS.index(sig), e["unknown"], 0.0)
        elec = e["electrical"]
        cur = (10 + 3.55 * tph * (1 + 0.12 * e["worm_wear"]) * dr_i * (1 + nz(0.02) + nz(0.05) * elec * 4)
               * (1 + 0.08 * u("motor_current")))
        spikes = (rng.random(H) < 0.02 * elec) * rng.uniform(0.1, 0.3, H)
        cur = cur * (1 + spikes)
        cone = (45 * np.maximum(load, 0.3) ** 0.3 + 6 * e["hydraulic_cone"]
                + rng.normal(0, 1, H) * noise_mult * (1.2 + 4 * e["hydraulic_cone"]) + 4 * u("cone_pressure"))
        oil = 58 + 12 * load + ambient + 12 * e["gearbox_shaft"] + nz(0.8) + 5 * u("gearbox_oil_temp") + drift(rng, H, 2)
        rms = 2.0 * (1 + 0.1 * load) * (1 + 0.7 * np.clip((e["bearing"] - 0.75) / 0.25, 0, None) ** 1.5
                                       + 0.25 * u("vib_rms")) * (1 + nz(0.04))
        kurt = 3.0 + 4.5 * e["bearing"] + nz(0.2) + 0.8 * u("vib_rms")
        daily = pd.Series(2.8 * (1 + 0.5 * e["worm_wear"]) + nz(0.15)).where(run)
        lab = np.full(H, np.nan); idx = np.where(hr == 8)[0]
        lab[idx] = daily.rolling(24, min_periods=1).mean().values[idx] + rng.normal(0, 0.12 * noise_mult, len(idx))
        df = pd.DataFrame(dict(mill_id=mill, asset_id=a, t=t, throughput_tph=tph, motor_current=cur, cone_pressure=cone,
                               gearbox_oil_temp=oil, vib_rms=rms, vib_kurtosis=kurt, fibre_oil_loss=lab))
        df["current_per_tonne"] = np.where(tph > 3, df.motor_current / np.maximum(tph, 1e-9), np.nan)
        off = ~run
        for c in ["motor_current", "cone_pressure", "vib_rms", "vib_kurtosis"]:
            df.loc[off, c] = np.nan if c in ("vib_kurtosis",) else df.loc[off, c] * 0.0
        df.loc[off, "gearbox_oil_temp"] = df.loc[off, "gearbox_oil_temp"] - 15
        frames.append(df)
    on = d["boiler_on"]; tot = d["tph"].sum(axis=1)
    es, ew = d["eff"][("boiler_1", "boiler_steam")] * d["amp"][("boiler_1", "boiler_steam")], \
        d["eff"][("boiler_1", "boiler_water")] * d["amp"][("boiler_1", "boiler_water")]
    nz = lambda s: rng.normal(0, s * noise_mult, H)
    bo = pd.DataFrame(dict(mill_id=mill, asset_id="boiler_1", t=t,
                           steam_temp=538 - 16 * es + nz(1.5) + drift(rng, H, 2) + offset * 20,
                           steam_pressure=21 + 0.01 * (tot - 40) + nz(0.15 + 0.5 * es),
                           feedwater_flow=0.6 * tot * (1 - 0.1 * es) + nz(0.5),
                           feedwater_cond=20 + 25 * ew + nz(1.5) + drift(rng, H, 2)))
    bo.loc[~on, ["steam_temp", "steam_pressure", "feedwater_flow"]] *= 0.9
    frames.append(bo)
    tel = pd.concat(frames, ignore_index=True)
    sigs = [c for c in tel.columns if c not in ("mill_id", "asset_id", "t")]
    mask = rng.random((len(tel), len(sigs))) < miss
    tel[sigs] = tel[sigs].mask(mask)
    for a in tel.asset_id.unique():                       # sensor dropout gaps
        for _ in range(rng.poisson(3)):
            s0 = rng.integers(0, H - 24); ln = rng.integers(4, 24)
            tel.loc[(tel.asset_id == a) & (tel.t >= t[s0]) & (tel.t < t[s0 + ln]), sigs] = np.nan
    return tel


def build_errors(tel, mill):
    rules = [("E_CONE_P_HIGH", "cone_pressure", lambda x: x > 57), ("E_OIL_TEMP_HIGH", "gearbox_oil_temp", lambda x: x > 80),
             ("E_VIB_HIGH", "vib_rms", lambda x: x > 3.2), ("E_FIBRE_LOSS", "fibre_oil_loss", lambda x: x > 4.0),
             ("E_STEAM_TEMP", "steam_temp", lambda x: (x < 530) | (x > 545))]
    rows = []
    for code, sig, f in rules:
        sub = tel[tel[sig].notna()]
        hit = sub[f(sub[sig])]
        rows.append(pd.DataFrame(dict(mill_id=mill, asset_id=hit.asset_id, t=hit.t, error_code=code)))
    return pd.concat(rows, ignore_index=True)


def build_failures(rng, p, mill, d):
    t = d["t"]
    rows = []
    for h, a, c in d["failures"]:
        at = "boiler" if a == "boiler_1" else "press"
        dt = val(p, "economics", "unplanned_boiler_stop_h" if at == "boiler" else "unplanned_press_stop_h")
        rows.append(dict(mill_id=mill, asset_id=a, t=t[h], fault_class=c, downtime_h=dt))
    fail = pd.DataFrame(rows, columns=["mill_id", "asset_id", "t", "fault_class", "downtime_h"])
    fail.insert(0, "failure_id", [f"m{mill}_{i}" for i in range(len(fail))])
    # messy work orders: ~10% wrong class or late timestamp
    mess = val(p, "simulator", "messy_work_order_share")
    wo = fail.copy()
    wo["parts_cost_rm"] = [round(p["repair_cost_rm"][c]["value"] * val(p, "economics", "unplanned_repair_multiplier")
                                 * rng.uniform(0.8, 1.3)) for c in wo.fault_class]
    wo["kind"] = "unplanned"
    bad = rng.random(len(wo)) < mess
    wrong = bad & (rng.random(len(wo)) < 0.5)
    late = bad & ~wrong
    for i in np.where(wrong)[0]:
        pool = BOILER_COMPS if wo.asset_id.iloc[i] == "boiler_1" else PRESS_COMPS
        wo.iloc[i, wo.columns.get_loc("fault_class")] = rng.choice([x for x in pool if x != wo.fault_class.iloc[i]])
    wo.loc[late, "t"] = wo.loc[late, "t"] + pd.to_timedelta(rng.integers(6, 72, late.sum()), unit="h")
    return fail, wo


def simulate_all(seed=2025):
    p = load(); DATA.mkdir(parents=True, exist_ok=True)
    tels, errs, fails, wos, lives, hidden = [], [], [], [], [], []
    for mill in range(1, val(p, "simulator", "n_mills") + 1):
        lo, hi = val(p, "simulator", "target_stops_per_mill_year")
        for attempt in range(50):   # scenario design: stop counts inside target; demo mill 10 needs a boiler event
            rng = np.random.default_rng(seed + mill + 1000 * attempt)
            noise_mult = rng.uniform(0.85, 1.25) * (1.25 if mill == 10 else 1.0)   # mill 10 deliberately noisier
            offset = rng.uniform(-0.03, 0.03) + (0.04 if mill == 10 else 0.0)       # and miscalibrated
            d = run_dynamics(rng, p, mill)
            n_press = sum(a != "boiler_1" for _, a, _ in d["failures"])
            n_boiler = len(d["failures"]) - n_press
            if lo <= n_press <= hi and (mill != 10 or n_boiler >= 1):
                break
        tel = build_telemetry(rng, p, mill, d, noise_mult, offset)
        f, wo = build_failures(rng, p, mill, d)
        tels.append(tel); errs.append(build_errors(tel, mill)); fails.append(f); wos.append(wo)
        lives.append(pd.DataFrame(d["lives"]))
        for pi in range(4):
            hidden.append(pd.DataFrame(dict(mill_id=mill, asset_id=f"press_{pi + 1}", t=d["t"], inc=d["inc"][:, pi])))
    out = dict(telemetry=pd.concat(tels), errors=pd.concat(errs), failures=pd.concat(fails),
               maintenance=pd.concat(wos), lives=pd.concat(lives), hidden=pd.concat(hidden))
    for k, v in out.items():
        v.reset_index(drop=True).to_parquet(DATA / f"{k}.parquet")
    return out


def summary(out):
    f = out["failures"]; f = f.assign(kind=np.where(f.asset_id == "boiler_1", "boiler", "press"))
    pr = f[f.kind == "press"]
    print("Failures per mill-year (press stops):", pr.groupby("mill_id").size().to_dict())
    print(pr.groupby("fault_class").size().div(pr.mill_id.nunique()).round(1).to_string())
    print("Boiler failures per mill-year:", f[f.kind == "boiler"].groupby("mill_id").size().to_dict())
    print("Work orders with wrong class: ",
          f"{(out['maintenance'].fault_class.values != f.fault_class.values).mean():.1%}")
    print("Telemetry rows:", len(out["telemetry"]))


if __name__ == "__main__":
    summary(simulate_all())
