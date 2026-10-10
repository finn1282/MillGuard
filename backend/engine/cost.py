"""Cost engine. All inputs come from params.yaml; sliders override via kwargs."""
from backend.params import load, val

BOILER_CLASSES = {"boiler_steam", "boiler_water"}


def asset_type(fault_class: str) -> str:
    return "boiler" if fault_class in BOILER_CLASSES else "press"


def rm_per_mill_hour(p, cpo_price=None) -> float:
    price = cpo_price or val(p, "economics", "cpo_price_rm_per_t")
    return val(p, "economics", "throughput_tph") * val(p, "economics", "oer") * price


def downtime_h(p, atype: str) -> float:
    key = "unplanned_boiler_stop_h" if atype == "boiler" else "unplanned_press_stop_h"
    return val(p, "economics", key)


def criticality(p, atype: str) -> float:
    return val(p, "economics", "criticality_boiler" if atype == "boiler" else "criticality_press")


def lost_cpo_t(p, atype: str, hours=None) -> float:
    h = downtime_h(p, atype) if hours is None else hours
    t = val(p, "economics", "throughput_tph") * criticality(p, atype) * h
    return t * val(p, "economics", "oer") * val(p, "economics", "lost_share")


def breakdown_cost(p, fault_class: str, cpo_price=None, miss_mult=1.0) -> int:
    at = asset_type(fault_class)
    lost = (downtime_h(p, at) * rm_per_mill_hour(p, cpo_price) * criticality(p, at)
            * val(p, "economics", "lost_share"))
    parts = p["repair_cost_rm"][fault_class]["value"] * val(p, "economics", "unplanned_repair_multiplier")
    return round((lost + parts) * miss_mult)


def planned_cost(p, fault_class: str) -> int:
    return round(p["repair_cost_rm"][fault_class]["value"])


def false_alarm_cost(p) -> int:
    return round(val(p, "economics", "false_alarm_cost_rm"))


def saved_if_acted(p, fault_class: str, cpo_price=None, miss_mult=1.0) -> int:
    return breakdown_cost(p, fault_class, cpo_price, miss_mult) - planned_cost(p, fault_class)
