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

# Завантажуємо питання з JSON
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# Словник для збереження стану користувача
user_state = {}

# Команда старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Test your English", callback_data="test")],
        [InlineKeyboardButton("💬 Chat with AI", callback_data="chat")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Hello! Choose an option:", reply_markup=reply_markup)

# Обробка натискання кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "test":
        # Вибір рівня
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        keyboard = [[InlineKeyboardButton(level, callback_data=f"level_{level}")] for level in levels]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select your English level:", reply_markup=reply_markup)

    elif query.data.startswith("level_"):
        level = query.data.split("_")[1]
        user_state[query.from_user.id] = {"mode": "test", "level": level, "q_index": 0, "score": 0}
        await send_question(query, context)

    elif query.data == "chat":
        user_state[query.from_user.id] = {"mode": "chat"}
        await query.edit_message_text("You can now chat in English with AI 🇬🇧. Just type your message!")

# Відправка питання
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
        # Завершення тесту
        total = len(QUESTIONS[level])
        score = state["score"]
        percent = int(score / total * 100)
        await query.edit_message_text(f"✅ Test finished!\nYour score: {score}/{total} ({percent}%)\n\nNow let's chat in English! 💬")
        user_state[user_id] = {"mode": "chat"}

# Обробка відповідей на тест
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

    # Перевірка відповіді
    answer_index = int(query.data.split("_")[1])
    if answer_index == q["correct"]:
        state["score"] += 1

    state["q_index"] += 1
    user_state[user_id] = state
    await send_question(query, context)

# Обробка повідомлень (чат з AI)
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = user_state.get(user_id)

    if not state or state.get("mode") != "chat":
        await update.message.reply_text("⚠️ Please start a test first or select 'Chat with AI'.")
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
        await update.message.reply_text(f"❌ Error with AI: {e}")

# Головна функція
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="^(test|level_|chat)$"))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    app.run_polling()

if __name__ == "__main__":
    main()

