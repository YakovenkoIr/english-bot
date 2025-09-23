import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from groq import Groq

# Логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Токени
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# Завантажуємо питання
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# Стан користувачів
user_state = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📝 Пройти тест англійської", callback_data="test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привіт! Спочатку перевіримо твій рівень англійської:", reply_markup=reply_markup)

# Натискання кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "test":
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        keyboard = [[InlineKeyboardButton(level, callback_data=f"level_{level}")] for level in levels]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Оберіть рівень тесту:", reply_markup=reply_markup)

    elif query.data.startswith("level_"):
        level = query.data.split("_")[1]
        user_state[query.from_user.id] = {"mode": "test", "level": level, "q_index": 0, "score": 0}
        await send_question(query, context)

    elif query.data == "chat":
        user_state[query.from_user.id] = {"mode": "chat"}
        await query.edit_message_text("Тепер спілкуйся англійською з AI 🇬🇧. Напиши будь-яке повідомлення!")

# Надсилання питання
async def send_question(query, context):
    user_id = query.from_user.id
    state = user_state[user_id]
    level = state["level"]
    index = state["q_index"]

    if index < len(QUESTIONS[level]):
        q = QUESTIONS[level][index]
        keyboard = [[InlineKeyboardButton(opt, callback_data=f"answer_{i}")] for i, opt in enumerate(q["options"])]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(q["question"], reply_markup=reply_markup)
    else:
        total = len(QUESTIONS[level])
        score = state["score"]
        percent = int(score / total * 100)

        # Показуємо результат українською
        msg = f"✅ Тест завершено!\n\nВаш результат: {score}/{total} ({percent}%)\nРівень тесту: {state['level']}\n\nРекомендуємо перейти до спілкування з AI англійською 🇬🇧"
        keyboard = [[InlineKeyboardButton("💬 Перейти до AI", callback_data="chat")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(msg, reply_markup=reply_markup)

# Відповідь на питання
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    state = user_state.get(user_id)

    if not state or state.get("mode") != "test":
        return

    level = state["level"]
    index = state["q_index"]
    q = QUESTIONS[level][index]

    # Перевірка
    answer_index = int(query.data.split("_")[1])
    if answer_index == q["correct"]:
        state["score"] += 1

    state["q_index"] += 1
    user_state[user_id] = state
    await send_question(query, context)

# Чат з AI
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = user_state.get(user_id)

    if not state or state.get("mode") != "chat":
        await update.message.reply_text("⚠️ Спочатку пройдіть тест, щоб дізнатися ваш рівень!")
        return

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an English teacher. Always reply in English."},
                {"role": "user", "content": update.message.text}
            ],
        )
        reply = completion.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"❌ Помилка AI: {e}")

# Головна
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="^(test|level_|chat)$"))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    app.run_polling()

if __name__ == "__main__":
    main()
