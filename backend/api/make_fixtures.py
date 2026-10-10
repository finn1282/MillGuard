"""Snapshot of the real API at the three demo bookmarks plus the real backtest -> contracts/fixtures/*.json.
Fixture mode (MILLGUARD_STUB=1) is the demo backup, so it shows true numbers. Run `make all` first."""
import json
import os
import re
from pathlib import Path

from backend.api.models import (AssetDetail, Assumption, Backtest, Brief, FeedbackOut, Line, Marker, Meta, NotifyOut, NotifyStatus, Robustness)
from backend.engine import playbook
from backend.engine.service import ART, ASSETS, Service

OUT = Path(__file__).resolve().parents[2] / "contracts" / "fixtures"


def write(name, data):
    if isinstance(data, list):
        data = [d.model_dump(mode="json") if hasattr(d, "model_dump") else d for d in data]
    elif hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))


NUM = re.compile(r"^(-?\d+(?:\.(\d+))?) (?:to|kepada) (-?\d+(?:\.(\d+))?)")
ENGLISH_IN_MS = re.compile(r"\b(hours?|days?|over|alarms?|since|the|and|is|are|per|Press|Boiler)\b")


def check(out):
    """Fail if any series summary quotes numbers outside its own served points, or Malay text still holds English words."""
    bad = []
    for f in sorted(out.glob("assets_*.json")):
        for s in json.loads(f.read_text())["series"]:
            v = [p[1] for p in s["points"]]
            for key in ("summary_en", "summary_ms"):
                m = NUM.match(s[key])
                if not v or not m:
                    bad.append(f"{f.name} {s['signal']}: cannot read {s[key]!r}")
                    continue
                tol = 0.5 * 10 ** -len(m.group(2) or "") + 0.0005
                for x in (float(m.group(1)), float(m.group(3))):
                    if not min(v) - tol <= x <= max(v) + tol:
                        bad.append(f"{f.name} {s['signal']}: {s[key]!r} outside points {min(v)}..{max(v)}")
            if s["unit_ms"] not in s["summary_ms"]:
                bad.append(f"{f.name} {s['signal']}: unit_ms {s['unit_ms']!r} missing from summary_ms")
    for f in sorted(out.glob("assets_*.json")):   # one signal, one percentage, per asset
        d = json.loads(f.read_text())
        quoted = {}
        for r in (d.get("action") or {}).get("reasons", []):
            m = re.search(r"(\d+)% (above|below)", r["text_en"])
            if m:
                quoted.setdefault(r["signal"], set()).add((int(m.group(1)), "up" if m.group(2) == "above" else "down"))
        for c in (d.get("diagnosis") or {}).get("fingerprint", []):
            m = re.match(r"(Up|Down) (\d+)%", c["observed_en"])
            if m:
                quoted.setdefault(c["signal"], set()).add((int(m.group(2)), m.group(1).lower()))
        bad += [f"{f.name} {sig}: two different comparisons {sorted(v)}" for sig, v in quoted.items() if len(v) > 1]
    for f in sorted(out.glob("*.json")):
        def walk(x, k=""):
            if isinstance(x, dict):
                for a, b in x.items():
                    walk(b, a)
            elif isinstance(x, list):
                for b in x:
                    walk(b, k)
            elif isinstance(x, str) and (k.endswith("_ms") or k == "name_ms") and ENGLISH_IN_MS.search(x):
                bad.append(f"{f.name} {k}: {x!r}")
        walk(json.loads(f.read_text()))
    if bad:
        raise SystemExit("fixture check failed:\n" + "\n".join(bad[:40]) + f"\n({len(bad)} problems)")
    print("fixture check ok: every summary sits inside its series, no English left in Malay text")


GRID = dict(cpo_price=[3800, 4292.5, 5000], miss_cost_mult=[0.5, 1, 3], alert_budget=[3, 5, 10], inspection_accuracy=[0, 0.5, 1])


