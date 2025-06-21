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
        """Создает групповой чат для пользователя"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.data.split('_')[1]
        
        try:
            # Создаем новую группу (бот + админ)
            chat = await context.bot.create_new_chat_invite_link(
                title=f"Чат с {user_id}",
                user_ids=[ADMIN_ID]
            )
            
            self.active_chats[user_id] = chat.chat.id
            invite_link = await chat.chat.export_invite_link()
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔹 Новый чат с {user_id}\nСсылка: {invite_link}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Открыть чат", url=invite_link)
                ]])
            )
            
            await query.edit_message_text(
                text="✅ Чат создан! Оператор свяжется с вами в новом окне.",
                reply_markup=None
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания чата: {e}")
            await query.edit_message_text("❌ Не удалось создать чат")

    async def forward_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пересылает сообщения в соответствующий чат"""
        if '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            
            if user_id in self.active_chats:
                await context.bot.send_message(
                    chat_id=self.active_chats[user_id],
                    text=update.message.text
                )

def main():
    chat_manager = ChatManager()
    
    # Важные параметры для Render:
    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .concurrent_updates(True) \  # Разрешаем параллельные запросы
        .http_version('1.1') \  # Стабильная версия HTTP
        .get_updates_http_version('1.1') \
        .build()

    # Обработчики
    app.add_handler(CallbackQueryHandler(
        chat_manager.create_chat, 
        pattern="^newchat_"
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        chat_manager.forward_message
    ))

    logger.info("Бот запущен в режиме polling (Render-compatible)")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,  # Критично для Render!
        stop_signals=[]    # Отключаем обработку сигналов остановки
    )

if __name__ == '__main__':
    main()
