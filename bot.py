import os
import openai

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise SystemExit("OPENAI_API_KEY not set in environment")

# створюємо клієнта один раз (наприклад глобально)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

# у функції chat_ai
response = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are an English teacher. Answer briefly and simply."},
        {"role": "user", "content": user_text}
    ]
)
answer = response.choices[0].message.content

