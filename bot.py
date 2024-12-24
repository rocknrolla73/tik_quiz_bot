import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Привет, {update.message.from_user.first_name}! Добро пожаловать в Tik Quiz!")

# Основной запуск бота
def main():
    # Получаем токен из переменной окружения
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    # Создаем объект Application
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчик команды /start
    app.add_handler(CommandHandler("start", start))

    # Запускаем бота
    app.run_polling()

if __name__ == "__main__":
    main()
