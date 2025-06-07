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

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://your-app.onrender.com

if not TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    logger.error("Проверь TELEGRAM_BOT_TOKEN, OPENAI_API_KEY и WEBHOOK_URL в переменных окружения.")
    exit(1)

openai.api_key = OPENAI_API_KEY

# Flask-приложение
flask_app = Flask(__name__)

# Telegram-приложение
application = ApplicationBuilder().token(TOKEN).build()

# --- Хендлеры ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start вызван от пользователя: {update.effective_user.id}")
    await update.message.reply_text("Привет! Я GPT-бот, напиши мне что-нибудь.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        logger.warning("Получено сообщение без текста.")
        return

    user_msg = update.message.text
    logger.info(f"Сообщение от пользователя: {user_msg}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_msg}]
        )
        bot_reply = response.choices[0].message["content"]
        await update.message.reply_text(bot_reply)
    except Exception as e:
        logger.error(f"Ошибка OpenAI: {e}")
        await update.message.reply_text("Произошла ошибка при обращении к GPT 😢")

# --- Добавляем хендлеры ---
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Роуты Flask ---
@flask_app.route("/", methods=["GET"])
def index():
    return "Бот работает!"

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_json = request.get_json(force=True)
        logger.info(f"Получен update от Telegram: {update_json}")
        update = Update.de_json(update_json, application.bot)
        asyncio.create_task(application.process_update(update))  # ✅ Ключевая строка
        return "ok"
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return "error", 500

# --- Запуск Telegram и Flask ---
async def run_bot():
    await application.initialize()
    await application.bot.set_webhook(url=WEBHOOK_URL + "/webhook")
    await application.start()
    logger.info("Бот запущен и webhook установлен.")

def start_flask():
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Flask-сервер запущен на порту {port}")
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=lambda: asyncio.run(run_bot())).start()
    start_flask()