def grid_name(c, m, b, a):
    return f"cpo{c:g}_miss{m:g}_bud{b:g}_acc{a:g}"


def backtest_grid(s):
    d = OUT / "backtest_grid"
    d.mkdir(exist_ok=True)
    index = []
    for c in GRID["cpo_price"]:
        for m in GRID["miss_cost_mult"]:
            for b in GRID["alert_budget"]:
                for a in GRID["inspection_accuracy"]:
                    name = grid_name(c, m, b, a)
                    (d / f"{name}.json").write_text(json.dumps(Backtest(**s.backtest(c, m, b, "run_to_failure", a)).model_dump(mode="json"), ensure_ascii=False))
                    index.append(dict(file=f"{name}.json", cpo_price=c, miss_cost_mult=m, alert_budget=b, inspection_accuracy=a))
    (d / "index.json").write_text(json.dumps(dict(axes=GRID, files=index), indent=1))
    print(f"backtest grid: {len(index)} files")


def advice_fixtures(s, at):
    """Press 2 act-now and Boiler 1 whole-mill, EN and BM. Kept once written; REFRESH_ADVICE=1 asks the model again."""
    from backend.advice import engine
    for aid, key, suffix in (("press_2", "act", "_act"), ("boiler_1", "both", "")):
        for lang in ("en", "ms"):
            f = OUT / f"advice_{aid}{suffix}_{lang}.json"
            if f.exists() and not os.environ.get("REFRESH_ADVICE"):
                continue
            o = engine.advise(s, aid, at[key], lang, use_cache=False)
            if o.sections:
                write(f.stem, o)
            else:
                print(f"WARNING: no advice written for {f.name} ({o.message})")


def keep_gateway_fixtures():
    """v1.14 gateway fixtures are authored by hand (contract examples); validate them here instead of regenerating."""
    from backend.api import models as m
    for name, model, many in (("ingest", m.IngestOut, 0), ("live", m.LiveStatus, 0), ("live_start", m.LiveSession, 0), ("live_stop", m.LiveStatus, 0),
                              ("scenarios", m.Scenario, 1), ("scenario_hours", m.ReadingIn, 1), ("upload", m.UploadOut, 0)):
        d = json.loads((OUT / f"{name}.json").read_text())
        [model(**x) for x in d] if many else model(**d)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = Service()
    marks = [m for m in s.markers() if m["kind"] == "bookmark"]
    at = {"quiet": next(m["t"] for m in marks if m["label_en"].startswith("Quiet")),
          "act": next(m["t"] for m in marks if m["label_en"].endswith("act now")),
          "both": next(m["t"] for m in marks if m["label_en"].startswith("Boiler alert"))}
    write("meta", Meta(**s.meta()))
    for key, suffix in (("both", ""), ("act", "_act"), ("quiet", "_quiet")):
        write(f"brief{suffix}", Brief(**s.brief(at[key])))
        write(f"line{suffix}", Line(**s.line(at[key])))
        for aid, *_ in ASSETS:
            write(f"assets_{aid}{suffix}", AssetDetail(**s.asset(aid, at[key])))
    write("backtest", Backtest(**s.backtest()))
    write("replay_markers", [Marker(**m) for m in s.markers()])
    write("assumptions", [Assumption(**a) for a in s.assumptions()])
    write("robustness", Robustness(**s.robustness()))
    write("faults", playbook.all_guides())
    write("feedback", FeedbackOut(ok=True))
    write("notify_status", NotifyStatus(enabled=False, channel="telegram", subscribers=0))
    write("notify", NotifyOut(ok=False, sent=0))
    write("notify_schedule", NotifyOut(ok=True, sent=3))
    keep_gateway_fixtures()
    (OUT / "bookmarks.json").write_text(json.dumps(at, indent=1))
    print("fixtures (real snapshot) written to", OUT, at)
    backtest_grid(s)
    advice_fixtures(s, at)
    check(OUT)


if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        check(OUT)
    else:
        main()
