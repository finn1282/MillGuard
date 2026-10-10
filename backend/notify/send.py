"""Send replay-clock alerts and briefs to subscribers (plain HTTPS to the Telegram Bot API; no event loop needed)."""
import httpx

from backend.engine import decide
import pandas as pd

from backend.notify import messages, store

BUDGET = 5   # per shift, same as the app's alert budget


def _post(method, **payload):
    r = httpx.post(f"https://api.telegram.org/bot{store.token()}/{method}", json=payload, timeout=20)
    return r.json().get("ok", False)


def status():
    return dict(enabled=store.token() is not None, channel="telegram", subscribers=len(store.subscribers()))


def _shift_key(at):
    return f"shift{decide.shift_id(pd.Timestamp(at).tz_localize(None))}"


def schedule(svc, at, action_id, record_feedback=True):
    """Tell every subscriber the supervisor scheduled this action (no dedupe, no shift budget). -> (ok, sent); None if no such action."""
    brief = svc.brief(at)
    a = next((x for x in brief["actions"] if x["id"] == action_id), None)
    if a is None:
        return None
    if record_feedback:
        from backend.api.feedback import record
        from backend.api.models import FeedbackIn
        record(FeedbackIn(action_id=action_id, decision="schedule_next_stop"))
    return schedule_message(a)


def schedule_message(a):
    if store.token() is None:
        return False, 0
    sent = sum(_post("sendMessage", chat_id=chat, text=messages.scheduled_text(a, s["lang"])) for chat, s in store.subscribers().items())
    return True, sent


def notify(svc, at, kind):
    """-> (ok, sent). kind 'alert': each current action once per chat, at most 5 per shift. kind 'brief': the shift brief."""
    if store.token() is None:
        return False, 0
    subs = store.subscribers()
    if not subs:
        print(store.NO_SUBS)
    brief = svc.brief(at)
    store.set_last_at(brief["at"])
    sent = 0
    if kind == "brief":
        for chat, s in subs.items():
            sent += _post("sendMessage", chat_id=chat, text=messages.brief_text(brief, s["lang"]))
        return True, sent
    key = _shift_key(brief["at"])
    for a in brief["actions"]:
        already = store.shift_sent(key)
        if a["id"] not in already and len(already) >= BUDGET:
            continue
        for chat, s in subs.items():
            if store.sent_before(chat, a["id"]):
                continue
            ok = _post("sendMessage", chat_id=chat, text=messages.alert_text(a, s["lang"]),
                       reply_markup={"inline_keyboard": messages.keyboard(a["id"], s["lang"])})
            if ok:
                store.mark_sent(chat, a["id"]); sent += 1
        store.mark_shift(key, a["id"])
    return True, sent
