"""Stub API: serves contracts/fixtures. Replaced by artifact-backed handlers in plan step 7."""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import (AssetDetail, Assumption, Backtest, Brief, FeedbackIn, FeedbackOut,
                                Line, Marker, Meta, Robustness)

FIX = Path(__file__).resolve().parents[2] / "contracts" / "fixtures"
app = FastAPI(title="MillGuard API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def fx(name):
    return json.loads((FIX / f"{name}.json").read_text())


@app.get("/api/meta", response_model=Meta)
def meta():
    return fx("meta")


@app.get("/api/brief", response_model=Brief)
def brief(at: str | None = None):
    return fx("brief")


@app.get("/api/line", response_model=Line)
def line(at: str | None = None):
    return fx("line")


@app.get("/api/assets/{asset_id}", response_model=AssetDetail)
def asset(asset_id: str, at: str | None = None, window_h: int = 168):
    try:
        return fx(f"assets_{asset_id}")
    except FileNotFoundError:
        raise HTTPException(404, "unknown asset")


@app.get("/api/backtest", response_model=Backtest)
def backtest(cpo_price: float = 4292.5, miss_cost_mult: float = 1.0,
             alert_budget: int = 5, compare: str = "run_to_failure", at: str | None = None):
    cpo_price = clamp(cpo_price, 3800, 5000)
    miss_cost_mult = clamp(miss_cost_mult, 0.5, 3)
    alert_budget = int(clamp(alert_budget, 1, 10))
    return fx("backtest")


@app.get("/api/assumptions", response_model=list[Assumption])
def assumptions(at: str | None = None):
    return fx("assumptions")


@app.get("/api/robustness", response_model=Robustness)
def robustness(at: str | None = None):
    return fx("robustness")


@app.get("/api/replay/markers", response_model=list[Marker])
def replay_markers(at: str | None = None):
    return fx("replay_markers")


@app.post("/api/feedback", response_model=FeedbackOut)
def feedback(body: FeedbackIn):
    return {"ok": True}
