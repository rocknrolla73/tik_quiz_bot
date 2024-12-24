import os
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
    args = context.args  # Получаем аргументы команды /start
    user_id = update.effective_user.id

    if args:
        block_key = args[0]  # Аргумент (например, "bar1")
        if block_key in questions_blocks:
            if user_id not in user_data:
                # Если пользователь запускает бота впервые
                user_data[user_id] = {"total_score": 0}  # Общий счёт
            user_data[user_id]["current_question"] = 0
            user_data[user_id]["score"] = 0  # Счёт за текущую локацию
            user_data[user_id]["questions"] = questions_blocks[block_key]

            bar_name = bar_names.get(block_key, "Unknown Bar")  # Получаем имя бара
            await update.message.reply_text(f"Добро пожаловать в викторину для {bar_name}!")
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

    # Проверяем правильность ответа
    if user_response == question_data["correct_option"]:
        points = question_data.get("weight", 1)
        user_data[user_id]["score"] += points
        await query.edit_message_text(f"Правильно! Вы заработали {points} баллов. Ваш текущий счёт за локацию: {user_data[user_id]['score']}")
    else:
        await query.edit_message_text(
            f"Неверно. Правильный ответ: {question_data['options'][question_data['correct_option']]}"
        )

    if current_question_index + 1 < len(questions):
        user_data[user_id]["current_question"] += 1
        await send_question(query, context)
    else:
        user_data[user_id]["total_score"] += user_data[user_id]["score"]
        total_score = user_data[user_id]["total_score"]
        location_score = user_data[user_id]["score"]

        await query.message.reply_text(
            f"Викторина для текущей локации завершена! Ваш счёт за локацию: {location_score}\n"
            f"Общий счёт за все локации: {total_score}"
        )

        # Очищаем данные текущей локации
        del user_data[user_id]["current_question"]
        del user_data[user_id]["score"]
        del user_data[user_id]["questions"]

# Основной запуск бота
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL вашего Webhook
    PORT = int(os.getenv("PORT", 8443))  # Порт для Webhook
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
