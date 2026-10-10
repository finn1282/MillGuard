"""Gitignored state for the bot: subscribers, sent alert ids, replay clock. Lives in backend/data/."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SUBS, SENT, STATE = DATA / "subscribers.json", DATA / "notify_sent.json", DATA / "notify_state.json"


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


def _read(f, default):
    try:
        return json.loads(f.read_text())
    except (OSError, ValueError):
        return default


def _write(f, obj):
    DATA.mkdir(exist_ok=True)
    f.write_text(json.dumps(obj))


def subscribers():
    return _read(SUBS, {})            # chat_id -> {"lang": "en"|"ms"}


def set_sub(chat_id, lang=None):
    s = subscribers()
    s.setdefault(str(chat_id), {"lang": "en"})
    if lang:
        s[str(chat_id)]["lang"] = lang
    _write(SUBS, s)
    return s[str(chat_id)]


def sent_before(chat_id, alert_id):
    return alert_id in _read(SENT, {}).get(str(chat_id), [])


def mark_sent(chat_id, alert_id):
    d = _read(SENT, {})
    d.setdefault(str(chat_id), []).append(alert_id)
    _write(SENT, d)


def shift_sent(shift_key):
    """Alerts already sent in this replay shift (all chats count once per alert id)."""
    return _read(STATE, {}).get("shift", {}).get(shift_key, [])


def mark_shift(shift_key, alert_id):
    st = _read(STATE, {})
    ids = st.setdefault("shift", {}).setdefault(shift_key, [])
    if alert_id not in ids:
        ids.append(alert_id)
    _write(STATE, st)


def last_at():
    return _read(STATE, {}).get("at")


def set_last_at(at):
    st = _read(STATE, {})
    st["at"] = at
    _write(STATE, st)
