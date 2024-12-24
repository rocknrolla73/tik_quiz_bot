import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(f"Привет, {update.message.from_user.first_name}! Добро пожаловать в Tik Quiz!")

# Основной запуск бота
def main():
    # Получаем токен из переменной окружения
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    # Создаем объект Updater
    updater = Updater(TOKEN)

    # Регистрируем обработчик команды /start
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
