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

BOT_TOKEN = os.getenv('BOT_TOKEN', '7768583912:AAEJ51jQ5ayuC3yuclzpSbFEbnfM4gz5rr8')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1642268174'))

class ChatManager:
    def __init__(self):
        self.active_chats = {}  # {user_id: chat_id}

    async def create_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки 'Создать чат'"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.data.split('_')[1]
        
        try:
            # Создаем новый чат (в продакшене используйте create_forum_topic или create_supergroup)
            chat = await context.bot.create_chat_invite_link(
                chat_id=ADMIN_ID,
                name=f"Чат с {user_id}"
            )
            
            self.active_chats[user_id] = chat.invite_link
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔹 Новый чат с {user_id}\nСсылка: {chat.invite_link}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Открыть чат", url=chat.invite_link)
                ]])
            )
            
            await query.edit_message_text("✅ Чат создан! Оператор свяжется с вами.")
            
        except Exception as e:
            logger.error(f"Ошибка создания чата: {e}")
            await query.edit_message_text("❌ Ошибка создания чата")

    async def forward_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пересылка сообщений"""
        if update.message and '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            
            if user_id in self.active_chats:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=update.message.text,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Ответить", url=self.active_chats[user_id])
                    ]])
                )

def main():
    chat_manager = ChatManager()
    
    # Инициализация бота (без переносов строк)
    app = (ApplicationBuilder()
           .token(BOT_TOKEN)
           .concurrent_updates(True)  # Разрешаем параллельные запросы
           .http_version('1.1')
           .get_updates_http_version('1.1')
           .build())

    # Регистрация обработчиков
    app.add_handler(CallbackQueryHandler(chat_manager.create_chat, pattern="^newchat_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_manager.forward_message))

    logger.info("Бот запущен (Render-compatible mode)")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        stop_signals=[]
    )

if __name__ == '__main__':
    main()
