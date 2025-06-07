import os
import openai
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import asyncio
from threading import Thread

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://your-service.onrender.com

openai.api_key = OPENAI_API_KEY

# Telegram bot application
application = ApplicationBuilder().token(TOKEN).build()

# Flask app
flask_app = Flask(__name__)

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я GPT-бот, напиши мне что-нибудь.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    response = openai.ChatCompletion.create(
        model="gpt-4",  # или gpt-3.5-turbo
        messages=[{"role": "user", "content": user_msg}]
    )
    await update.message.reply_text(response.choices[0].message["content"])

# --- Привязка обработчиков ---
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Flask routes ---
@flask_app.route("/", methods=["GET"])
def index():
    return "Бот работает!"

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

# --- Запуск ---
async def run_bot():
    await application.initialize()
    # Устанавливаем webhook в Telegram (одноразово при запуске)
    await application.bot.set_webhook(url=WEBHOOK_URL + "/webhook")
    await application.start()
    # polling не нужен при вебхуке, поэтому не вызываем start_polling()

def start_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    # Запускаем Telegram Application в отдельном потоке
    Thread(target=lambda: asyncio.run(run_bot())).start()
    # Запускаем Flask сервер в основном потоке
    start_flask()
