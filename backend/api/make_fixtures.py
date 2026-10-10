"""Snapshot of the real API at the three demo bookmarks plus the real backtest -> contracts/fixtures/*.json.
Fixture mode (MILLGUARD_STUB=1) is the demo backup, so it shows true numbers. Run `make all` first."""
import json
from pathlib import Path

from backend.api.models import (AssetDetail, Assumption, Backtest, Brief, FeedbackOut, Line, Marker, Meta, Robustness)
from backend.engine import playbook
from backend.engine.service import ART, ASSETS, Service

OUT = Path(__file__).resolve().parents[2] / "contracts" / "fixtures"


def write(name, data):
    if isinstance(data, list):
        data = [d.model_dump(mode="json") if hasattr(d, "model_dump") else d for d in data]
    elif hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = Service()
    marks = [m for m in s.markers() if m["kind"] == "bookmark"]
    at = {"quiet": next(m["t"] for m in marks if m["label_en"].startswith("Quiet")),
          "act": next(m["t"] for m in marks if m["label_en"].endswith("act now")),
          "both": next(m["t"] for m in marks if m["label_en"].startswith("Boiler and press"))}
    write("meta", Meta(**s.meta()))
    for key, suffix in (("both", ""), ("act", "_act"), ("quiet", "_quiet")):
        write(f"brief{suffix}", Brief(**s.brief(at[key])))
        write(f"line{suffix}", Line(**s.line(at[key])))
        if key != "quiet":
            for aid, *_ in ASSETS:
                write(f"assets_{aid}{suffix}", AssetDetail(**s.asset(aid, at[key])))
    write("backtest", Backtest(**s.backtest()))
    write("replay_markers", [Marker(**m) for m in s.markers()])
    write("assumptions", [Assumption(**a) for a in s.assumptions()])
    write("robustness", Robustness(**s.robustness()))
    write("faults", playbook.all_guides())
    write("feedback", FeedbackOut(ok=True))
    (OUT / "bookmarks.json").write_text(json.dumps(at, indent=1))
    print("fixtures (real snapshot) written to", OUT, at)


if __name__ == "__main__":
    main()
