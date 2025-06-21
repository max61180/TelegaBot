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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN', '7768583912:AAEJ51jQ5ayuC3yuclzpSbFEbnfM4gz5rr8')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1642268174'))

class ChatManager:
    def __init__(self):
        self.user_chats = {}  # {user_id: chat_id}

    async def create_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создает новый чат при нажатии кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.data.split('_')[1]
        
        try:
            # Создаем новый чат (в реальности - приватный чат бота с админом)
            chat = await context.bot.create_chat_invite_link(
                chat_id=ADMIN_ID,
                name=f"Чат с {user_id}"
            )
            
            self.user_chats[user_id] = chat.invite_link
            
            # Отправляем приглашение админу
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔹 Новый чат с {user_id}\n"
                     f"Используйте эту ссылку: {chat.invite_link}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Открыть чат", url=chat.invite_link)
                ]])
            )
            
            # Уведомляем пользователя
            await query.edit_message_text(
                text=f"✅ Чат создан! Оператор скоро свяжется",
                reply_markup=None
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания чата: {e}")
            await query.edit_message_text("❌ Ошибка создания чата")

    async def forward_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пересылает сообщения в нужный чат"""
        if '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            
            if user_id in self.user_chats:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=update.message.text,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Ответить в чате", url=self.user_chats[user_id])
                    ]])
                )

def main():
    chat_manager = ChatManager()
    
    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .build()

    app.add_handler(CallbackQueryHandler(chat_manager.create_chat, pattern="^create_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_manager.forward_message))

    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
