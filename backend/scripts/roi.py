"""Low/base/high table from params.yaml, using the same backtest as the app (mill 10, full year)."""
import copy
import json

from backend.params import load
from backend.run_all import ART, evaluate

CASES = {   # cpo RM/t, share of delayed output truly lost, false-alarm cost multiplier, retrofit kit RM
    "low": dict(cpo=3800.0, lost=0.20, fa=2.0, kit=25000),
    "base": dict(cpo=4292.5, lost=0.30, fa=1.0, kit=15000),
    "high": dict(cpo=5000.0, lost=0.40, fa=1.0, kit=10000),
}


def main():
    base = load()
    fit = json.loads((ART / "policy_fit.json").read_text())
    print(f"{'case':5s} {'CPO':>6s} {'lost':>5s} {'run-to-failure':>15s} {'fixed interval':>15s} {'MillGuard':>10s} {'Sched+MG':>10s} "
          f"{'Sched+MG vs RTF':>13s} {'Sched+MG vs fixed':>15s} {'payback (mo)':>13s}")
    for name, c in CASES.items():
        p = copy.deepcopy(base)
        p["economics"]["lost_share"]["value"] = c["lost"]
        p["economics"]["false_alarm_cost_rm"]["value"] *= c["fa"]
        _, _, _, pols, _ = evaluate(p, fit, cpo=c["cpo"])
        t = {r["id"]: r["total_cost_rm"] for r in pols}
        s_rtf, s_fix = t["run_to_failure"] - t["schedule_plus_millguard"], t["fixed_interval"] - t["schedule_plus_millguard"]
        pay = 12 * c["kit"] / s_rtf if s_rtf > 0 else float("inf")
        print(f"{name:5s} {c['cpo']:6,.0f} {c['lost']:5.0%} {t['run_to_failure']:15,d} {t['fixed_interval']:15,d} "
              f"{t['millguard']:10,d} {t['schedule_plus_millguard']:10,d} {s_rtf:13,d} {s_fix:15,d} {pay:13.1f}")


if __name__ == "__main__":
    main()
