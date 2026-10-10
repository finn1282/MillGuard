"""Read-only service over pipeline artifacts. Stateless: every call takes `at`."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from backend.engine import backtest, cost, decide, fingerprint, playbook, text
from backend.params import load, val

ART = Path(__file__).resolve().parents[1] / "artifacts"
T0 = pd.Timestamp("2025-01-01")
ASSETS = [("press_1", "Press 1", "press", 1), ("press_2", "Press 2", "press", 2),
          ("press_3", "Press 3", "press", 3), ("press_4", "Press 4", "press", 4),
          ("boiler_1", "Boiler 1", "boiler", 0)]
NAME = {a: n for a, n, _, _ in ASSETS}
PRESS_SERIES = ["current_per_tonne", "vib_kurtosis", "gearbox_oil_temp", "cone_pressure", "vib_rms",
                "motor_current", "fibre_oil_loss"]
BOILER_SERIES = ["steam_temp", "steam_pressure", "feedwater_flow", "feedwater_cond"]
SERIES_UNIT = {"current_per_tonne": "A/t", "vib_kurtosis": "", "gearbox_oil_temp": "°C", "cone_pressure": "bar",
               "vib_rms": "mm/s", "motor_current": "A", "fibre_oil_loss": "%", "steam_temp": "°C",
               "steam_pressure": "bar", "feedwater_flow": "t/h", "feedwater_cond": "µS/cm"}
DAY_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_MS = ["Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"]
MYT = "+08:00"


def iso(t) -> str:
    return pd.Timestamp(t).strftime("%Y-%m-%dT%H:%M:%S") + MYT


def parse(at, default):
    if not at:
        return default
    return pd.Timestamp(at).tz_localize(None) if pd.Timestamp(at).tzinfo is None else \
        pd.Timestamp(at).tz_convert("Asia/Kuala_Lumpur").tz_localize(None)


def shift_of(t) -> str:
    return "night" if t.hour >= 19 or t.hour < 7 else "day"


class Service:
    def __init__(self):
        self.p = load()
        self.fit = json.loads((ART / "policy_fit.json").read_text())
        self.pred = pd.read_parquet(ART / "mill10_predictions.parquet")
        self.fails = pd.read_parquet(ART / "mill10_failures.parquet")
        self.tel = pd.read_parquet(ART / "mill10_telemetry.parquet")
        self.lives = pd.read_parquet(ART / "mill10_lives.parquet")
        self.hidden = pd.read_parquet(ART / "mill10_hidden.parquet")
        self.actions = json.loads((ART / "actions.json").read_text())
        for a in self.actions:
            for k in ("t_open", "t_close", "t_candidate"):
                a[k] = pd.Timestamp(a[k]).tz_localize(None)
        self.times = pd.DatetimeIndex(sorted(self.pred.t.unique()))
        self.rm_h = cost.rm_per_mill_hour(self.p)
        self.thr = {t: decide.risk_threshold(self.p, t, self.fit["k"][t]) for t in ("press", "boiler")}
        self._trig = self._trigger_arrays()
        self._bt_cache = {}

    # ---- helpers
    def _trigger_arrays(self):
        min_lead = val(self.p, "alerting", "min_lead_h")
        hts = np.array([decide.hours_to_stop(t, min_lead) for t in self.times])
        out = {}
        for a, _, atype, _ in ASSETS:
            g = self.pred[self.pred.asset_id == a].set_index("t").reindex(self.times)
            p24, p72, p168 = g.p24.fillna(0).values, g.p72.fillna(0).values, g.p168.fillna(0).values
            trig = p72
            if self.fit["trigger"][atype] == "pstop":
                trig = np.array([decide.p_before(*x, h) for x, h in zip(zip(p24, p72, p168), hts)])
            out[a] = dict(trig=trig, p72=p72, p24=p24, p168=p168,
                          cp=g[[c for c in g.columns if c.startswith("cp_")]].fillna(0))
        return out

    def clamp_time(self, at):
        t = parse(at, self.times[-1])
        return min(max(t.floor("h"), self.times[0]), self.times[-1])

    def idx(self, t):
        return int((t - self.times[0]) / pd.Timedelta(hours=1))

    def active(self, t):
        return [a for a in self.actions if a["t_open"] <= t < a["t_close"]]

    def status(self, t):
        """Per asset: (status, risk_pct, suppressed_flag)."""
        h = self.idx(t)
        act = {a["asset_id"] for a in self.active(t)}
        res = {}
        for aid, _, atype, _ in ASSETS:
            tr = self._trig[aid]
            thr = self.thr[atype]
            recent = tr["trig"][max(0, h - 23): h + 1]
            s = "act" if aid in act else ("watch" if tr["trig"][h] >= 0.5 * thr else "ok")
            sup = aid not in act and bool((recent > thr).any())
            res[aid] = (s, float(tr["trig"][h]) * 100, sup)
        return res

    # ---- endpoints
    def meta(self):
        return dict(mill=dict(name="Demo mill (mill 10, unseen in training)", throughput_tph=val(self.p, "economics", "throughput_tph"),
                              presses=4, oer=val(self.p, "economics", "oer"),
                              cpo_price_rm=val(self.p, "economics", "cpo_price_rm_per_t")),
                    replay=dict(start=iso(self.times[0]), end=iso(self.times[-1]), step_h=1),
                    rm_per_mill_hour=round(self.rm_h))

    def line(self, at):
        t = self.clamp_time(at)
        st = self.status(t)
        return dict(at=iso(t), assets=[self._line_asset(a, n, ty, pos, st[a], t) for a, n, ty, pos in ASSETS])

    def _line_asset(self, a, n, ty, pos, st, t):
        cur = next((x for x in self.active(t) if x["asset_id"] == a), None)
        fc = cur["fault_class"] if cur else self._top_class(a, t) if st[0] == "watch" else None
        risk = self._window(cur, t)[1] * 100 if cur else st[1]
        summ = text.SUMMARY[fc] if fc else text.SUMMARY_OK
        return dict(id=a, name=n, type=ty, stage=ty, position=pos, status=st[0], risk_pct=round(risk, 1),
                    summary_en=summ[0], summary_ms=summ[1])

    def _top_class(self, aid, t):
        return self._class_probs(aid, t)[0][0]

    def _class_probs(self, aid, t):
        row = self._trig[aid]["cp"].iloc[self.idx(t)]
        row = row[row > 0]
        if row.empty:
            return [("unknown", 1.0)]
        row = row / row.sum()
        return [(c[3:], float(v)) for c, v in row.sort_values(ascending=False).items()]

    def _window(self, a, t):
        """(horizon_h, P(fail before the action deadline)) at replay time t."""
        h = self.idx(t)
        tr = self._trig[a["asset_id"]]
        if a["recommendation"] == "fix_now":   # waiting means waiting for the next planned stop
            hrs = min(168, decide.hours_to_stop(t, val(self.p, "alerting", "min_lead_h")))
        else:
            hrs = max(1, int(np.ceil((pd.Timestamp(a["deadline"]).tz_localize(None) - t) / pd.Timedelta(hours=1))))
        return hrs, decide.p_before(tr["p24"][h], tr["p72"][h], tr["p168"][h], hrs)

    def _action(self, a, rank, top_saved, has_whole, t=None):
        why = (text.WHY_WHOLE_EN, text.WHY_WHOLE_MS) if a["criticality"] == "whole_mill" else \
            (text.WHY_PARTIAL_EN, text.WHY_PARTIAL_MS) if has_whole else \
            (text.WHY_TOP_EN, text.WHY_TOP_MS) if rank == 0 else (text.WHY_LOWER_EN, text.WHY_LOWER_MS)
        out = {k: v for k, v in a.items() if k not in ("t_open", "t_close", "t_candidate", "internal")}
        out.update(why_rank_en=why[0], why_rank_ms=why[1])
        return self._money(out, a, t) if t is not None else out

    def _money(self, out, a, t):
        """rm_at_risk = expected loss if you wait = P(fail before deadline) x full breakdown cost."""
        hrs, risk = self._window(a, t)
        pct = round(risk * 100)
        full = cost.breakdown_cost(self.p, a["fault_class"])
        out.update(horizon_h=hrs, risk_pct=pct, rm_at_risk=round(pct / 100 * full))
        out["rm_saved_if_acted"] = max(0, out["rm_at_risk"] - out["rm_cost_to_act"])
        return out

    def _live(self, t):
        """Active alerts with money recomputed for replay time t, biggest saving first."""
        rows = [self._money(dict(a), a, t) for a in self.active(t)]
        return sorted(zip(rows, self.active(t)), key=lambda x: -x[0]["rm_saved_if_acted"])

    def brief(self, at, budget=5):
        t = self.clamp_time(at)
        act = [a for _, a in self._live(t)]
        has_whole = any(a["criticality"] == "whole_mill" for a in act)
        shown = [self._action(a, i, None, has_whole, t) for i, a in enumerate(act[:budget])]
        st = self.status(t)
        watching = sum(1 for aid, (s, _, _) in st.items() if s == "watch")
        suppressed = sum(1 for aid, (s, _, sup) in st.items() if sup) + max(0, len(act) - budget)
        return dict(at=iso(t), shift=shift_of(t), actions=shown, watching_count=watching, suppressed_count=suppressed)

    def asset(self, aid, at, window_h=168):
        t = self.clamp_time(at)
        names = {a: (n, ty, pos) for a, n, ty, pos in ASSETS}
        if aid not in names:
            return None
        n, ty, pos = names[aid]
        st = self.status(t)[aid]
        g = self.tel[(self.tel.asset_id == aid) & (self.tel.t > t - pd.Timedelta(hours=window_h)) & (self.tel.t <= t)]
        sigs = PRESS_SERIES if ty == "press" else BOILER_SERIES
        series = []
        for s in sigs:
            d = g[["t", s]].dropna()
            if d.empty:
                continue
            en, ms = text.SIGNAL_LABEL.get(s, (s, s))
            series.append(dict(signal=s, label_en=en, label_ms=ms, unit=SERIES_UNIT[s],
                               points=[[iso(a), round(float(b), 3)] for a, b in zip(d.t, d[s])]))
        lo = t - pd.Timedelta(hours=window_h)
        wins = [dict(start=iso(max(a["t_open"], lo)), end=iso(min(a["t_close"], t))) for a in self.actions
                if a["asset_id"] == aid and a["t_close"] > lo and a["t_open"] <= t]
        fl = self.fails[(self.fails.asset_id == aid) & (self.fails.t > lo) & (self.fails.t <= t)]
        cur = next((a for a in self.active(t) if a["asset_id"] == aid), None)
        action = self._action(cur, 0, None, cur["criticality"] == "whole_mill", t) if cur else None
        la = self._line_asset(aid, n, ty, pos, st, t)
        diag, fix = self._diagnosis(aid, cur, st[0], t, action)
        return dict(asset=la, status=la["status"], risk_pct=la["risk_pct"], series=series, alert_windows=wins,
                    failures=[dict(t=iso(r.t), fault_class=r.fault_class) for r in fl.itertuples()], action=action,
                    diagnosis=diag, fix=fix, history=self._history(aid, t))

    def _diagnosis(self, aid, cur, status, t, action):
        if status == "ok":
            return None, None
        probs = self._class_probs(aid, cur["t_open"] if cur else t)
        fc = cur["fault_class"] if cur else probs[0][0]
        rest = [(c, v) for c, v in probs if c != fc]
        top = dict(probs).get(fc, 0.0)
        conf = round(top * 100)
        alts = [(c, round(v * 100)) for c, v in rest[:2]]
        diag = playbook.diagnosis(fc, conf, alts, fingerprint.fingerprint(self.tel, aid, fc, t)).model_dump(mode="json")
        fix = None
        if cur:
            best = action["deadline"] if action["recommendation"] == "schedule_next_stop" else iso(t)
            fix = playbook.fix_plan(fc, best).model_dump(mode="json")
        return diag, fix

    def _history(self, aid, t):
        lo = t - pd.Timedelta(days=365)
        fl = self.fails[(self.fails.asset_id == aid) & (self.fails.t > lo) & (self.fails.t <= t)]
        out = []
        for r in fl.sort_values("t", ascending=False).itertuples():
            warned = any(a["asset_id"] == aid and a["t_open"] <= r.t and (r.t - a["t_open"]) <= pd.Timedelta(hours=168)
                         for a in self.actions)
            f_en, f_ms = text.FAULT_LABEL[r.fault_class]
            w = text.HISTORY_WHAT[warned]
            out.append(dict(t=iso(r.t), fault_class=r.fault_class, what_en=w[0].format(fault=f_en.capitalize()),
                            what_ms=w[1].format(fault=f_ms.capitalize()), downtime_h=float(r.downtime_h), was_predicted=warned))
        return out

    def backtest(self, cpo_price=None, miss_cost_mult=1.0, alert_budget=5, compare="run_to_failure"):
        cpo = min(max(cpo_price if cpo_price else val(self.p, "economics", "cpo_price_rm_per_t"), 3800), 5000)
        miss = min(max(miss_cost_mult, 0.5), 3)
        bud = int(min(max(alert_budget, 1), 10))
        key = (round(cpo, 2), round(miss, 3), bud)
        if key not in self._bt_cache:
            ep, events, thr, = None, None, None
            ep, events, thr = backtest.run_all_policies(self.p, 10, self.pred, self.fails, self.lives, self.hidden,
                                                        self.fit["k"], self.fit["fixed_interval_frac"], bud, cpo, miss,
                                                        self.fit["trigger"], self.fit["schedule_plus"])
            pols = [backtest.summarize(self.p, events, k) for k in backtest.POLICIES]
            tl = backtest.timeline(events)
            evs = sorted(({"t": iso(e["t"]), "policy": e["policy"], "type": e["type"], "asset_id": e["asset_id"]}
                          for e in events), key=lambda e: e["t"])
            self._bt_cache[key] = dict(threshold=round(float(thr["press"]), 3), policies=pols,
                                       timeline=[dict(t=iso(x["t"]), cost=x["cost"]) for x in tl], events=evs)
        return self._bt_cache[key]

    def assumptions(self):
        out = []
        for sec, items in self.p.items():
            for k, e in items.items():
                v = e["value"]
                out.append(dict(key=f"{sec}.{k}", label=k.replace("_", " ").capitalize(),
                                value=v if isinstance(v, (int, float)) else ", ".join(map(str, v)),
                                unit=e["unit"], source=e["source"],
                                status="validated" if e["status"] == "validated" else "assumed"))
        return out

    def robustness(self):
        f = ART / "robustness.json"
        if f.exists():
            return json.loads(f.read_text())
        return dict(dataset="MetroPT-3", failures_total=0, caught=0, median_lead_h=0.0, false_alarms_per_week=0.0,
                    note="Not run yet.")

    def markers(self):
        return json.loads((ART / "markers.json").read_text())
