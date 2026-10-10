"""Backend checks: every fixture matches its Pydantic model, the three bookmarks hold their rules, numbers agree across endpoints."""
import json
import os
from pathlib import Path

import pytest

from backend.api import models as m
from backend.api.make_fixtures import check

FIX = Path(__file__).resolve().parents[2] / "contracts" / "fixtures"
ASSET_IDS = ["press_1", "press_2", "press_3", "press_4", "boiler_1"]
SUFFIX = {"quiet": "_quiet", "act": "_act", "both": ""}


def load(name):
    return json.loads((FIX / f"{name}.json").read_text())


def test_fixtures_match_models():
    single = {"meta": m.Meta, "backtest": m.Backtest, "robustness": m.Robustness, "feedback": m.FeedbackOut,
              "notify": m.NotifyOut, "notify_status": m.NotifyStatus}
    for name, model in single.items():
        model(**load(name))
    for name, model in (("assumptions", m.Assumption), ("faults", m.FaultGuide), ("replay_markers", m.Marker)):
        [model(**x) for x in load(name)]
    for suf in SUFFIX.values():
        m.Brief(**load("brief" + suf)); m.Line(**load("line" + suf))
        for a in ASSET_IDS:
            m.AssetDetail(**load(f"assets_{a}{suf}"))
    for f in FIX.glob("advice_*.json"):
        m.AdviceOut(**json.loads(f.read_text()))
    for f in list((FIX / "backtest_grid").glob("cpo*.json"))[:5]:
        m.Backtest(**json.loads(f.read_text()))


def test_backtest_grid_complete():
    idx = load("backtest_grid/index")
    assert len(idx["files"]) == 81 and all((FIX / "backtest_grid" / f["file"]).exists() for f in idx["files"])


def test_summaries_inside_series_and_one_number_per_signal():
    check(FIX)


def test_quiet_night_is_quiet():
    b = load("brief_quiet")
    assert b["actions"] == []
    for a in ASSET_IDS:
        d = load(f"assets_{a}_quiet")
        assert d["outlook"]["rm_saved_if_acted"] == 0 and d["status"] in ("ok", "watch")


def test_act_and_whole_mill_bookmarks():
    assert [a["asset_id"] for a in load("brief_act")["actions"]] == ["press_2"]
    assert load("brief")["actions"][0]["asset_id"] == "boiler_1"


@pytest.mark.parametrize("suf", list(SUFFIX.values()))
def test_one_risk_and_money_rule(suf):
    brief, line = load("brief" + suf), load("line" + suf)
    risk = {x["id"]: x["risk_pct"] for x in line["assets"]}
    for a in ASSET_IDS:
        d = load(f"assets_{a}{suf}")
        assert d["risk_pct"] == risk[a] == d["asset"]["risk_pct"] == d["outlook"]["risk_pct"]
        assert d["asset"]["name_ms"] and (d["action"] is None) == (d["status"] != "act")
        assert d["last_service"]["hours_since"] >= 0
    for act in brief["actions"]:
        assert 2 <= len(act["reasons"]) <= 3 and act["risk_pct"] <= 99
        assert act["rm_saved_if_acted"] == max(0, act["rm_at_risk"] - act["rm_cost_to_act"])
        assert act["asset_name_ms"] and risk[act["asset_id"]] == act["risk_pct"]
    assert brief["rm_protected_total"] == sum(a["rm_saved_if_acted"] for a in brief["actions"])


def test_four_policies_and_order():
    pol = {p["id"]: p["total_cost_rm"] for p in load("backtest")["policies"]}
    assert set(pol) == {"run_to_failure", "fixed_interval", "millguard", "schedule_plus_millguard"}
    assert pol["schedule_plus_millguard"] < pol["millguard"] < pol["fixed_interval"] < pol["run_to_failure"]


def test_assumption_labels_are_human():
    for a in load("assumptions"):
        assert a["label"] and "_" not in a["label"] and a["label"][0].isupper()


def test_live_api_matches_fixture_bookmarks():
    from fastapi.testclient import TestClient
    from backend.api.main import app, STUB
    if STUB:
        pytest.skip("stub mode")
    c, at = TestClient(app), load("bookmarks")
    for key, suf in SUFFIX.items():
        b = c.get("/api/brief", params={"at": at[key]}).json()
        assert [a["id"] for a in b["actions"]] == [a["id"] for a in load("brief" + suf)["actions"]]
        for a in ASSET_IDS:
            assert c.get(f"/api/assets/{a}", params={"at": at[key]}).status_code == 200


def test_advice_never_crashes_without_key(monkeypatch):
    from backend.advice import engine
    from backend.engine.service import Service
    monkeypatch.setenv("LLM_API_KEY", "")
    s = Service()
    act = next(a for a in s.actions if a["t_open"].month == 3)
    o = engine.advise(s, act["asset_id"], act["t_open"].isoformat(), "en", use_cache=False)
    assert o.cached is False and o.sections == [] and o.message
    assert engine.advise(s, "nope", None, "ms").message
