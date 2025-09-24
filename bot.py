import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from groq import Groq

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Завантаження API ключів
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# Завантаження питань з файлу
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# СТАНИ
CHOOSING, TEST, CHAT = range(3)

# Словник для збереження відповідей
user_data = {}

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📝 Пройти тест")], [KeyboardButton("🤖 Спілкування з AI")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привіт! 👋 Обери дію:", reply_markup=reply_markup)
    return CHOOSING

# Обробка вибору
async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📝 Пройти тест":
        context.user_data["level"] = "A1"  # Починаємо з A1
        context.user_data["index"] = 0
        context.user_data["score"] = 0
        return await ask_question(update, context)

    elif text == "🤖 Спілкування з AI":
        await update.message.reply_text("Тепер ти можеш спілкуватися англійською з AI 🤖")
        return CHAT

# Задаємо питання
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = context.user_data["level"]
    index = context.user_data["index"]

    if index < len(QUESTIONS[level]):
        q = QUESTIONS[level][index]
        options = [[KeyboardButton(opt)] for opt in q["options"]]
        reply_markup = ReplyKeyboardMarkup(options, resize_keyboard=True)
        await update.message.reply_text(q["question"], reply_markup=reply_markup)
        return TEST
    else:
        # Якщо питання закінчилися — показуємо результат
        score = context.user_data["score"]
        total = len(QUESTIONS[level])
        result_text = f"Тест рівня {level} завершено ✅\nПравильних відповідей: {score}/{total}\n"

        if score == total:
            if level == "A1":
                context.user_data["level"] = "A2"
                context.user_data["index"] = 0
                return await ask_question(update, context)
            elif level == "A2":
                context.user_data["level"] = "B1"
                context.user_data["index"] = 0
                return await ask_question(update, context)
            else:
                await update.message.reply_text(result_text + "\nВаш рівень — **B1** 🎉\nРекомендуємо перейти до спілкування з AI 🤖")
        else:
            await update.message.reply_text(result_text + f"\nВаш рівень — **{level}** 📘\nРекомендуємо перейти до спілкування з AI 🤖")

        return CHOOSING

# Обробка відповідей на тест
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = context.user_data["level"]
    index = context.user_data["index"]
    q = QUESTIONS[level][index]

    if update.message.text == q["answer"]:
        context.user_data["score"] += 1

    context.user_data["index"] += 1
    return await ask_question(update, context)

# AI чат
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are an English teacher. Always reply in English."},
            {"role": "user", "content": user_input},
        ],
    )

    bot_reply = response.choices[0].message.content
    await update.message.reply_text(bot_reply)

# Основна функція
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose)],
            TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
            CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
