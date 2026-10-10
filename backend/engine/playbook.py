"""Static fault playbook (text.FAULTS) turned into the v1.5 contract objects."""
from backend.api.models import (Alternative, Diagnosis, FaultGuide, FingerprintCheck, FixPlan, Part, Sign)
from backend.engine import text


def label(signal):
    return text.SIGNAL_LABEL.get(signal) or text.SERIES[signal][:2]


def guide(fc):
    f = text.FAULTS[fc]
    return FaultGuide(fault_class=fc, name_en=f["name"][0], name_ms=f["name"][1], what_en=f["plain"][0],
                      what_ms=f["plain"][1], why_en=f["why"][0], why_ms=f["why"][1],
                      signs=[Sign(signal=s, label_en=label(s)[0], label_ms=label(s)[1], expected=e) for s, e in f["signs"]],
                      fix_steps_en=f["steps"][0], fix_steps_ms=f["steps"][1], typical_downtime_h=f["downtime"],
                      typical_cost_rm=f["cost"], onset=f["onset"])


def all_guides():
    return [guide(fc) for fc in text.FAULTS if fc != "unknown"] + [guide("unknown")]


def fix_plan(fc, best_window):
    f = text.FAULTS[fc]
    return FixPlan(title_en=text.FIX_PHRASE[fc][0], title_ms=text.FIX_PHRASE[fc][1], steps_en=f["steps"][0],
                   steps_ms=f["steps"][1], parts=[Part(name_en=n[0], name_ms=n[1], qty=q) for n, q in f["parts"]],
                   crew=f["crew"], est_hours=f["hours"], needs_stop=f["needs_stop"], best_window=best_window)


def diagnosis(fc, confidence, alternatives, checks):
    f = text.FAULTS[fc]
    return Diagnosis(fault_class=fc, name_en=f["name"][0], name_ms=f["name"][1], confidence_pct=confidence,
                     plain_en=f["plain"][0], plain_ms=f["plain"][1],
                     alternatives=[Alternative(fault_class=a, confidence_pct=c) for a, c in alternatives],
                     fingerprint=checks)


def check(signal, expected, observed_en, observed_ms, matches):
    en, ms = label(signal)
    return FingerprintCheck(signal=signal, label_en=en, label_ms=ms, expected=expected,
                            observed_en=observed_en, observed_ms=observed_ms, matches=matches)
