"""v1.14 gateway: payload validation, sensor-health (sensor alert, never a machine alert), scenario parity, state backends, write-key."""
import itertools
import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import state
from backend.engine.service import ART
from backend.gateway import health, scenarios

SCN = ART / "scenarios"
needs_scn = pytest.mark.skipif(not (SCN / "bad_sensor" / "actions.json").exists(), reason="run `make scenarios` first")


@pytest.fixture(autouse=True)
def fresh_state():
    state.use(state.Memory())
    yield
    state.use(None)


@pytest.fixture
def client():
    from backend.api.main import app
    return TestClient(app)


def press(t, **kw):
    r = dict(motor_current=62.0, throughput_tph=14.0, vib_rms=2.1, vib_kurtosis=3.0, gearbox_oil_temp=68.0, cone_pressure=45.0, fibre_oil_loss=None)
    return dict(gateway_id="g", source="test", asset_id="press_4", t=t, readings={**r, **kw})


def test_bad_payload_is_422(client):
    assert client.post("/api/ingest", json={"gateway_id": "g"}).status_code == 422
    assert client.post("/api/ingest", json=press("2025-09-01T00:00:00+08:00") | {"asset_id": "press_9"}).status_code == 422
    assert client.post("/api/ingest", json=press("2025-09-01T00:00:00+08:00") | {"readings": {"vib_rms": "high"}}).status_code == 422


def test_health_checks_unit():
    rng = np.random.default_rng(1)
    base = press("x")["readings"]
    hist = [{k: (None if v is None else float(v * (1 + rng.normal(0, 0.01)))) for k, v in base.items()} for _ in range(48)]
    ok = health.check("press_4", press("x")["readings"], hist)
    assert ok == []
    assert ("vib_rms", "out_of_range") in health.check("press_4", press("x", vib_rms=99.0)["readings"], hist)
    assert ("vib_rms", "spike") in health.check("press_4", press("x", vib_rms=12.6)["readings"], hist)
    frozen = hist[:40] + [dict(hist[0], vib_rms=2.1)] * 5
    assert ("vib_rms", "stuck") in health.check("press_4", press("x", vib_rms=2.1)["readings"], frozen)
    gone = hist + [dict(hist[0], vib_rms=None)] * 2
    assert ("vib_rms", "missing") in health.check("press_4", press("x", vib_rms=None)["readings"], gone)
    off = health.check("press_4", press("x", throughput_tph=0.0, vib_rms=0.0, motor_current=0.0)["readings"], hist)
    assert off == []   # a stopped press reads zero: not a fault


@needs_scn
def test_stuck_then_spike_raises_sensor_alert_and_no_machine_alert(client):
    from backend.api import main
    if main.STUB:
        pytest.skip("stub mode")
    s = client.post("/api/live/start", json={"scenario_id": "bad_sensor"}).json()
    meta = scenarios.meta("bad_sensor")
    start = s["start_t"]
    rows = client.get("/api/scenarios/bad_sensor/hours", params={"from": start, "n": 60}).json()
    sensor, machine = [], set()
    for _, g in itertools.groupby(rows, key=lambda r: r["t"]):
        client.post("/api/ingest", json=list(g))
        b = client.get("/api/brief").json()
        sensor += b["sensor_alerts"]
        machine |= {a["asset_id"] for a in b["actions"]}
    assert {i["kind"] for i in sensor if i["asset_id"] == "press_4"} >= {"stuck", "spike"}
    assert all("not the machine" in i["message_en"] for i in sensor)
    assert "press_4" not in machine
    assert meta["fault_window"]["stuck_from"] < meta["fault_window"]["spike_at"]
    line = client.get("/api/line").json()
    assert next(a for a in line["assets"] if a["id"] == "press_4")["status"] != "act"


@needs_scn
def test_mill10_scenario_equals_existing_artifacts():
    from backend.engine.service import Service
    a, b = Service(), scenarios.service("mill10")
    for at in ("2025-02-10T19:00:00+08:00", "2025-06-21T17:00:00+08:00", "2025-08-25T03:00:00+08:00", "2025-11-03T05:00:00+08:00"):
        assert a.brief(at) == b.brief(at)
        assert a.line(at) == b.line(at)
        for aid in ("press_2", "boiler_1"):
            assert a.asset(aid, at) == b.asset(aid, at)
    assert len(a.actions) == len(b.actions)


