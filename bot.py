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

class ChatManager:
    def __init__(self):
        self.active_chats = {}  # {user_id: chat_id}

    async def start_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки 'Ответить'"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.data.split('_')[-1]
        self.active_chats[user_id] = query.message.chat.id
        
        await query.edit_message_text(
            text=f"✅ Чат с {user_id} активирован\nОтправьте сообщение:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Закрыть", callback_data=f"close_{user_id}")
            ]])
        )

    async def close_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки 'Закрыть'"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.data.split('_')[-1]
        self.active_chats.pop(user_id, None)
        await query.edit_message_text(f"❌ Чат с {user_id} закрыт")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка входящих сообщений"""
        if not update.message or not update.message.text:
            return

        if '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            
            if user_id in self.active_chats:
                await context.bot.send_message(
                    chat_id=self.active_chats[user_id],
                    text=update.message.text
                )
            else:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=update.message.text,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Ответить", callback_data=f"start_{user_id}")
                    ]])
                )

def main():
    chat_manager = ChatManager()
    
    try:
        app = ApplicationBuilder() \
            .token(BOT_TOKEN) \
            .concurrent_updates(True) \
            .build()

        # Регистрация обработчиков
        app.add_handler(CallbackQueryHandler(chat_manager.start_chat, pattern="^start_"))
        app.add_handler(CallbackQueryHandler(chat_manager.close_chat, pattern="^close_"))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_manager.handle_message))

        logger.info("Бот запущен (режим polling)...")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            close_loop=False,
            stop_signals=None  # Важно для Render.com
        )
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")

if __name__ == '__main__':
    main()
