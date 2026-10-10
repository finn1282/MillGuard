"""Telegram bot (long polling, no public URL): /start /en /bm /brief and the Fix now / Schedule / Keep watching buttons.
Token: TELEGRAM_BOT_TOKEN in backend/.env. Run: make bot."""
import logging
import asyncio
import os

from telegram.error import Conflict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from backend.api.feedback import record
from backend.api.models import FeedbackIn
from backend.engine import text
from backend.notify import send
from backend.notify import messages, store

logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)   # httpx logs the bot URL, which contains the token
svc = None


def _service():
    global svc
    if svc is None:
        from backend.engine.service import Service
        svc = Service()
    return svc


def _lang(chat):
    return store.subscribers().get(str(chat), {}).get("lang", "en")


def _ok(chat):
    a = store.allowed()
    return not a or str(chat) in a


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    if not _ok(chat):
        return await update.message.reply_text(text.NOTIFY["not_allowed"][0])
    s = store.set_sub(chat)
    await update.message.reply_text(text.NOTIFY["start"][messages.LANG[s["lang"]]])


async def set_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE, lang):
    chat = update.effective_chat.id
    if _ok(chat):
        store.set_sub(chat, lang)
        await update.message.reply_text(text.NOTIFY["lang_set"][messages.LANG[lang]])


async def en(update, ctx):
    await set_lang(update, ctx, "en")


async def bm(update, ctx):
    await set_lang(update, ctx, "ms")


async def brief(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    if _ok(chat):
        await update.message.reply_text(messages.brief_text(_service().brief(store.last_at()), _lang(chat)))


async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    print("bot: button tap received", q.data.split("|")[-1] if q.data else "", flush=True)   # no ids or tokens
    _, action_id, decision = q.data.split("|")
    record(FeedbackIn(action_id=action_id, decision=decision), source="telegram")   # same path as POST /api/feedback
    lang = _lang(q.message.chat.id)
    choice = text.NOTIFY["buttons"][decision][messages.LANG[lang]]
    if decision == "schedule_next_stop":   # close the loop: tell the whole group
        action = next((x for x in _service().brief(store.last_at())["actions"] if x["id"] == action_id), None)
        if action:
            await asyncio.to_thread(send.schedule_message, action)
    await q.answer(text.NOTIFY["recorded"][messages.LANG[lang]].format(choice=choice))
    await q.edit_message_reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton("✔ " + choice, callback_data="done")]]))


async def on_error(update, ctx: ContextTypes.DEFAULT_TYPE):
    if isinstance(ctx.error, Conflict):   # another poller on the same token would silently take our taps
        print("Another MillGuard bot is already running with this token; stop it.", flush=True)
        os._exit(4)
    print("bot: error", type(ctx.error).__name__, flush=True)


async def other(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    print("bot: other callback received", flush=True)
    await update.callback_query.answer()


def main():
    tok = store.token()
    if not tok:
        print("TELEGRAM_BOT_TOKEN is not set in backend/.env; the bot is disabled.")
        raise SystemExit(3)
    app = Application.builder().token(tok).build()
    for name, fn in (("start", start), ("en", en), ("bm", bm), ("brief", brief)):
        app.add_handler(CommandHandler(name, fn))
    app.add_handler(CallbackQueryHandler(button, pattern=r"^fb\|"))
    app.add_error_handler(on_error)
    app.add_handler(CallbackQueryHandler(other, pattern=r"^(?!fb\|)"))
    print("MillGuard bot polling (Ctrl+C to stop)", flush=True)
    app.run_polling(bootstrap_retries=-1)   # keep retrying if the network is down at start


if __name__ == "__main__":
    main()
