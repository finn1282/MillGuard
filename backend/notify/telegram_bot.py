"""Telegram bot (long polling, no public URL): /start /en /bm /brief and the Fix now / Schedule / Keep watching buttons.
Token: TELEGRAM_BOT_TOKEN in backend/.env. Run: make bot."""
import logging
import asyncio
import os

from telegram.error import Conflict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from backend.notify import handlers, store

logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)   # httpx logs the bot URL, which contains the token
svc = None


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(handlers.start(update.effective_chat.id))


async def en(update, ctx):
    out = handlers.set_lang(update.effective_chat.id, "en")
    if out:
        await update.message.reply_text(out)


async def bm(update, ctx):
    out = handlers.set_lang(update.effective_chat.id, "ms")
    if out:
        await update.message.reply_text(out)


async def brief(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    out = await asyncio.to_thread(handlers.brief, update.effective_chat.id)
    if out:
        await update.message.reply_text(out)


async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    print("bot: button tap received", q.data.split("|")[-1] if q.data else "", flush=True)   # no ids or tokens
    toast, label = await asyncio.to_thread(handlers.button, q.message.chat.id, q.data)
    await q.answer(toast)
    await q.edit_message_reply_markup(InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data="done")]]))


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
