import logging
from telegram import Update
from telegram.ext import ContextTypes

logging.basicConfig(level=logging.INFO)

# client має бути створений глобально десь вище:
# from groq import Groq
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_CANDIDATES = [
    "llama-3.1-8b-instant",    # постав свою основну модель
    "llama-3.3-70b-versatile", # запасна
    # додай ще, якщо потрібно
]

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    last_error = None

    for model_name in MODEL_CANDIDATES:
        try:
            logging.info(f"Trying Groq model: {model_name}")
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an English teacher. Always reply in English. Keep answers short and simple."},
                    {"role": "user", "content": user_text}
                ]
            )
            # Отримали відповідь — обробляємо її ТІЛЬКИ тут (у try)
            answer = resp.choices[0].message.content
            await update.message.reply_text(answer)
            return  # Успіх — виходимо з функції

        except Exception as e:
            last_error = e
            logging.exception(f"Model {model_name} failed with error:")
            # якщо помилка явно про decommissioned або квоту — пробуємо наступну модель
            err_text = str(e).lower()
            if any(keyword in err_text for keyword in ("decommissioned", "model_decommissioned", "insufficient_quota", "quota", "429")):
                continue  # пробуємо наступну модель
            else:
                # інші помилки (наприклад: invalid_api_key) — краще не пробувати ще моделі
                break

    # Якщо дійшли сюди — нічого не спрацювало
    if last_error:
        await update.message.reply_text("⚠️ Помилка зі ШІ: " + str(last_error))
    else:
        await update.message.reply_text("⚠️ Невідома помилка зі ШІ — перевір логи.")
