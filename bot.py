import os
import openai
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Вида: https://your-service.onrender.com

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

# --- Flask route для webhook ---
@flask_app.route("/")
def index():
    return "Бот работает!"

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

# --- Запуск ---
if __name__ == "__main__":
    import asyncio
    from threading import Thread

    # Фоновый запуск Telegram Application
    async def run_bot():
        await application.initialize()
        await application.start()
        await application.updater.start_polling()  # неважно, не будет использоваться
        # Не вызываем application.run_webhook()!
    
    # Запускаем Telegram-приложение в отдельном потоке
    Thread(target=lambda: asyncio.run(run_bot())).start()

    # Flask сервер (порт подхватывается от Render)
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
