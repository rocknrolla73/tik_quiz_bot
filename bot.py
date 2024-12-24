import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

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
            "media": "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif"  # Гифка
        },
        {
            "question": "Сколько планет в солнечной системе?",
            "options": ["7", "8", "9", "10"],
            "correct_option": 1,
            "weight": 2,
            "media": "https://museum-21.su/upload/iblock/a2d/cu5nmj88d9uahq2bdxi3bxx7x6ut5qaa.jpg"  # Изображение
        }
    ],
    "bar2": [
        {
            "question": "Кто написал роман 'Война и мир'?",
            "options": ["Достоевский", "Пушкин", "Толстой", "Чехов"],
            "correct_option": 2,
            "weight": 3,
            "media": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQI-dFGIQNA-8NmQPrQugDxmkAiD4DLEQDvmQ&s"  # Фото Толстого
        },
        {
            "question": "Как называется столица Казахстана?",
            "options": ["Алматы", "Астана", "Шымкент", "Караганда"],
            "correct_option": 1,
            "weight": 1
        }
    ]
    # Добавьте остальные блоки для баров 3-6
}

# Состояние пользователей
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_data:
        user_data[user_id] = {"total_score": 0}
        user_name = update.effective_user.first_name or update.effective_user.username or "Игрок"
        user_data[user_id]["username"] = user_name
        await update.message.reply_text(
            f"Привет, {user_name}! Добро пожаловать в викторину. Выберите бар, чтобы начать."
        )
    else:
        await update.message.reply_text("Вы уже зарегистрированы! Используйте ссылку для начала викторины.")

# Запуск викторины
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args  # Получаем аргументы команды /start
    user_id = update.effective_user.id

    if args:
        block_key = args[0]  # Аргумент (например, "bar1")
        if block_key in questions_blocks:
            if user_id not in user_data:
                await update.message.reply_text("Вы не зарегистрированы. Используйте команду /start для начала.")
                return

            user_data[user_id]["current_question"] = 0
            user_data[user_id]["score"] = 0  # Счёт за текущую локацию
            user_data[user_id]["fastest_user"] = None
            user_data[user_id]["fastest_time"] = float("inf")  # Устанавливаем бесконечное время
            user_data[user_id]["questions"] = questions_blocks[block_key]

            bar_name = bar_names.get(block_key, "Unknown Bar")
            await update.message.reply_text(f"Начинаем викторину для {bar_name}!")
            await send_question(update, context)
            return

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

    # Обновляем самого быстрого игрока
    if time_taken < user_data[user_id]["fastest_time"]:
        user_data[user_id]["fastest_time"] = time_taken
        user_data[user_id]["fastest_user"] = user_id

    if current_question_index + 1 < len(questions):
        user_data[user_id]["current_question"] += 1
        await send_question(query, context)
    else:
        fastest_user_id = user_data[user_id]["fastest_user"]
        fastest_time = user_data[user_id]["fastest_time"]
        fastest_user_name = user_data[fastest_user_id]["username"]

        await query.message.reply_text(
            f"Викторина завершена!\n"
            f"Ваш счёт за локацию: {user_data[user_id]['score']}\n"
            f"Самый быстрый игрок: {fastest_user_name} ({fastest_time:.2f} секунд)."
        )

        # Очищаем данные текущей локации
        del user_data[user_id]["current_question"]
        del user_data[user_id]["questions"]

# Основной запуск бота
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", 8443))

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", start_quiz))
    app.add_handler(CallbackQueryHandler(handle_answer))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
