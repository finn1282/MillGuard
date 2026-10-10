"""Telegram message text, built from the same text.py templates and Service numbers as the app."""
import pandas as pd

from backend.engine import text

LANG = {"en": 0, "ms": 1}


def _t(key, lang, **kw):
    return text.NOTIFY[key][LANG[lang]].format(**kw)


def asset_name(name, lang):
    return name if lang == "en" else text.name_ms(name)


def _rec(a, lang):
    if a["recommendation"] == "fix_now":
        return text.NOTIFY["rec_fix_now"][LANG[lang]]
    return text.NOTIFY["rec_schedule"][LANG[lang]].format(deadline=a[f"deadline_label_{lang}"])


def alert_text(a, lang):
    fault = text.FAULT_LABEL[a["fault_class"]][LANG[lang]]
    return _t("alert", lang, asset=asset_name(a["asset_name"], lang), fault=fault.capitalize(), risk=round(a["risk_pct"]),
              window=a[f"window_label_{lang}"], rec=_rec(a, lang), saved=a["rm_saved_if_acted"],
              reason=a["reasons"][0][f"text_{lang}"], deadline=a[f"deadline_label_{lang}"])


def scheduled_text(a, lang):
    return _t("scheduled", lang, asset=asset_name(a["asset_name"], lang), fault=text.FAULT_LABEL[a["fault_class"]][LANG[lang]],
              deadline=a[f"deadline_label_{lang}"], saved=a["rm_saved_if_acted"])


def brief_text(b, lang):
    shift = text.NOTIFY["shift"][b["shift"]][LANG[lang]]
    clock = pd.Timestamp(b["at"]).strftime("%d/%m %H:%M")
    head = _t("brief_head", lang, shift=shift, clock=clock)
    if not b["actions"]:
        return head + "\n" + _t("brief_none", lang, when=text.NOTIFY["when"][b["shift"]][LANG[lang]], w=b["watching_count"])
    lines = [_t("brief_line", lang, i=i, asset=asset_name(a["asset_name"], lang),
                fault=text.FAULT_LABEL[a["fault_class"]][LANG[lang]].capitalize(), risk=round(a["risk_pct"]),
                rec=_rec(a, lang), saved=a["rm_saved_if_acted"]) for i, a in enumerate(b["actions"], 1)]
    return "\n".join([head, *lines, _t("brief_total", lang, total=b["rm_protected_total"])])


def keyboard(action_id, lang):
    """Inline buttons; callback data is 'fb|<action id>|<decision>' (well under Telegram's 64-byte limit)."""
    return [[{"text": text.NOTIFY["buttons"][d][LANG[lang]], "callback_data": f"fb|{action_id}|{d}"}]
            for d in ("fix_now", "schedule_next_stop", "monitor")]
