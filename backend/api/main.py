"""MillGuard API. Reads pipeline artifacts; falls back to contracts/fixtures if artifacts are missing
or MILLGUARD_STUB=1. Stateless except an append-only feedback log."""
import json
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import (AdviceIn, AdviceOut, AssetDetail, Assumption, Backtest, Brief, FeedbackIn, FeedbackOut,
                                FaultGuide, IngestOut, Line, LiveSession, LiveStartIn, LiveStatus, Marker, Meta, NotifyIn, NotifyOut, NotifyStatus,
                                ReadingIn, Robustness, Scenario, UploadOut)

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "contracts" / "fixtures"
ART = ROOT / "backend" / "artifacts"
STUB = os.environ.get("MILLGUARD_STUB") == "1" or not (ART / "actions.json").exists()
svc = None
if not STUB:
    from backend.engine.service import Service
    svc = Service()

from backend.notify import store as _store   # noqa: E402  (loads backend/.env into os.environ: DEMO_KEY, KV_*, TELEGRAM_*)
_store.load_env()
try:
    print(_store.startup_line())
except Exception as e:   # a state backend that is down must not stop the API
    print("telegram: status unavailable", type(e).__name__)

app = FastAPI(title="MillGuard API", version="1.14")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def need_key(x_demo_key: str | None = Header(default=None)):
    """Write endpoints: X-Demo-Key must match DEMO_KEY when it is set; open when unset (local)."""
    want = os.environ.get("DEMO_KEY")
    if want and x_demo_key != want:
        raise HTTPException(401, "X-Demo-Key missing or wrong")


def pick(at):
    """(service, at): while a live session is active, its scenario at live_at; otherwise the replay mill 10."""
    from backend.gateway import live
    return live.current(svc, at)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def fx(name):
    return json.loads((FIX / f"{name}.json").read_text())


def variant(at):
    """Fixture suffix for the bookmark date nearest to `at` (default: the both-alerts night)."""
    idx = fx("bookmarks")
    d = (at or "")[:10]
    return {idx["quiet"][:10]: "_quiet", idx["act"][:10]: "_act"}.get(d, "")


@app.get("/api/meta", response_model=Meta)
def meta():
    if STUB:
        return fx("meta")
    return pick(None)[0].meta()


@app.get("/api/brief", response_model=Brief)
def brief(at: str | None = None):
    if STUB:
        return fx("brief" + variant(at))
    from backend.gateway import live
    sv, at2 = pick(at)
    out = sv.brief(at2)
    out["sensor_alerts"] = live.sensor_alerts_at(out["at"]) if live.session() else []
    return out


@app.get("/api/line", response_model=Line)
def line(at: str | None = None):
    if STUB:
        return fx("line" + variant(at))
    from backend.gateway import live
    sv, at2 = pick(at)
    out = sv.line(at2)
    out["sensor_alerts"] = live.sensor_alerts_at(out["at"]) if live.session() else []
    return out


@app.get("/api/assets/{asset_id}", response_model=AssetDetail)
def asset(asset_id: str, at: str | None = None, window_h: int = 168):
    if STUB:
        try:
            v = variant(at)
            return fx(f"assets_{asset_id}{v}")
        except FileNotFoundError:
            raise HTTPException(404, "unknown asset")
    sv, at2 = pick(at)
    out = sv.asset(asset_id, at2, int(clamp(window_h, 24, 720)))
    if out is None:
        raise HTTPException(404, "unknown asset")
    return out


@app.get("/api/backtest", response_model=Backtest)
def backtest(cpo_price: float = 4292.5, miss_cost_mult: float = 1.0, alert_budget: int = 5,
             compare: str = "run_to_failure", inspection_accuracy: float = 0.5, at: str | None = None):
    cpo_price = clamp(cpo_price, 3800, 5000)
    miss_cost_mult = clamp(miss_cost_mult, 0.5, 3)
    alert_budget = int(clamp(alert_budget, 1, 10))
    if STUB:
        return fx("backtest")
    return svc.backtest(cpo_price, miss_cost_mult, alert_budget, compare, clamp(inspection_accuracy, 0.0, 1.0))


@app.get("/api/faults", response_model=list[FaultGuide])
def faults(at: str | None = None):
    from backend.engine import playbook
    return fx("faults") if STUB else playbook.all_guides()


@app.get("/api/assumptions", response_model=list[Assumption])
def assumptions(at: str | None = None):
    return fx("assumptions") if STUB else svc.assumptions()


@app.get("/api/robustness", response_model=Robustness)
def robustness(at: str | None = None):
    return fx("robustness") if STUB else svc.robustness()


