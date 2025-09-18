import os
import json
import openai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 🔹 Токен від Render (Environment Variables)
TOKEN = os.getenv("TELEGRAM_TOKEN")

# 🔹 API ключ OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# ------------------------
# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["A1", "B2", "C1"], ["Chat with AI 🤖"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Привіт! Обери рівень англійської або спробуй чат з ШІ:", reply_markup=reply_markup)

# ------------------------
# /chat команда (ШІ)
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text  

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти викладач англійської. Відповідай коротко і просто."},
                {"role": "user", "content": user_text}
            ]
        )
        answer = response.choices[0].message["content"]
        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text("⚠️ Сталася помилка зі ШІ: " + str(e))

# ------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Chat with AI 🤖"), chat_ai))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))  # відповіді на будь-який текст

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()


