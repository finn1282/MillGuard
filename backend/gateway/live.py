"""Live session and ingest. All state goes through backend/state.py; nothing is kept in this process."""
import math
import os
import time
import uuid

import pandas as pd

from backend import state
from backend.engine import text
from backend.gateway import health, scenarios
from backend.gateway.health import BOILER_SIGNALS, PRESS_SIGNALS, SENSOR_OF

ASSETS = ["press_1", "press_2", "press_3", "press_4", "boiler_1"]
ACTIVE_H = 3   # a sensor issue stays active this long after its last bad reading


def iso(t):
    return pd.Timestamp(t).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"


def naive(t):
    t = pd.Timestamp(t)
    return t.tz_convert("Asia/Kuala_Lumpur").tz_localize(None) if t.tzinfo else t


def session():
    """The active session record, or None."""
    return state.db().get("live")


def start(scenario_id, start_t=None, speed=2.0):
    d = scenarios.meta(scenario_id)
    if d is None:
        return None
    rec = dict(session_id="s-" + uuid.uuid4().hex[:6], scenario_id=scenario_id, start_t=iso(naive(start_t or d["default_start"]).floor("h")),
               speed_s_per_h=float(speed), started_wallclock=pd.Timestamp.now(tz="Asia/Kuala_Lumpur").strftime("%Y-%m-%dT%H:%M:%S+08:00"),
               gateway_id=None, source=None, ingested=0, last_wall=None, pending={}, live_at=None)
    state.db().set("live", rec)
    return {k: rec[k] for k in ("session_id", "scenario_id", "start_t", "speed_s_per_h", "started_wallclock")}


def stop():
    state.db().delete("live")


def _issues(sid):
    return state.db().get(f"issues:{sid}") or {}


def active_issues(sid, at):
    at = naive(at) if at else None
    out = []
    for i in _issues(sid).values():
        last = naive(i["t"])
        if at is None or (last <= at and (at - last) < pd.Timedelta(hours=ACTIVE_H)):
            out.append(i)
    return sorted(out, key=lambda i: (i["t"], i["asset_id"]))


def status():
    s = session()
    if not s:
        return dict(enabled=False, session_id=None, source=None, gateway_id=None, live_at=None, readings_ingested=0,
                    seconds_since_last=None, sensor_issues=[])
    return dict(enabled=True, session_id=s["session_id"], source=s["source"] or f"scenario:{s['scenario_id']}", gateway_id=s["gateway_id"],
                live_at=s["live_at"], readings_ingested=s["ingested"],
                seconds_since_last=None if s["last_wall"] is None else round(time.time() - s["last_wall"], 1),
                sensor_issues=active_issues(s["session_id"], s["live_at"] or s["start_t"]))


def sensor_alerts_at(at=None):
    """Active sensor alerts of the session at `at` (default live_at), for merging into line and brief."""
    s = session()
    return [] if not s else active_issues(s["session_id"], at or s["live_at"] or s["start_t"])


def _clean(readings, asset_id):
    allowed = BOILER_SIGNALS if asset_id.startswith("boiler") else PRESS_SIGNALS
    return {k: (None if v is None or (isinstance(v, float) and not math.isfinite(v)) else float(v)) for k, v in readings.items() if k in allowed}


def ingest(items):
    """items: list of ReadingIn. -> IngestOut dict. Sensor-health checks run here; a bad reading is a sensor alert only."""
    db = state.db()
    s = session()
    sid = s["session_id"] if s else "adhoc"
    accepted = rejected = 0
    raised = {}
    issues = _issues(sid)
    new_keys = []
    for it in sorted(items, key=lambda x: (x.asset_id, x.t)):
        try:
            t = naive(it.t).floor("h")
        except (ValueError, TypeError):
            rejected += 1; continue
        r = _clean(it.readings, it.asset_id)
        if not r:
            rejected += 1; continue
        key = f"buf:{sid}:{it.asset_id}"
        buf = db.items(key)
        history = [b["r"] for b in buf if naive(b["t"]) < t]
        db.push(key, dict(t=iso(t), r=r), keep=health.HISTORY_H)
        accepted += 1
        found = {}
        for sig, kind in health.check(it.asset_id, r, history):
            found.setdefault((SENSOR_OF[sig], kind), sig)
        for (sensor, kind), sig in found.items():
            k = f"{it.asset_id}|{sensor}|{kind}"
            prev = issues.get(k)
            continuing = prev is not None and (t - naive(prev["t"])) <= pd.Timedelta(hours=ACTIVE_H)
            a = health.alert(it.asset_id, sig, kind, iso(t), prev["first_t"] if continuing else None)
            if not continuing:
                new_keys.append(k + "|" + a["first_t"])
            issues[k] = raised[k] = a
    if raised:
        db.set(f"issues:{sid}", issues)
    live_at = None
    if s:
        first = items[0] if items else None
        s["gateway_id"] = s["gateway_id"] or (first.gateway_id if first else None)
        s["source"] = s["source"] or (first.source if first else None)
        s["ingested"] += accepted
        s["last_wall"] = time.time()
        for it in items:
            try:
                h = iso(naive(it.t).floor("h"))
            except (ValueError, TypeError):
                continue
            seen = s["pending"].setdefault(h, [])
            if it.asset_id not in seen:
                seen.append(it.asset_id)
        done = [h for h, a in s["pending"].items() if len(a) == len(ASSETS)]
        before = s["live_at"]
        if done:
            s["live_at"] = max(done + ([before] if before else []))
        s["pending"] = {h: a for h, a in s["pending"].items() if not s["live_at"] or naive(h) > naive(s["live_at"])}
        db.set("live", s)
        live_at = s["live_at"]
        if live_at and live_at != before and os.environ.get("LIVE_AUTONOTIFY") == "1":
            _autonotify(s, live_at, new_keys)
    return dict(accepted=accepted, rejected=rejected, sensor_issues=list(raised.values()), live_at=live_at)


def _autonotify(s, live_at, new_keys):
    """Push new machine alerts (deduped by the notify store) and first-time sensor issues to Telegram, inside this request."""
    try:
        from backend.notify import messages, send, store
        svc = scenarios.service(s["scenario_id"])
        if svc is None or store.token() is None:
            return
        send.notify(svc, live_at, "alert")
        for i in active_issues(s["session_id"], live_at):
            if state.db().add(f"sensor_sent:{s['session_id']}", f"{i['asset_id']}|{i['signal']}|{i['kind']}|{i['first_t']}"):
                if not store.subscribers():
                    print(store.NO_SUBS)
                for chat, sub in store.subscribers().items():
                    send._post("sendMessage", chat_id=chat, text=messages.sensor_text(i, sub["lang"]))
    except Exception as e:   # Telegram or network trouble must never fail an ingest
        print("autonotify failed:", type(e).__name__)


def current(default_svc, at=None):
    """(service, at) for what the app should show now: the session's scenario at live_at, else the default replay."""
    s = session()
    if s:
        sv = scenarios.service(s["scenario_id"])
        if sv is not None:
            return sv, s["live_at"] or s["start_t"]
    return default_svc, at
