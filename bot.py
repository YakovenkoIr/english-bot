import os
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("8204640997:AAF4GPpv6FDyBFuG2BE86O1KjQhR9f4en1g")

async def start(update, context):
    await update.message.reply_text("Привіт! Я English Bot. Вибери свій рівень англійської.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()


