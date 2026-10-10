"""MillGuard API. Reads pipeline artifacts; falls back to contracts/fixtures if artifacts are missing
or MILLGUARD_STUB=1. Stateless except an append-only feedback log."""
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import (AssetDetail, Assumption, Backtest, Brief, FeedbackIn, FeedbackOut,
                                FaultGuide, Line, Marker, Meta, Robustness)

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "contracts" / "fixtures"
ART = ROOT / "backend" / "artifacts"
STUB = os.environ.get("MILLGUARD_STUB") == "1" or not (ART / "actions.json").exists()
svc = None
if not STUB:
    from backend.engine.service import Service
    svc = Service()

app = FastAPI(title="MillGuard API", version="1.6")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def fx(name):
    return json.loads((FIX / f"{name}.json").read_text())


def is_quiet(at):
    return bool(at) and at.startswith("2025-01-11")


@app.get("/api/meta", response_model=Meta)
def meta():
    return fx("meta") if STUB else svc.meta()


@app.get("/api/brief", response_model=Brief)
def brief(at: str | None = None):
    if STUB:
        return fx("brief_quiet" if is_quiet(at) else "brief")
    return svc.brief(at)


@app.get("/api/line", response_model=Line)
def line(at: str | None = None):
    if STUB:
        return fx("line_quiet" if is_quiet(at) else "line")
    return svc.line(at)


@app.get("/api/assets/{asset_id}", response_model=AssetDetail)
def asset(asset_id: str, at: str | None = None, window_h: int = 168):
    if STUB:
        try:
            return fx(f"assets_{asset_id}")
        except FileNotFoundError:
            raise HTTPException(404, "unknown asset")
    out = svc.asset(asset_id, at, int(clamp(window_h, 24, 720)))
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
def feedback(body: FeedbackIn):
    if not STUB:
        with open(ART / "feedback.jsonl", "a") as f:
            f.write(body.model_dump_json() + "\n")
    return {"ok": True}