@app.get("/api/replay/markers", response_model=list[Marker])
def replay_markers(at: str | None = None):
    return fx("replay_markers") if STUB else svc.markers()


@app.post("/api/feedback", response_model=FeedbackOut)
def feedback(body: FeedbackIn, _=Depends(need_key)):
    if not STUB:
        from backend.api.feedback import record
        record(body)
    return {"ok": True}


@app.post("/api/advice", response_model=AdviceOut)
def advice(body: AdviceIn):
    from backend.advice import engine
    if STUB:
        return engine.from_fixture(body.asset_id, body.at, body.lang) or engine.unavailable(body.lang)
    return engine.advise(svc, body.asset_id, body.at, body.lang)


@app.get("/api/notify/status", response_model=NotifyStatus)
def notify_status():
    if STUB:
        return fx("notify_status")
    from backend.notify import send
    return send.status()


@app.post("/api/notify", response_model=NotifyOut)
def notify(body: NotifyIn, _=Depends(need_key)):
    if STUB:
        return fx("notify_schedule") if body.kind == "schedule" else {"ok": False, "sent": 0}
    from backend.notify import send
    try:
        if body.kind == "schedule":
            res = send.schedule(svc, body.at, body.action_id)
            if res is None:
                raise HTTPException(404, "action not found")
            return {"ok": res[0], "sent": res[1]}
        ok, sent = send.notify(svc, body.at, body.kind)
    except HTTPException:
        raise
    except Exception:   # a Telegram or network problem must never take the API down
        return {"ok": False, "sent": 0}
    return {"ok": ok, "sent": sent}


# ---- v1.14 gateway ----
@app.post("/api/ingest", response_model=IngestOut)
def ingest(body: ReadingIn | list[ReadingIn], _=Depends(need_key)):
    if STUB:
        return fx("ingest")
    from backend.gateway import live
    return live.ingest(body if isinstance(body, list) else [body])


@app.get("/api/live", response_model=LiveStatus)
def live_status():
    if STUB:
        return fx("live_stop")
    from backend.gateway import live
    return live.status()


@app.post("/api/live/start", response_model=LiveSession)
def live_start(body: LiveStartIn, _=Depends(need_key)):
    if STUB:
        return fx("live_start")
    from backend.gateway import live
    out = live.start(body.scenario_id, body.start, body.speed_s_per_h)
    if out is None:
        raise HTTPException(404, "unknown scenario (run make scenarios)")
    return out


@app.post("/api/live/stop", response_model=LiveStatus)
def live_stop(_=Depends(need_key)):
    if STUB:
        return fx("live_stop")
    from backend.gateway import live
    live.stop()
    return live.status()


@app.get("/api/scenarios", response_model=list[Scenario])
def scenarios_list():
    if STUB:
        return fx("scenarios")
    from backend.gateway import scenarios
    return scenarios.listing()


@app.get("/api/scenarios/{scenario_id}/hours", response_model=list[ReadingIn])
def scenario_hours(scenario_id: str, n: int = 24, from_: str | None = Query(default=None, alias="from")):
    if STUB:
        return fx("scenario_hours")
    from backend.gateway import scenarios
    m = scenarios.meta(scenario_id)
    if m is None:
        raise HTTPException(404, "unknown scenario")
    return scenarios.hours(scenario_id, from_ or m["default_start"], int(clamp(n, 1, 168)))


@app.post("/api/upload", response_model=UploadOut)
async def upload(request: Request, name: str | None = None, _=Depends(need_key)):
    """CSV (asset_id, t, one column per reading), as multipart/form-data or a raw text/csv body. Local only."""
    if os.environ.get("VERCEL") == "1":
        raise HTTPException(501, "CSV upload is available in the local version")
    if STUB:
        raise HTTPException(501, "run make all and make scenarios first")
    from backend.gateway import upload as up
    raw = await request.body()
    fname, data = up.read_body(raw, request.headers.get("content-type", ""), name)
    try:
        return up.build_from_csv(fname, data)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    """Telegram calls this (set with backend/scripts/set_webhook.py). Same handlers as the polling bot."""
    want = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    if not want or x_telegram_bot_api_secret_token != want:
        raise HTTPException(401, "bad webhook secret")
    update = await request.json()
    if STUB:
        return {"ok": True}
    from backend.notify import handlers
    try:
        handlers.handle_update(update, svc)
    except Exception as e:   # always 200 so Telegram does not retry forever
        print("webhook: error", type(e).__name__)
    return {"ok": True}
