"""Stream a scenario through the gateway API, hour by hour, like the browser Gateway page does.
  python -m backend.scripts.stream --scenario bad_sensor --speed 2 [--base-url http://localhost:8000] [--demo-key KEY] [--start ISO] [--hours 72]
The client is the gateway: it fetches the scenario's hourly payloads and POSTs them to /api/ingest."""
import argparse
import itertools
import os
import sys
import time

import httpx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="mill10")
    ap.add_argument("--speed", type=float, default=2.0, help="seconds of wall clock per simulated hour")
    ap.add_argument("--base-url", default=os.environ.get("MILLGUARD_API", "http://localhost:8000"))
    ap.add_argument("--demo-key", default=os.environ.get("DEMO_KEY"))
    ap.add_argument("--start", default=None)
    ap.add_argument("--hours", type=int, default=96, help="how many hours to send (default 96)")
    a = ap.parse_args()
    h = {"X-Demo-Key": a.demo_key} if a.demo_key else {}
    c = httpx.Client(base_url=a.base_url, headers=h, timeout=30)
    s = c.post("/api/live/start", json={"scenario_id": a.scenario, "start": a.start, "speed_s_per_h": a.speed})
    if s.status_code != 200:
        sys.exit(f"cannot start: {s.status_code} {s.text}")
    sess = s.json()
    print(f"session {sess['session_id']} · scenario {a.scenario} · from {sess['start_t']} · {a.speed} s per hour")
    sent = 0
    t = sess["start_t"]
    try:
        while sent < a.hours:
            n = min(24, a.hours - sent)
            rows = c.get(f"/api/scenarios/{a.scenario}/hours", params={"from": t, "n": n}).json()
            for hour, group in itertools.groupby(rows, key=lambda r: r["t"]):
                r = c.post("/api/ingest", json=list(group)).json()
                sent += 1
                flag = "  SENSOR: " + "; ".join(i["message_en"] for i in r["sensor_issues"]) if r["sensor_issues"] else ""
                brief = c.get("/api/brief").json()
                alerts = ", ".join(f"{x['asset_name']} {x['fault_class']}" for x in brief["actions"]) or "none"
                print(f"{hour}  live_at={r['live_at']}  machine alerts: {alerts}{flag}", flush=True)
                time.sleep(a.speed)
            t = rows[-1]["t"] if rows else t
            t = (__import__("pandas").Timestamp(t) + __import__("pandas").Timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    except KeyboardInterrupt:
        pass
    finally:
        c.post("/api/live/stop")
        print("stopped")


if __name__ == "__main__":
    main()
