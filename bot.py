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
            "question": "В каком году был основан бренд *Christopher Ward?*",
            "options": ["2005", "2010", "2000", "1995"],
            "correct_option": 0,
            "weight": 2,
            "media": "https://upload.wikimedia.org/wikipedia/en/9/9d/Christopher_Ward_London_Logo.png"
        },
        {
            "question": "В каком городе находится главная штаб-квартира *Christopher Ward?*",
            "options": ["Нью-Йорк, США", "Лондон, Великобритания", "Женеве, Швейцария", "Цюрих, Швейцария"],
            "correct_option": 1,
            "weight": 1,
            "media": "https://media.giphy.com/media/1BhFiWpMigCnWnRMAG/giphy.gif"
        },
        {
            "question": "Какая самая известная модель часов, выпущенная Christopher Ward в 2009 году, которая стала их визитной карточкой?",
            "options": ["C60 Trident", "C5 Malvern", "C1 Grand Malvern", "C7 Rapide"],
            "correct_option": 0,
            "weight": 2
        }
    ]
}

# Состояние пользователей
user_data = {}

# ID администратора (замените на свой Telegram ID)
ADMIN_ID = int(os.getenv("ADMIN_ID", 53914223))

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
            f"Привет, {user_name}! Вы успешно зарегистрированы. Начнем игру!"
        )
    else:
        await update.message.reply_text(
            "_Добро пожаловать обратно! Продолжаем игру!_"
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
            await update.message.reply_text(f"Начинаем игру в *{bar_name}*!")
            await send_question(update, context)
            return

    # Если аргумент отсутствует или неверен
    await update.message.reply_text(
        "Для начала игры отсканируйте QR-код."
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
            f"Правильно! Вы получили *{points} баллов*.\n"
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

        # Добавляем баллы за текущую локацию в общий счёт
        user_data[user_id]["total_score"] += location_score

        await query.message.reply_text(
            f"Уровень пройден!\n"
            f"Ваш счёт на локации: {location_score}\n"
            f"Общее время на ответы: {total_time:.2f} секунд."
        )

        # Очищаем данные текущей локации
        del user_data[user_id]["current_question"]
        del user_data[user_id]["questions"]
        del user_data[user_id]["total_time"]

# Команда /results (только для администратора)
async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для использования этой команды.")
        return

    if not user_data:
        await update.message.reply_text("Никто ещё не зарегистрировался в викторине.")
        return

    results = "Результаты участников:\n"
    for uid, data in user_data.items():
        results += f"Игрок: {data['username']}, Общий счёт: {data['total_score']}.\n"

    await update.message.reply_text(results)

# Основной запуск бота
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", 8443))

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_answer))
    app.add_handler(CommandHandler("results", show_results))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
