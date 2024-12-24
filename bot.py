import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Вопросы по блокам
questions_blocks = {
    "bar1": [
        {"question": "Какой напиток самый популярный в мире?", "options": ["Чай", "Кофе", "Вода", "Вино"], "correct_option": 0},
        {"question": "Сколько планет в солнечной системе?", "options": ["7", "8", "9", "10"], "correct_option": 1}
    ],
    "bar2": [
        {"question": "Кто написал роман 'Война и мир'?", "options": ["Достоевский", "Пушкин", "Толстой", "Чехов"], "correct_option": 2},
        {"question": "Как называется столица Казахстана?", "options": ["Алматы", "Астана", "Шымкент", "Караганда"], "correct_option": 1}
    ],
    # Добавьте остальные блоки для баров 3-8
}

# Состояние пользователей
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args  # Получаем аргументы команды /start
    user_id = update.effective_user.id

    # Если аргументы присутствуют
    if args:
        block_key = args[0]  # Аргумент (например, "bar1")
        if block_key in questions_blocks:
            if user_id not in user_data:
                # Если пользователь запускает бота впервые
                user_data[user_id] = {"total_score": 0}  # Общий счёт
            user_data[user_id]["current_question"] = 0
            user_data[user_id]["score"] = 0  # Счёт за текущую локацию
            user_data[user_id]["questions"] = questions_blocks[block_key]

            await update.message.reply_text(f"Добро пожаловать! Викторина для заведения {block_key} активирована.")
            await send_question(update, context)
            return

    # Если параметр некорректен
    await update.message.reply_text("Неверная ссылка или команда. Попробуйте снова.")

# Отправка текущего вопроса
async def send_question(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update_or_query, Update):
        user_id = update_or_query.effective_user.id
        message = update_or_query.message
    else:
        user_id = update_or_query.from_user.id
        message = update_or_query.message

    current_question_index = user_data[user_id]["current_question"]
    questions = user_data[user_id]["questions"]
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
    questions = user_data[user_id]["questions"]
    question_data = questions[current_question_index]

    # Проверяем правильность ответа
    if user_response == question_data["correct_option"]:
        user_data[user_id]["score"] += 1
        await query.edit_message_text(f"Правильно! Ваш текущий счёт за локацию: {user_data[user_id]['score']}")
    else:
        await query.edit_message_text(
            f"Неверно. Правильный ответ: {question_data['options'][question_data['correct_option']]}"
        )

    # Если есть ещё вопросы
    if current_question_index + 1 < len(questions):
        user_data[user_id]["current_question"] += 1
        await send_question(query, context)
    else:
        # Завершаем викторину для локации
        user_data[user_id]["total_score"] += user_data[user_id]["score"]  # Обновляем общий счёт
        total_score = user_data[user_id]["total_score"]  # Общий счёт
        location_score = user_data[user_id]["score"]  # Счёт за текущую локацию

        await query.message.reply_text(
            f"Викторина завершена! Ваш счёт за локацию: {location_score}\n"
            f"Общий счёт за все локации: {total_score}"
        )

        # Очищаем данные текущей локации
        del user_data[user_id]["current_question"]
        del user_data[user_id]["score"]
        del user_data[user_id]["questions"]

# Основной запуск бота
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))  # Убрали pass_args
    app.add_handler(CallbackQueryHandler(handle_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
