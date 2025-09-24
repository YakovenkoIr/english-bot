import json
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import asyncio

TOKEN = "ТУТ_ТВОЙ_ТОКЕН"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Панель меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Пройти тест")],
        [KeyboardButton(text="💬 Спілкування англійською")]
    ],
    resize_keyboard=True
)

# Завантажуємо питання з JSON
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# Словник для збереження даних користувачів
user_data = {}

# Команда /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Привіт! 👋\nОберіть дію на панелі нижче:",
        reply_markup=main_menu
    )

# Натискання на "Пройти тест"
@dp.message(F.text == "📝 Пройти тест")
async def start_test(message: types.Message):
    user_data[message.from_user.id] = {
        "level": None,
        "score": 0,
        "current_q": 0,
        "questions": []
    }
    # Генеруємо по 1 питанню з кожного рівня
    for level in questions:
        q = random.choice(questions[level])
        q["level"] = level
        user_data[message.from_user.id]["questions"].append(q)

    await send_question(message)

# Функція відправки питання
async def send_question(message):
    data = user_data[message.from_user.id]
    if data["current_q"] < len(data["questions"]):
        q = data["questions"][data["current_q"]]
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=opt)] for opt in q["options"]],
            resize_keyboard=True
        )
        await message.answer(q["question"], reply_markup=kb)
    else:
        # Обчислюємо рівень
        levels = [q["level"] for i, q in enumerate(data["questions"]) if i < data["score"]]
        if levels:
            user_level = levels[-1]
        else:
            user_level = "A1"
        user_data[message.from_user.id]["level"] = user_level

        await message.answer(
            f"✅ За результатами тесту ваш рівень: *{user_level}*.\n"
            f"Тепер ви можете перейти до спілкування англійською!",
            parse_mode="Markdown",
            reply_markup=main_menu
        )

# Обробка повідомлень
@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    # Якщо користувач відповідає на питання
    if user_id in user_data and user_data[user_id]["current_q"] < len(user_data[user_id]["questions"]):
        q = user_data[user_id]["questions"][user_data[user_id]["current_q"]]
        if message.text == q["answer"]:
            user_data[user_id]["score"] += 1
        user_data[user_id]["current_q"] += 1
        await send_question(message)

    # Якщо обрав "Спілкування"
    elif message.text == "💬 Спілкування англійською":
        if user_id not in user_data or not user_data[user_id].get("level"):
            await message.answer("❌ Спочатку пройдіть тест, щоб визначити ваш рівень.")
        else:
            await message.answer(
                "Добре! Тепер спілкуємось англійською 😊\n\nНапишіть будь-що, і я відповім англійською."
            )

    # Режим спілкування
    elif user_id in user_data and user_data[user_id].get("level"):
        await message.answer(f"Your message in English: {message.text}")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
