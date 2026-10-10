"""Print the 3 demo bookmarks with each card's key numbers, and the 4-policy table at default and strict inspection."""
import json

from backend.engine.service import ART, Service


def main():
    s = Service()
    marks = [m for m in json.loads((ART / "markers.json").read_text()) if m["kind"] == "bookmark"]
    for m in marks:
        b, line = s.brief(m["t"]), s.line(m["t"])
        print(f"\n{m['t']}  {m['label_en']}   watching {b['watching_count']}  suppressed {b['suppressed_count']}  actions {len(b['actions'])}")
        for a in b["actions"]:
            d = s.asset(a["asset_id"], m["t"])
            fp = d["diagnosis"]["fingerprint"] if d["diagnosis"] else []
            print(f"  {a['asset_name']:9s} {a['fault_class']:13s} {a['recommendation']:18s} risk {a['risk_pct']:.0f}%  window {a['horizon_h']} h  "
                  f"at_risk RM{a['rm_at_risk']:,}  cost RM{a['rm_cost_to_act']:,}  saved RM{a['rm_saved_if_acted']:,}  "
                  f"fingerprint {sum(c['matches'] for c in fp)}/{len(fp)}")
    for acc in (None, 0.0):
        bt = s.backtest(inspection_accuracy=acc)
        print(f"\n4 policies, inspection_accuracy {'default 0.5' if acc is None else acc}:")
        for r in bt["policies"]:
            print(f"  {r['id']:24s} RM {r['total_cost_rm']:>9,}  breakdowns {r['breakdowns']:3d}  planned {r['planned_stops']:3d}  "
                  f"false alarms {r['false_alarms']:3d}  downtime {r['downtime_h']:.0f} h")


if __name__ == "__main__":
    main()
