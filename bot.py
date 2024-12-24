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

# Состояние пользователей
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"current_question": 0, "score": 0}
    await send_question(update, context)

# Отправка текущего вопроса
async def send_question(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update_or_query, Update):
        user_id = update_or_query.effective_user.id
        message = update_or_query.message
    else:
        user_id = update_or_query.from_user.id
        message = update_or_query.message

    current_question_index = user_data[user_id]["current_question"]
    question_data = questions[current_question_index]

    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(i))]
        for i, option in enumerate(question_data["options"])
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        question_data["question"],
        reply_markup=reply_markup
    )

# Обработка ответа на вопрос
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_data:
        await query.message.reply_text("Произошла ошибка. Попробуйте снова отправить команду /start.")
        return

    user_response = int(query.data)
    current_question_index = user_data[user_id]["current_question"]
    question_data = questions[current_question_index]

    if user_response == question_data["correct_option"]:
        user_data[user_id]["score"] += 1
        await query.edit_message_text(f"Правильно! Ваш текущий счет: {user_data[user_id]['score']}")
    else:
        await query.edit_message_text(
            f"Неверно. Правильный ответ: {question_data['options'][question_data['correct_option']]}"
        )

    if current_question_index + 1 < len(questions):
        user_data[user_id]["current_question"] += 1
        await send_question(query, context)
    else:
        await query.message.reply_text(
            f"Викторина завершена! Ваш итоговый счет: {user_data[user_id]['score']}"
        )
        del user_data[user_id]

# Основной запуск бота
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL вашего Webhook
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_answer))

    # Настройка Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
