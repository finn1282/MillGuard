"""Set or delete the Telegram webhook. Usage: python -m backend.scripts.set_webhook https://<host>/api/telegram/webhook   |   --delete
Needs TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET (backend/.env or the environment). Polling (make bot) and a webhook cannot both be active."""
import sys

import httpx

from backend.notify import store


def main():
    tok = store.token()
    if not tok:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    api = f"https://api.telegram.org/bot{tok}"
    if "--delete" in sys.argv:
        print(httpx.post(f"{api}/deleteWebhook", json={"drop_pending_updates": True}, timeout=20).json().get("description", "?"))
        return
    url = next((a for a in sys.argv[1:] if a.startswith("https://")), None)
    secret = __import__("os").environ.get("TELEGRAM_WEBHOOK_SECRET")
    if not url or not secret:
        raise SystemExit("usage: set_webhook.py https://<host>/api/telegram/webhook   (and TELEGRAM_WEBHOOK_SECRET must be set)")
    r = httpx.post(f"{api}/setWebhook", json={"url": url, "secret_token": secret, "allowed_updates": ["message", "callback_query"]}, timeout=20)
    print(r.json().get("description", "?"))


if __name__ == "__main__":
    main()