@needs_scn
def test_live_at_needs_all_five_assets(client):
    from backend.api import main
    if main.STUB:
        pytest.skip("stub mode")
    client.post("/api/live/start", json={"scenario_id": "mill10"})
    rows = client.get("/api/scenarios/mill10/hours", params={"n": 2}).json()
    assert len(rows) == 10 and {r["asset_id"] for r in rows} == {"press_1", "press_2", "press_3", "press_4", "boiler_1"}
    first_hour = [r for r in rows if r["t"] == rows[0]["t"]]
    r = client.post("/api/ingest", json=first_hour[:4]).json()
    assert r["live_at"] is None and r["accepted"] == 4
    r = client.post("/api/ingest", json=first_hour[4:]).json()
    assert r["live_at"] == rows[0]["t"]
    st = client.get("/api/live").json()
    assert st["enabled"] and st["readings_ingested"] == 5 and st["live_at"] == rows[0]["t"]
    assert client.post("/api/live/stop").json()["enabled"] is False


def test_state_memory_backend():
    db = state.Memory()
    db.set("a", {"x": 1}); assert db.get("a") == {"x": 1} and db.get("none") is None
    for i in range(10):
        db.push("l", i, keep=3)
    assert db.items("l") == [7, 8, 9]
    assert db.add("s", "m") is True and db.add("s", "m") is False and db.members("s") == ["m"]
    db.delete("a"); assert db.get("a") is None


def test_state_file_backend_is_shared_between_instances(tmp_path):
    f = tmp_path / "s.json"
    a, b = state.Memory(f), state.Memory(f)   # the API and the polling bot are two processes
    a.set("subs", {"1": {"lang": "en"}})
    assert b.get("subs") == {"1": {"lang": "en"}}
    b.add("sent:1", "act_x"); assert a.members("sent:1") == ["act_x"]


def test_state_picks_backend_from_env(monkeypatch):
    monkeypatch.setenv("KV_REST_API_URL", "https://x.upstash.io"); monkeypatch.setenv("KV_REST_API_TOKEN", "t")
    assert isinstance(state.make_backend(), state.Redis)
    monkeypatch.delenv("KV_REST_API_URL"); monkeypatch.delenv("KV_REST_API_TOKEN")
    assert isinstance(state.make_backend(), state.Memory)


@pytest.mark.parametrize("method,path,body", [
    ("post", "/api/ingest", press("2025-09-01T00:00:00+08:00")), ("post", "/api/live/start", {"scenario_id": "mill10"}),
    ("post", "/api/live/stop", None), ("post", "/api/upload", None),
    ("post", "/api/notify", {"kind": "brief"}), ("post", "/api/feedback", {"action_id": "x", "useful": True})])
def test_write_endpoints_need_the_demo_key(client, monkeypatch, method, path, body):
    monkeypatch.setenv("DEMO_KEY", "secret")
    r = getattr(client, method)(path, json=body) if body is not None else getattr(client, method)(path)
    assert r.status_code == 401
    r = getattr(client, method)(path, json=body, headers={"X-Demo-Key": "secret"}) if body is not None else getattr(client, method)(path, headers={"X-Demo-Key": "secret"})
    assert r.status_code != 401
    monkeypatch.delenv("DEMO_KEY")
    r = getattr(client, method)(path, json=body) if body is not None else getattr(client, method)(path)
    assert r.status_code != 401   # open when DEMO_KEY is unset (local)


def test_upload_is_501_on_vercel(client, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    r = client.post("/api/upload", content=b"asset_id,t\n", headers={"content-type": "text/csv"})
    assert r.status_code == 501 and "CSV upload is available in the local version" in r.text


def test_webhook_needs_the_secret(client, monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "w")
    assert client.post("/api/telegram/webhook", json={}).status_code == 401
    assert client.post("/api/telegram/webhook", json={}, headers={"X-Telegram-Bot-Api-Secret-Token": "bad"}).status_code == 401
    assert client.post("/api/telegram/webhook", json={}, headers={"X-Telegram-Bot-Api-Secret-Token": "w"}).status_code == 200


def test_csv_parsing_and_validation(client, monkeypatch):
    from backend.gateway import upload
    name, data = upload.read_body(b"--b\r\nContent-Disposition: form-data; name=\"file\"; filename=\"my.csv\"\r\nContent-Type: text/csv\r\n\r\nasset_id,t\r\n--b--\r\n",
                                  "multipart/form-data; boundary=b", None)
    assert name == "my.csv" and data.startswith(b"asset_id,t")
    assert upload.read_body(b"x", "text/csv", "raw.csv") == ("raw.csv", b"x")
    monkeypatch.delenv("VERCEL", raising=False)
    from backend.api import main
    if main.STUB:
        pytest.skip("stub mode")
    r = client.post("/api/upload?name=s.csv", content=b"asset_id,t,vib_rms\npress_1,2025-01-01T00:00:00,1\n", headers={"content-type": "text/csv"})
    assert r.status_code == 422 and "at least 400" in r.json()["detail"]
    assert client.post("/api/upload?name=s.csv", content=b"hello", headers={"content-type": "text/csv"}).status_code == 422
