import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from datetime import datetime
import asyncio

# Настройки
BOT_TOKEN = "8488896816:AAEWHfMkV850nFfLNmbJbJxYI7gjvXc-Mk8"
ADMIN_ID = 7352069187

# Хранение данных (в памяти)
user_data = {}
current_prize = "Не установлен"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO,
    handlers=[logging.StreamHandler()]  # Добавляем вывод в консоль
)
logger = logging.getLogger(__name__)

# Клавиатура для заданий
keyboard = [['/get_tokens', '/my_stats'], ['/leaderboard', '/help']]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Функция для определения ранга пользователя
def get_user_rank(user_id):
    if not user_data:
        return "Н/Д"
    
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]["tokens"], reverse=True)
    user_ids = [uid for uid, _ in sorted_users]
    
    if user_id in user_ids:
        return user_ids.index(user_id) + 1
    return "Н/Д"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        if user_id not in user_data:
            user_data[user_id] = {"tokens": 0, "username": username}
        
        await update.message.reply_text(
            f"Привет, {username}! Я бот для заработка токенов.\n\n"
            "Выполняй задания и получай токены! Раз в неделю подводим итоги.\n"
            "Используй кнопки ниже для взаимодействия.",
            reply_markup=reply_markup
        )
        logger.info(f"User {username} started the bot")
    except Exception as e:
        logger.error(f"Error in start command: {e}")

# Команда /get_tokens - показывает доступные задания
async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tasks_text = """
🎯 Доступные задания:

1. 📝 Написать содержательное сообщение (более 50 символов) - 1 токен
2. 🖼 Отправить крутое фото/картинку - 1 токен
3. 💬 Активно участвовать в обсуждении (3+ сообщения подряд) - 2 токена
4. 👥 Привести друга в группу - 3 токена
5. 🤔 Решить загадку от бота - 2 токена

Просто выполняй задания и бот автоматически начислит токены!
        """
        await update.message.reply_text(tasks_text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in show_tasks: {e}")

# Команда /my_stats - показывает статистику пользователя
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        if user_id not in user_data:
            user_data[user_id] = {"tokens": 0, "username": username}
        
        stats = user_data[user_id]
        await update.message.reply_text(
            f"📊 Статистика {username}:\n"
            f"Токены: {stats['tokens']} 🪙\n"
            f"Место в рейтинге: {get_user_rank(user_id)}",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in show_stats: {e}")

# Команда /leaderboard - показывает таблицу лидеров
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not user_data:
            await update.message.reply_text("Пока никто не заработал токенов. Будь первым!", reply_markup=reply_markup)
            return
        
        sorted_users = sorted(user_data.items(), key=lambda x: x[1]["tokens"], reverse=True)[:10]
        
        leaderboard_text = "🏆 ТОП-10 участников:\n\n"
        for i, (user_id, data) in enumerate(sorted_users, 1):
            leaderboard_text += f"{i}. {data['username']} - {data['tokens']} 🪙\n"
        
        leaderboard_text += f"\nПриз этой недели: {current_prize}"
        
        await update.message.reply_text(leaderboard_text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in leaderboard: {e}")

# Команда /help - показывает помощь
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        help_text = """
🤖 Помощь по боту:

/get_tokens - показать доступные задания
/my_stats - показать свою статистику
/leaderboard - показать таблицу лидеров
/help - показать эту помощь

Для админов:
/set_prize [текст] - установить приз на неделю
        """
        await update.message.reply_text(help_text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in help: {e}")

# Обработчик сообщений - начисление токенов за задания
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        if user_id not in user_data:
            user_data[user_id] = {"tokens": 0, "username": username}
        
        message = update.message
        earned_tokens = 0
        
        # Задание 1: Сообщение более 50 символов
        if message.text and len(message.text) > 50:
            earned_tokens += 1
            logger.info(f"User {username} earned 1 token for long message")
        
        # Задание 2: Отправка фото
        if message.photo:
            earned_tokens += 1
            logger.info(f"User {username} earned 1 token for photo")
        
        # Начисление токенов
        if earned_tokens > 0:
            user_data[user_id]["tokens"] += earned_tokens
            await message.reply_text(
                f"+{earned_tokens} токен(а) 🪙 за активность!\n"
                f"Теперь у тебя: {user_data[user_id]['tokens']} токенов",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error handling message: {e}")

# Команда для админа - установить приз
async def set_prize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("Эта команда только для админа!")
            return
        
        if not context.args:
            await update.message.reply_text("Использование: /set_prize [описание приза]")
            return
        
        prize_text = " ".join(context.args)
        global current_prize
        current_prize = prize_text
        await update.message.reply_text(f"🎉 Приз установлен: {prize_text}")
        logger.info(f"Prize set to: {prize_text}")
    except Exception as e:
        logger.error(f"Error in set_prize: {e}")

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")

# Основная функция
def main():
    try:
        logger.info("Starting bot...")
        
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("get_tokens", show_tasks))
        application.add_handler(CommandHandler("my_stats", show_stats))
        application.add_handler(CommandHandler("leaderboard", show_leaderboard))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("set_prize", set_prize))
        
        # Обработчики сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_message))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("Bot started successfully!")
        print("Бот запущен! Проверь его в Telegram")
        
        # Запускаем бота
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"Ошибка запуска: {e}")

if __name__ == "__main__":
    main()
