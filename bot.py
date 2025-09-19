import os
import openai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# -----------------------------
# Отримуємо токени із Render Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise SystemExit("❌ TELEGRAM_TOKEN not set in environment")
if not OPENAI_KEY:
    raise SystemExit("❌ OPENAI_API_KEY not set in environment")

# -----------------------------
# Створюємо клієнта OpenAI
client = openai.OpenAI(api_key=OPENAI_KEY)

# -----------------------------
# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["A1", "B2", "C1"], ["Chat with AI 🤖"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привіт! Обери рівень англійської або спробуй чат з ШІ:",
        reply_markup=reply_markup
    )

# -----------------------------
# ChatGPT інтеграція
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти викладач англійської. Відповідай коротко і просто."},
                {"role": "user", "content": user_text}
            ]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text("⚠️ Сталася помилка зі ШІ: " + str(e))

# -----------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Chat with AI 🤖"), chat_ai))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))  # відповідає на будь-який текст

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
