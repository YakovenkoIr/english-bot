import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# ---------------- ЛОГІ ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- ЗМІННІ ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    raise SystemExit("❌ TELEGRAM_TOKEN не заданий у середовищі")
if not GROQ_API_KEY:
    raise SystemExit("❌ GROQ_API_KEY не заданий у середовищі")

# Groq клієнт
groq_client = Groq(api_key=GROQ_API_KEY)

# Завантаження питань з JSON
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# Словник для збереження прогресу користувачів
user_progress = {}

# ---------------- ФУНКЦІЇ ----------------

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Пройти тест 📖", "Спілкуватися з AI 🤖"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Привіт! Я English Bot.\n"
        "📖 Обери, що хочеш зробити:",
        reply_markup=markup
    )

# Вибір режиму
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "Пройти тест 📖":
        user_progress[user_id] = {"q_index": 0, "score": 0}
        await send_question(update, context)

    elif text == "Спілкуватися з AI 🤖":
        await update.message.reply_text("✍️ Напиши своє питання англійською, і я відповім!")

    elif user_id in user_progress:
        await check_answer(update, context, text)

    else:
        await chat_ai(update, context, text)

# Надсилаємо питання з тесту
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    progress = user_progress[user_id]
    q_index = progress["q_index"]

    if q_index < len(QUESTIONS):
        q = QUESTIONS[q_index]
        keyboard = [[opt] for opt in q["options"]]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(q["question"], reply_markup=markup)
    else:
        score = progress["score"]
        level = "A1 (початковий)"
        if score >= 4:
            level = "B1 (середній)"
        elif score >= 7:
            level = "B2 (вище середнього)"

        await update.message.reply_text(
            f"✅ Тест завершено!\nТвій рівень: {level}\n\nТепер можеш перейти у режим AI 🤖 та практикувати англійську."
        )
        del user_progress[user_id]

# Перевірка відповіді
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, user_answer: str):
    user_id = update.message.from_user.id
    progress = user_progress[user_id]
    q_index = progress["q_index"]

    if q_index < len(QUESTIONS):
        correct = QUESTIONS[q_index]["answer"]
        if user_answer == correct:
            progress["score"] += 1

        progress["q_index"] += 1
        await send_question(update, context)

# Chat з Groq AI
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, user_text: str):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an English teacher. Always reply in English, short and clear."},
                {"role": "user", "content": user_text}
            ]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"AI error: {e}")
        await update.message.reply_text("⚠️ Сталася помилка зі ШІ.")

# ---------------- ЗАПУСК ----------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
