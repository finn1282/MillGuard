"""Bot behaviour shared by the polling bot (python-telegram-bot) and the webhook (plain HTTPS): /start /en /bm /brief and the
Fix now / Schedule / Keep watching buttons. Pure functions over backend/state.py; the callers do the sending."""
from backend.api.feedback import record
from backend.api.models import FeedbackIn
from backend.engine import text
from backend.notify import messages, send, store

_default = None


def default_service():
    global _default
    if _default is None:
        from backend.engine.service import Service
        _default = Service()
    return _default


def lang_of(chat):
    return store.subscribers().get(str(chat), {}).get("lang", "en")


def allowed(chat):
    a = store.allowed()
    return not a or str(chat) in a


def start(chat):
    if not allowed(chat):
        return text.NOTIFY["not_allowed"][0]
    s = store.set_sub(chat)
    return text.NOTIFY["start"][messages.LANG[s["lang"]]]


def set_lang(chat, lang):
    if not allowed(chat):
        return None
    store.set_sub(chat, lang)
    return text.NOTIFY["lang_set"][messages.LANG[lang]]


def brief(chat, svc=None):
    """The current brief: the live session's scenario at live_at, else the replay clock."""
    if not allowed(chat):
        return None
    from backend.gateway import live
    sv, at = live.current(svc or default_service(), store.last_at())
    return messages.brief_text(sv.brief(at), lang_of(chat))


def button(chat, data, svc=None):
    """data = 'fb|<action id>|<decision>'. -> (toast, label shown on the pressed button). Schedule also tells the whole group."""
    _, action_id, decision = data.split("|")
    record(FeedbackIn(action_id=action_id, decision=decision), source="telegram")   # same path as POST /api/feedback
    lang = lang_of(chat)
    if decision == "schedule_next_stop":   # close the loop: tell the group
        from backend.gateway import live
        sv, at = live.current(svc or default_service(), store.last_at())
        action = next((x for x in sv.brief(at)["actions"] if x["id"] == action_id), None)
        if action:
            send.schedule_message(action)
    choice = text.NOTIFY["buttons"][decision][messages.LANG[lang]]
    return text.NOTIFY["recorded"][messages.LANG[lang]].format(choice=choice), "✔ " + choice


def handle_update(update, svc=None):
    """Webhook entry: one Telegram update (dict). Replies over HTTPS."""
    cb = update.get("callback_query")
    if cb:
        data = cb.get("data") or ""
        if data.startswith("fb|") and len(data.split("|")) == 3:
            chat = cb["message"]["chat"]["id"]
            toast, label = button(chat, data, svc)
            send._post("answerCallbackQuery", callback_query_id=cb["id"], text=toast)
            send._post("editMessageReplyMarkup", chat_id=chat, message_id=cb["message"]["message_id"],
                       reply_markup={"inline_keyboard": [[{"text": label, "callback_data": "done"}]]})
        else:
            send._post("answerCallbackQuery", callback_query_id=cb["id"])
        return
    msg = update.get("message") or {}
    cmd = (msg.get("text") or "").split()[0].split("@")[0].lower() if msg.get("text") else ""
    chat = (msg.get("chat") or {}).get("id")
    if chat is None:
        return
    reply = {"/start": lambda: start(chat), "/en": lambda: set_lang(chat, "en"), "/bm": lambda: set_lang(chat, "ms"),
             "/brief": lambda: brief(chat, svc)}.get(cmd)
    out = reply() if reply else None
    if out:
        send._post("sendMessage", chat_id=chat, text=out)
