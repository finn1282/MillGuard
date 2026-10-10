"""Slide-ready assets into pitch/: cumulative-cost chart, stress-test table (no noise x3 row), catch-by-class table, numbers.md.
Every number comes from the same Service the API uses (or artifacts it reads). Run after `make all`: make pitch."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backend.engine import cost
from backend.engine.service import ART, Service
from backend.params import val

OUT = Path(__file__).resolve().parents[2] / "pitch"
NAMES = {"run_to_failure": "Fix when it breaks", "fixed_interval": "Fixed schedule", "millguard": "MillGuard alone",
         "schedule_plus_millguard": "Schedule + MillGuard"}
COL = {"run_to_failure": "#b3261e", "fixed_interval": "#8a8a8a", "millguard": "#3b7dd8", "schedule_plus_millguard": "#1a7f4b"}
rm = lambda x: f"RM{x:,.0f}"


def chart(bt):
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=160)
    t = pd.to_datetime([p["t"][:10] for p in bt["timeline"]])
    for k in NAMES:
        y = [p["cost"][k] / 1000 for p in bt["timeline"]]
        ax.plot(t, y, label=f"{NAMES[k]}  {rm(y[-1] * 1000)}", color=COL[k], lw=3 if k == "schedule_plus_millguard" else 2)
    ax.set_ylabel("Cumulative cost (RM thousand)"); ax.set_title("Mill 10, 2025: cumulative cost by policy (unseen mill, base case)")
    ax.grid(alpha=.25); ax.legend(frameon=False, loc="upper left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(OUT / "cumulative_cost.png"); plt.close(fig)


def table_png(path, title, head, rows, widths, note=None, hl=None):
    fig, ax = plt.subplots(figsize=(10, 0.55 * (len(rows) + 2.6)), dpi=160); ax.axis("off")
    tb = ax.table(cellText=rows, colLabels=head, loc="center", cellLoc="center", colWidths=widths)
    tb.auto_set_font_size(False); tb.set_fontsize(11); tb.scale(1, 1.7)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor("#dddddd")
        if r == 0:
            cell.set_facecolor("#1f2a37"); cell.set_text_props(color="white", weight="bold")
        elif hl and hl(r - 1, c, rows):
            cell.set_text_props(color="#b3261e", weight="bold")
    ax.set_title(title, fontsize=13, weight="bold", loc="left")
    if note:
        fig.text(0.01, 0.01, note, fontsize=8, color="#555555")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


SHORT = {"baseline": "No perturbation (reference)", "noise2": "Sensor noise ×2", "miss20": "20% of readings missing",
         "miss40": "40% of readings missing", "drift": "Slow sensor drift (+10% a year)", "wo25": "25% wrong work-order classes"}


def stress(bt):
    rows = [r for r in json.loads((ART / "stress_table.json").read_text()) if r["key"] != "noise3"]
    body = []
    for r in rows:
        sp, fx = r["cost"]["schedule_plus_millguard"], r["cost"]["fixed_interval"]
        body.append([SHORT[r["key"]], f"{r['caught']}/{r['total']}", f"{r['fa_week']:.1f}", rm(sp), rm(fx),
                     rm(abs(fx - sp)) + (" cheaper" if sp < fx else " more costly")])
    table_png(OUT / "stress_test.png", "Stress test on unseen mill 10: same models, same thresholds, no retraining",
              ["Condition", "Failures\ncaught", "False alarms\nper week", "Schedule +\nMillGuard", "Fixed\nschedule", "Schedule + MillGuard\nvs fixed schedule"],
              body, [0.30, 0.10, 0.12, 0.14, 0.13, 0.21],
              note="Sensor noise ×3 is left off this slide (see numbers.md). Reference row = no perturbation.",
              hl=lambda r, c, rows: c == 5 and "more costly" in rows[r][5])
    return rows


def catch(tm):
    body = [[r["fault_class"].replace("_", " "), f"{r['caught']}/{r['total']}",
             f"{100 * r['caught'] / r['total']:.0f}%", f"{r['median_lead_h']:.0f} h" if r["caught"] else "-"] for r in tm["by_fault_class"]]
    tot, got = sum(r["total"] for r in tm["by_fault_class"]), sum(r["caught"] for r in tm["by_fault_class"])
    body.append(["All faults", f"{got}/{tot}", f"{100 * got / tot:.0f}%", ""])
    table_png(OUT / "catch_by_fault_class.png", "Failures caught before they happen, by fault class (unseen mill 10, 2025)",
              ["Fault class", "Caught / total", "Catch rate", "Median warning"], body, [0.34, 0.22, 0.22, 0.22],
              note=f"{tm['false_alarms_per_week']} false alarms per week. Warning periods in the simulator are assumed (params.yaml).")
    (OUT / "catch_by_fault_class.md").write_text("| Fault class | Caught / total | Median warning |\n|---|---|---|\n" +
                                                 "\n".join(f"| {r[0]} | {r[1]} | {r[3]} |" for r in body) + "\n")
    return body


def numbers(s, bt, strict, tm, stress_rows):
    pol = {p["id"]: p for p in bt["policies"]}
    sp = {p["id"]: p for p in strict["policies"]}
    ep = pd.read_parquet(ART / "episodes.parquet")
    prev = ep[ep.outcome == "prevented"]
    lead = [(pd.Timestamp("2025-01-01") + pd.Timedelta(hours=int(r.fail_idx)) - r.t_open) / pd.Timedelta(hours=1) for r in prev.itertuples()]
    met = json.loads((ART / "model_metrics.json").read_text())
    rob, p = s.robustness(), s.p
    bk = {a["key"]: a["value"] for a in s.assumptions() if a["key"].startswith("derived.")}
    roi = json.loads((ART / "roi_table.json").read_text()) if (ART / "roi_table.json").exists() else None
    L = ["# MillGuard: headline numbers and sources", "",
         "All results are from simulated mills (mill 10 is unseen in training) unless marked real. Re-generate: `make all && make pitch`.", "",
         "## Inputs", "| Number | Value | Source |", "|---|---|---|",
         f"| Mill throughput | {val(p, 'economics', 'throughput_tph')} t FFB/h | params.yaml economics.throughput_tph |",
         f"| Oil extraction rate | {val(p, 'economics', 'oer'):.2%} | params.yaml economics.oer (MPOB 2025) |",
         f"| CPO price | RM{val(p, 'economics', 'cpo_price_rm_per_t'):,} /t | params.yaml economics.cpo_price_rm_per_t (MPOB 2025 average) |",
         f"| Value of a mill-hour | RM{s.rm_h:,.0f} | /api/meta rm_per_mill_hour |",
         f"| Share of delayed output truly lost | {val(p, 'economics', 'lost_share'):.0%} (assumed; slider range 20-40%) | params.yaml economics.lost_share |",
         f"| Press breakdown cost (worm wear) | {rm(cost.breakdown_cost(p, 'worm_wear'))} | /api/assumptions derived.breakdown_cost_press |",
         f"| Boiler breakdown cost | {rm(cost.breakdown_cost(p, 'boiler_steam'))} | /api/assumptions derived.breakdown_cost_boiler |",
         "", "## Four policies, mill 10, 2025 (base case)", "| Policy | Cost | Breakdowns | Planned fixes | False alarms | Source |", "|---|---|---|---|---|---|"]
    for k in NAMES:
        L.append(f"| {NAMES[k]} | {rm(pol[k]['total_cost_rm'])} | {pol[k]['breakdowns']} | {pol[k]['planned_stops']} | {pol[k]['false_alarms']} | /api/backtest policies[{k}] |")
    sp_, rtf, fx = pol["schedule_plus_millguard"]["total_cost_rm"], pol["run_to_failure"]["total_cost_rm"], pol["fixed_interval"]["total_cost_rm"]
    L += ["", f"- Schedule + MillGuard saves **{rm(rtf - sp_)}** a year vs fixing when it breaks ({(rtf - sp_) / rtf:.0%}) and **{rm(fx - sp_)}** vs the best fixed schedule ({(fx - sp_) / fx:.0%}). Source: /api/backtest.",
          f"- Strict case (a wrong-class alert never finds the fault, `inspection_accuracy=0`): Schedule + MillGuard {rm(sp['schedule_plus_millguard']['total_cost_rm'])}, still {rm(fx - sp['schedule_plus_millguard']['total_cost_rm'])} below the fixed schedule. Source: /api/backtest?inspection_accuracy=0.",
          "- The fixed schedule is the best interval found by a sweep on training mills (0.5 x mean part life); Schedule + MillGuard uses 0.6 x. Source: backend/artifacts/policy_fit.json.",
          "", "## Detection quality (mill 10, MillGuard alerts)", "| Number | Value | Source |", "|---|---|---|",
          f"| Failures caught before they happened | {sum(r['caught'] for r in tm['by_fault_class'])} of {sum(r['total'] for r in tm['by_fault_class'])} | /api/robustness test_mill |",
          f"| Median warning time | {np.median(lead):.0f} h | backend/artifacts/episodes.parquet (alert open to failure) |",
          f"| False alarms per week | {tm['false_alarms_per_week']} | /api/robustness test_mill.false_alarms_per_week |",
          f"| Press risk model AUC, 72 h / 168 h | {met['press']['mill10_all/72h']['auc']} / {met['press']['mill10_all/168h']['auc']} | backend/artifacts/model_metrics.json |",
          f"| Boiler risk model AUC, 24 h | {met['boiler']['mill10_all/24h']['auc']} | backend/artifacts/model_metrics.json |",
          "", "## Real-data checks (honest)", "| Test | Result | Source |", "|---|---|---|",
          f"| MetroPT-3 real compressor, 4 air-leak failures | {rob['caught']} of {rob['failures_total']} flagged before they started; {rob['false_alarms_per_week']} false alarms per week | /api/robustness |"]
    for e in rob["extra"]:
        if e["dataset"].startswith("Real coal"):
            L.append(f"| Real coal-fired boiler, steam excursions 10-15 min ahead | {e['events_caught']} of {e['events_total']} caught, precision {e['precision_pct']}%, {e['false_alarms_per_day']} false alarms per day. No usable skill (AUC 0.54). | /api/robustness extra[] |")
    L += ["", "## Stress test (mill 10, no retraining, thresholds unchanged)", "| Condition | Caught | Schedule + MillGuard | Fixed schedule |", "|---|---|---|---|"]
    for r in stress_rows:
        L.append(f"| {r['label']} | {r['caught']}/{r['total']} | {rm(r['cost']['schedule_plus_millguard'])} | {rm(r['cost']['fixed_interval'])} |")
    n3 = next(r for r in json.loads((ART / "stress_table.json").read_text()) if r["key"] == "noise3")
    L += ["", "**Why noise ×3 is not on the slide:** at ×3 the model catches only "
          f"{n3['caught']} of {n3['total']} failures and mostly stops alerting, so its cost ({rm(n3['cost']['schedule_plus_millguard'])}) comes from the fixed schedule underneath, "
          "not from MillGuard. It is in /api/robustness extra[] and backend/artifacts/stress_table.json if a judge asks. "
          "Noise ×2 (worse than fixed) is on the slide on purpose: MillGuard needs reasonably clean sensors or retraining on the mill's own data.",
          "", "## Assumptions to say out loud", "- Mills are simulated; warning periods before failure (worm 300 h, gearbox 400 h, bearing 150 h, cone 200 h) are assumed.",
          "- Crew inspection finds the real fault 50% of the time when the predicted class is wrong (`inspection_finds_wrong_class`; slider = `inspection_accuracy`).",
          "- Alert threshold uses a false-alarm multiplier fitted on training mills only; nothing is tuned on mill 10.",
          "- Press fault fingerprints use the machine's own previous 30 days as 'normal'."]
    (OUT / "numbers.md").write_text("\n".join(L) + "\n")


def main():
    OUT.mkdir(exist_ok=True)
    s = Service()
    bt, strict = s.backtest(), s.backtest(inspection_accuracy=0.0)
    tm = s.robustness()["test_mill"]
    chart(bt)
    rows = stress(bt)
    catch(tm)
    numbers(s, bt, strict, tm, rows)
    print("wrote", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
