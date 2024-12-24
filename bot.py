import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Список вопросов
questions = [
    {
        "question": "Какой напиток самый популярный в мире?",
        "options": ["Чай", "Кофе", "Вода", "Вино"],
        "correct_option": 0
    },
    {
        "question": "Сколько планет в солнечной системе?",
        "options": ["7", "8", "9", "10"],
        "correct_option": 1
    },
    {
        "question": "Кто написал роман 'Война и мир'?",
        "options": ["Достоевский", "Пушкин", "Толстой", "Чехов"],
        "correct_option": 2
    }
]

# Переменная для отслеживания текущего вопроса
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"current_question": 0, "score": 0}
    await send_question(update, context)

# Функция для отправки вопроса
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_question_index = user_data[user_id]["current_question"]
    question_data = questions[current_question_index]

    # Создаем клавиатуру с вариантами ответов
    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(i))]
        for i, option in enumerate(question_data["options"])
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        question_data["question"],
        reply_markup=reply_markup
    )

# Обработка ответа
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_response = int(query.data)
    current_question_index = user_data[user_id]["current_question"]
    question_data = questions[current_question_index]

    # Проверяем ответ
    if user_response == question_data["correct_option"]:
        user_data[user_id]["score"] += 1
        await query.edit_message_text(f"Правильно! Ваш текущий счет: {user_data[user_id]['score']}")
    else:
        await query.edit_message_text(
            f"Неверно. Правильный ответ: {question_data['options'][question_data['correct_option']]}"
        )

    # Переходим к следующему вопросу или завершаем викторину
    if current_question_index + 1 < len(questions):
        user_data[user_id]["current_question"] += 1
        await send_question(update, context)
    else:
        await query.message.reply_text(
            f"Викторина завершена! Ваш итоговый счет: {user_data[user_id]['score']}"
        )

# Основной запуск бота
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчики команд и ответов
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
