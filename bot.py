import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 🔑 Встав сюди свій токен від BotFather
TELEGRAM_TOKEN = "8204640997:AAF4GPpv6FDyBFuG2BE86O1KjQhR9f4en1g"

# Завантажуємо питання з JSON
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# Стан користувачів (хто що проходить)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["A1", "A2"], ["B1", "B2"], ["C1"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Привіт! Обери рівень тесту з англійської:",
        reply_markup=markup
    )

async def choose_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    level = update.message.text.strip().upper()

    if level not in QUESTIONS:
        await update.message.reply_text("❌ Невірний вибір. Спробуй ще раз.")
        return

    user_data[user_id] = {"level": level, "score": 0, "current": 0}
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    level = user_data[user_id]["level"]
    current = user_data[user_id]["current"]

    if current < len(QUESTIONS[level]):
        q = QUESTIONS[level][current]
        reply_keyboard = [[opt] for opt in q["options"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(q["question"], reply_markup=markup)
    else:
        score = user_data[user_id]["score"]
        total = len(QUESTIONS[level])
        await update.message.reply_text(f"✅ Тест завершено! Твій результат: {score}/{total}")
        del user_data[user_id]

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        await update.message.reply_text("Напиши /start, щоб почати новий тест.")
        return

    level = user_data[user_id]["level"]
    current = user_data[user_id]["current"]
    answer = update.message.text
    correct = QUESTIONS[level][current]["answer"]

    if answer == correct:
        user_data[user_id]["score"] += 1
        await update.message.reply_text("✅ Правильно!")
    else:
        await update.message.reply_text(f"❌ Неправильно. Правильна відповідь: {correct}")

    user_data[user_id]["current"] += 1
    await ask_question(update, context)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(A1|A2|B1|B2|C1)$"), choose_level))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))
    print("✅ English Level Bot запущений...")
    app.run_polling()

if __name__ == "__main__":
    main()
