import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Названия баров
bar_names = {
    "bar1": "Line Brew",
    "bar2": "AMBER",
    "bar3": "STORY",
    "bar4": "PlatformA",
    "bar5": "French 42",
    "bar6": "loopers"
}

# Вопросы по блокам
questions_blocks = {
    "bar1": [
        {
            "question": "Какой напиток самый популярный в мире?",
            "options": ["Чай", "Кофе", "Вода", "Вино"],
            "correct_option": 0,
            "weight": 1,
            "media": "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif"
        },
        {
            "question": "Сколько планет в солнечной системе?",
            "options": ["7", "8", "9", "10"],
            "correct_option": 1,
            "weight": 2,
            "media": "https://museum-21.su/upload/iblock/a2d/cu5nmj88d9uahq2bdxi3bxx7x6ut5qaa.jpg"
        }
    ],
    "bar2": [
        {
            "question": "Кто написал роман 'Война и мир'?",
            "options": ["Достоевский", "Пушкин", "Толстой", "Чехов"],
            "correct_option": 2,
            "weight": 3,
            "media": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Lev_Nikolayevich_Tolstoy_in_1910_by_Vladimir_Chertkov.jpg/548px-Lev_Nikolayevich_Tolstoy_in_1910_by_Vladimir_Chertkov.jpg"
        },
        {
            "question": "Как называется столица Казахстана?",
            "options": ["Алматы", "Астана", "Шымкент", "Караганда"],
            "correct_option": 1,
            "weight": 1
        }
    ]
}

# Состояние пользователей
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args  # Получаем аргументы из команды /start
    user_id = update.effective_user.id

    # Проверяем, если пользователь уже зарегистрирован
    if user_id not in user_data:
        user_name = update.effective_user.first_name or update.effective_user.username or "Игрок"
        user_data[user_id] = {
            "total_score": 0,
            "username": user_name
        }
        await update.message.reply_text(
            f"Привет, {user_name}! Вы успешно зарегистрированы. Начинаем викторину!"
        )
    else:
        await update.message.reply_text(
            "Добро пожаловать обратно! Начинаем викторину!"
        )

    # Проверяем наличие аргумента для запуска викторины
    if args:
        block_key = args[0]  # Аргумент (например, "bar1")
        if block_key in questions_blocks:
            user_data[user_id]["current_question"] = 0
            user_data[user_id]["score"] = 0
            user_data[user_id]["total_time"] = 0.0  # Общее время на локации
            user_data[user_id]["fastest_time"] = float("inf")
            user_data[user_id]["questions"] = questions_blocks[block_key]

            bar_name = bar_names.get(block_key, "Unknown Bar")
            await update.message.reply_text(f"Начинаем викторину для {bar_name}!")
            await send_question(update, context)
            return

    # Если аргумент отсутствует или неверен
    await update.message.reply_text(
        "Для начала викторины отсканируйте QR-код или используйте правильную ссылку."
    )

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

    # Фиксируем время отправки вопроса
    user_data[user_id]["question_start_time"] = datetime.now()

    # Если у вопроса есть медиа, отправляем его
    if "media" in question_data:
        media_url = question_data["media"]
        if media_url.endswith((".jpg", ".jpeg", ".png")):
            await message.reply_photo(photo=media_url)
        elif media_url.endswith(".gif"):
            await message.reply_animation(animation=media_url)

    # Отправляем текст вопроса и варианты ответа
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

    # Вычисляем время ответа
    answer_time = datetime.now()
    question_start_time = user_data[user_id].get("question_start_time")
    time_taken = (answer_time - question_start_time).total_seconds()

    # Добавляем время в общий счётчик
    user_data[user_id]["total_time"] += time_taken

    # Проверяем правильность ответа
    if user_response == question_data["correct_option"]:
        points = question_data.get("weight", 1)
        user_data[user_id]["score"] += points
        await query.edit_message_text(
            f"Правильно! Вы заработали {points} баллов.\n"
            f"Ваше время ответа: {time_taken:.2f} секунд."
        )
    else:
        await query.edit_message_text(
            f"Неверно. Правильный ответ: {question_data['options'][question_data['correct_option']]}\n"
            f"Ваше время ответа: {time_taken:.2f} секунд."
        )

    if current_question_index + 1 < len(questions):
        user_data[user_id]["current_question"] += 1
        await send_question(query, context)
    else:
        total_time = user_data[user_id]["total_time"]  # Суммарное время
        location_score = user_data[user_id]["score"]

        await query.message.reply_text(
            f"Викторина завершена!\n"
            f"Ваш счёт за локацию: {location_score}\n"
            f"Общее время на ответы: {total_time:.2f} секунд."
        )

        # Очищаем данные текущей локации
        del user_data[user_id]["current_question"]
        del user_data[user_id]["questions"]
        del user_data[user_id]["total_time"]

# Основной запуск бота
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", 8443))

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_answer))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
