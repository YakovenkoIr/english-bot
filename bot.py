# ------------------------
# /chat команда (ШІ)
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text  

    try:
        # новий клієнт OpenAI
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # запит до моделі
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти викладач англійської. Відповідай коротко і просто."},
                {"role": "user", "content": user_text}
            ]
        )

        # витягуємо відповідь
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text("⚠️ Сталася помилка зі ШІ: " + str(e))




