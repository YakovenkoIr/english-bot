import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import os
import openai

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------
# API KEYS (заміни своїми!)
# ----------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# ----------------------------
# Завантажуємо питання з JSON
# ----------------------------
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# ----------------------------
# СТАРТОВЕ МЕНЮ
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Пройти тест", callback_data="start_test")],
        [InlineKeyboardButton("🤖 Почати спілкування з AI", callback_data="start_ai")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привіт! Оберіть дію:", reply_markup=reply_markup)

# ----------------------------
# ОБРОБКА КНОПОК
# ----------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "start_test":
        context.user_data["score"] = 0
        context.user_data["q_index"] = 0
        await ask_question(query, context)

    elif query.data == "start_ai":
        await query.message.reply_text("✍️ Тепер пишіть англійською, я буду відповідати.")

# ----------------------------
# ТЕСТ
# ----------------------------
async def ask_question(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data.get("q_index", 0)

    if q_index < len(QUESTIONS):
        q = QUESTIONS[q_index]
        keyboard = [[InlineKeyboardButton(opt, callback_data=f"answer:{opt}")]
                    for opt in q["options"]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if hasattr(update_or_query, "message"):
            await update_or_query.message.reply_text(q["question"], reply_markup=reply_markup)
        else:
            await update_or_query.message.reply_text(q["question"], reply_markup=reply_markup)
    else:
        score = context.user_data["score"]
        level = "A1 (початковий)" if score <= 2 else "A2 (базовий)" if score <= 4 else "B1 (середній)"
        await update_or_query.message.reply_text(
            f"✅ Тест завершено!\nВаш рівень: {level}\n\n"
            "Раджу продовжити у спілкуванні з AI 👉 натисніть /start та виберіть AI."
        )

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("answer:"):
        selected = query.data.split(":")[1]
        q_index = context.user_data.get("q_index", 0)
        correct = QUESTIONS[q_index]["answer"]

        if selected == correct:
            context.user_data["score"] += 1

        context.user_data["q_index"] = q_index + 1
        await ask_question(query, context)

# ----------------------------
# AI CHAT
# ----------------------------
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # або groq-mixtral
            messages=[
                {"role": "system", "content": "You are a friendly English tutor."},
                {"role": "user", "content": user_text}
            ]
        )
        reply_text = response["choices"][0]["message"]["content"]
        await update.message.reply_text(reply_text)

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        await update.message.reply_text("⚠️ Помилка при спілкуванні з AI.")

# ----------------------------
# MAIN
# ----------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(start_test|start_ai)$"))
    app.add_handler(CallbackQueryHandler(answer_handler, pattern="^answer:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    app.run_polling()

if __name__ == "__main__":
    main()

