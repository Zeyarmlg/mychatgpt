import os
import openai
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from threading import Thread
from asyncio import run_coroutine_threadsafe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    logger.error("Проверь TELEGRAM_BOT_TOKEN, OPENAI_API_KEY и WEBHOOK_URL")
    exit(1)

openai.api_key = OPENAI_API_KEY

flask_app = Flask(__name__)
application = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я GPT-бот.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_msg}]
        )
        bot_reply = response.choices[0].message["content"]
        await update.message.reply_text(bot_reply)
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        await update.message.reply_text("Ошибка при обращении к OpenAI.")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@flask_app.route("/", methods=["GET"])
def index():
    return "Бот работает!"

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, application.bot)
        future = run_coroutine_threadsafe(application.process_update(update), application.loop)
        future.result(timeout=10)
        return "ok"
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return "error", 500

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

async def main():
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL + "/webhook")
    logger.info(f"Webhook установлен: {WEBHOOK_URL}/webhook")

    # Запускаем Flask в отдельном потоке, чтобы не блокировать event loop
    Thread(target=run_flask, daemon=True).start()

    await application.start()
    await application.updater.start_polling()  # Хотя у тебя webhook, чтобы Telegram Ext не жаловался
    await application.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
