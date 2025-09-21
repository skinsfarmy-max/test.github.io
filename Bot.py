import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from datetime import datetime, timedelta
import asyncio

# Настройки
BOT_TOKEN = "8488896816:AAEWHfMkV850nFfLNmbJbJxYI7gjvXc-Mk8"  # Замени на токен от @BotFather
ADMIN_ID = 7352069187  # Замени на свой ID в Telegram

# Хранение данных (в памяти)
user_data = {}  # {user_id: {"tokens": int, "username": str}}
group_week_winner = None
week_start_date = datetime.now()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Клавиатура для заданий
keyboard = [['/get_tokens', '/my_stats'], ['/leaderboard', '/help']]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    if user_id not in user_data:
        user_data[user_id] = {"tokens": 0, "username": username}
    
    await update.message.reply_text(
        f"Привет, {username}! Я бот для заработка токенов в этой группе.\n\n"
        "Выполняй задания и получай токены! Раз в неделю подводим итоги и определяем победителя.\n"
        "Используй кнопки ниже для взаимодействия.",
        reply_markup=reply_markup
    )

# Команда /get_tokens - показывает доступные задания
async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks_text = """
🎯 Доступные задания:

1. 📝 Написать содержательное сообщение (более 50 символов) - 1 токен
2. 🖼 Отправить крутое фото/картинку - 1 токен
3. 💬 Активно участвовать в обсуждении (3+ сообщения подряд) - 2 токена
4. 👥 Привести друга в группу (по реферальной ссылке) - 3 токена
5. 🤔 Решить загадку от бота - 2 токена

Просто выполняй задания и бот автоматически начислит токены!
    """
    await update.message.reply_text(tasks_text, reply_markup=reply_markup)

# Команда /my_stats - показывает статистику пользователя
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        stats = user_data[user_id]
        await update.message.reply_text(
            f"📊 Твоя статистика:\n"
            f"Токены: {stats['tokens']} 🪙\n"
            f"Место в рейтинге: {get_user_rank(user_id)}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Ты еще не заработал токенов. Выполняй задания!", reply_markup=reply_markup)

# Команда /leaderboard - показывает таблицу лидеров
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_data:
        await update.message.reply_text("Пока никто не заработал токенов. Будь первым!", reply_markup=reply_markup)
        return
    
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]["tokens"], reverse=True)[:10]
    
    leaderboard_text = "🏆 ТОП-10 участников:\n\n"
    for i, (user_id, data) in enumerate(sorted_users, 1):
        leaderboard_text += f"{i}. {data['username']} - {data['tokens']} 🪙\n"
    
    await update.message.reply_text(leaderboard_text, reply_markup=reply_markup)

# Команда /help - показывает помощь
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 Помощь по боту:

/get_tokens - показать доступные задания
/my_stats - показать свою статистику
/leaderboard - показать таблицу лидеров
/help - показать эту помощь

Для админов:
/announce [текст] - объявление для всех
/set_prize [текст] - установить приз на неделю
    """
    await update.message.reply_text(help_text, reply_markup=reply_markup)

# Обработчик сообщений - начисление токенов за задания
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    if user_id not in user_data:
        user_data[user_id] = {"tokens": 0, "username": username}
    
    message = update.message
    earned_tokens = 0
    
    # Задание 1: Сообщение более 50 символов
    if len(message.text or "") > 50:
        earned_tokens += 1
    
    # Задание 2: Отправка фото
    if message.photo:
        earned_tokens += 1
    
    # Начисление токенов
    if earned_tokens > 0:
        user_data[user_id]["tokens"] += earned_tokens
        await message.reply_text(
            f"+{earned_tokens} токен(а) 🪙 за активность!\n"
            f"Теперь у тебя: {user_data[user_id]['tokens']} токенов",
            reply_markup=reply_markup
        )

# Функция для определения ранга пользователя
def get_user_rank(user_id):
    if not user_data:
        return "Н/Д"
    
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]["tokens"], reverse=True)
    user_ids = [uid for uid, _ in sorted_users]
    
    if user_id in user_ids:
        return user_ids.index(user_id) + 1
    return "Н/Д"

# Еженедельное подведение итогов
async def weekly_winner(context: CallbackContext):
    global group_week_winner
    
    if not user_data:
        return
    
    # Находим победителя
    winner_id = max(user_data.items(), key=lambda x: x[1]["tokens"])[0]
    winner_data = user_data[winner_id]
    group_week_winner = winner_id
    
    # Отправляем сообщение о победителе
    winner_text = (
        f"🏆 Недельный победитель!\n"
        f"Поздравляем {winner_data['username']} с {winner_data['tokens']} токенами!\n"
        f"Админ свяжется с тобой для вручения приза!"
    )
    
    await context.bot.send_message(chat_id=context.job.chat_id, text=winner_text)
    
    # Сбрасываем счетчики на новую неделю
    for user_id in user_data:
        user_data[user_id]["tokens"] = 0

# Команда для админа - установить приз
async def set_prize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Эта команда только для админа!")
        return
    
    prize_text = " ".join(context.args)
    if not prize_text:
        await update.message.reply_text("Использование: /set_prize [описание приза]")
        return
    
    global current_prize
    current_prize = prize_text
    await update.message.reply_text(f"Приз установлен: {prize_text}")

# Команда для админа - объявление
async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Эта команда только для админа!")
        return
    
    announcement = " ".join(context.args)
    if not announcement:
        await update.message.reply_text("Использование: /announce [текст объявления]")
        return
    
    await update.message.reply_text(f"📢 Объявление: {announcement}")

# Основная функция
def main():
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get_tokens", show_tasks))
    application.add_handler(CommandHandler("my_stats", show_stats))
    application.add_handler(CommandHandler("leaderboard", show_leaderboard))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_prize", set_prize))
    application.add_handler(CommandHandler("announce", announce))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
