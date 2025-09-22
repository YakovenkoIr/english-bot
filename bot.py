# bot.py
import os
from groq import Groq
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# -----------------------------
# ENV variables (в Render або локально)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Безпечна перевірка на старті
if not TELEGRAM_TOKEN:
    raise SystemExit("❌ TELEGRAM_TOKEN not set in environment")
if not GROQ_API_KEY:
    raise SystemExit("❌ GROQ_API_KEY not set in environment")

# -----------------------------
# Ініціалізація Groq клієнта
client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["A1", "B2", "C1"], ["Chat with AI 🤖"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Привіт! Обери рівень англійської або спробуй чат з ШІ:", reply_markup=reply_markup)

# -----------------------------
# Chat з Groq (LLaMA-3)
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = client.chat.completions.create(
    model="llama3-8b-8192",  # або інша модель, яку ти обрала
    messages=[
        {"role": "system", "content": "You are an English teacher. Always answer in English, briefly and simply."},
        {"role": "user", "content": user_text}
    ]
)
        answer = resp.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        # НЕ виводимо ключі тут — тільки текст помилки
        await update.message.reply_text("⚠️ Помилка зі ШІ: " + str(e))

# -----------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Chat with AI 🤖"), chat_ai))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))

    print("✅ Bot is running with Groq AI...")
    app.run_polling()

if __name__ == "__main__":
    main()



