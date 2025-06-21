import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация (ЗАМЕНИТЕ НА СВОИ ЗНАЧЕНИЯ!)
BOT_TOKEN = os.getenv('BOT_TOKEN', '7768583912:AAEJ51jQ5ayuC3yuclzpSbFEbnfM4gz5rr8')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1642268174'))

# Глобальные переменные для хранения состояния
active_chats = {}  # Формат: {user_id: chat_id}

async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки 'Ответить'"""
    query = update.callback_query
    await query.answer()

    try:
        user_id = query.data.split('_')[-1]  # Извлекаем user_id из callback_data
        
        # Сохраняем активный чат
        active_chats[user_id] = query.message.chat.id
        
        # Меняем сообщение
        await query.edit_message_text(
            text=f"✅ Чат с пользователем {user_id} активирован\n\n"
                 "Отправьте сообщение для пользователя:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔒 Закрыть чат", callback_data=f"close_{user_id}")
            ]])
        )
        
        logger.info(f"Чат с {user_id} активирован")
        
    except Exception as e:
        logger.error(f"Ошибка в start_chat: {e}")
        await query.edit_message_text("❌ Ошибка активации чата")

async def close_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка закрытия чата"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.data.split('_')[-1]
    
    if user_id in active_chats:
        del active_chats[user_id]
    
    await query.edit_message_text(
        text=f"❌ Чат с пользователем {user_id} закрыт",
        reply_markup=None
    )
    logger.info(f"Чат с {user_id} закрыт")

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений от пользователей"""
    if not update.message or not update.message.text:
        return
    
    # Игнорируем сообщения от бота
    if update.message.from_user.is_bot:
        return
    
    # Сообщения формата "👤 user-123: текст"
    if '👤' in update.message.text:
        user_id = update.message.text.split('👤 ')[1].split(':')[0]
        
        # Если чат уже активен - пересылаем сообщение
        if user_id in active_chats:
            await context.bot.send_message(
                chat_id=active_chats[user_id],
                text=update.message.text
            )
            return
    
    # Для новых сообщений создаем кнопку
    keyboard = [[InlineKeyboardButton("✅ Ответить", callback_data=f"start_{user_id}")]]
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=update.message.text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений от администратора"""
    if update.message.chat.id != ADMIN_ID:
        return
    
    # Ищем user_id для текущего чата
    user_id = next((uid for uid, chat_id in active_chats.items() 
                   if chat_id == update.message.chat.id), None)
    
    if user_id:
        # Пересылаем сообщение пользователю (имитация - в реальности нужен механизм связи)
        logger.info(f"Сообщение для {user_id}: {update.message.text}")
        
        # Здесь должен быть код отправки сообщения пользователю
        # Например, через сохранение в БД или другой механизм
    else:
        await update.message.reply_text("Сначала активируйте чат кнопкой 'Ответить'")

def main():
    try:
        # Создаем приложение
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        app.add_handler(CallbackQueryHandler(start_chat, pattern="^start_"))
        app.add_handler(CallbackQueryHandler(close_chat, pattern="^close_"))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
        app.add_handler(MessageHandler(filters.TEXT & filters.Chat(ADMIN_ID), handle_admin_message))
        
        logger.info("Бот запущен...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == '__main__':
    main()
