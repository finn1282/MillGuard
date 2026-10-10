"""Bot state (subscribers, sent alert ids, replay clock) through backend/state.py; token and allowed chats from backend/.env."""
import os
from pathlib import Path

from backend import state

ROOT = Path(__file__).resolve().parents[1]


def load_env():
    """Read backend/.env into os.environ (never printed, never committed)."""
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def token():
    load_env()
    return os.environ.get("TELEGRAM_BOT_TOKEN") or None


def allowed():
    load_env()
    raw = os.environ.get("TELEGRAM_ALLOWED_CHATS", "")
    return {c.strip() for c in raw.split(",") if c.strip()}


def subscribers():
    return state.db().get("subs") or {}   # chat_id -> {"lang": "en"|"ms"}


def set_sub(chat_id, lang=None):
    s = subscribers()
    s.setdefault(str(chat_id), {"lang": "en"})
    if lang:
        s[str(chat_id)]["lang"] = lang
    state.db().set("subs", s)
    return s[str(chat_id)]


def sent_before(chat_id, alert_id):
    return alert_id in state.db().members(f"sent:{chat_id}")


def mark_sent(chat_id, alert_id):
    state.db().add(f"sent:{chat_id}", alert_id)


def shift_sent(shift_key):
    """Alerts already sent in this replay shift (all chats count once per alert id)."""
    return state.db().members(f"shift:{shift_key}")


def mark_shift(shift_key, alert_id):
    state.db().add(f"shift:{shift_key}", alert_id)


def last_at():
    return state.db().get("last_at")


def set_last_at(at):
    state.db().set("last_at", at)
