"""Stub API: serves contracts/fixtures. Replaced by artifact-backed handlers in plan step 7."""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import (AssetDetail, Assumption, Backtest, Brief, FeedbackIn, FeedbackOut,
                                Line, Meta, Robustness)

FIX = Path(__file__).resolve().parents[2] / "contracts" / "fixtures"
app = FastAPI(title="MillGuard API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


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
def backtest(cpo_price: float | None = None, miss_cost_mult: float | None = None,
             alert_budget: int | None = None, compare: str = "run_to_failure", at: str | None = None):
    return fx("backtest")


@app.get("/api/assumptions", response_model=list[Assumption])
def assumptions(at: str | None = None):
    return fx("assumptions")


@app.get("/api/robustness", response_model=Robustness)
def robustness(at: str | None = None):
    return fx("robustness")


@app.post("/api/feedback", response_model=FeedbackOut)
def feedback(body: FeedbackIn):
    return {"ok": True}
