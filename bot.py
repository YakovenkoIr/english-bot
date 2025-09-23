import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq

# ---------------- Налаштування логів ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------------- Ключі ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN not set in environment")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not set in environment")

# ---------------- Groq клієнт ----------------
client = Groq(api_key=GROQ_API_KEY)

# ---------------- Моделі Groq ----------------
MODEL_CANDIDATES = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile"
]

# ---------------- Основна функція AI ----------------
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    last_error = None

    for model_name in MODEL_CANDIDATES:
        try:
            logging.info(f"Trying Groq model: {model_name}")
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an English tutor. Always reply in English. Keep it short and simple."
                    },
                    {
                        "role": "user",
                        "content": user_text
                    }
                ]
            )
            answer = resp.choices[0].message.content
            await update.message.reply_text(answer)
            return   # ✅ Вихід після першої вдалої відповіді

        except Exception as e:
            last_error = e
            logging.exception(f"Model {model_name} failed with error:")
            continue   # Спробуємо наступну модель

    # Якщо жодна модель не спрацювала
    if last_error:
        await update.message.reply_text("⚠️ AI error: " + str(last_error))
    else:
        await update.message.reply_text("⚠️ Unknown AI error.")

# ---------------- Головна функція запуску ----------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Усі повідомлення йдуть у chat_ai
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))

    logging.info("✅ Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
