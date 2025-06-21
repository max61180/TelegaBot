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
        self.active_chats = {}  # {user_id: chat_title}

    async def create_group_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создает новую группу для общения"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.data.split('_')[1]
        chat_title = f"Чат с {user_id}"
        
        try:
            # Создаем новую группу
            chat = await context.bot.create_new_chat(
                title=chat_title,
                user_ids=[ADMIN_ID]  # Бот автоматически добавляется как администратор
            )
            
            self.active_chats[user_id] = chat.title
            
            # Получаем ссылку-приглашение
            invite_link = await chat.export_invite_link()
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔹 Создана новая группа: {chat_title}\n"
                     f"Ссылка для присоединения: {invite_link}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Открыть чат", url=invite_link)
                ]])
            )
            
            await query.edit_message_text(
                text="✅ Групповой чат создан! Оператор свяжется с вами.",
                reply_markup=None
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания группы: {e}")
            await query.edit_message_text("❌ Не удалось создать групповой чат")

    async def forward_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пересылает сообщения в группу"""
        if update.message and '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            
            if user_id in self.active_chats:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"Сообщение из чата '{self.active_chats[user_id]}':\n{update.message.text}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            "Перейти в чат",
                            url=f"https://t.me/{self.active_chats[user_id].replace(' ', '_')}"
                        )
                    ]])
                )

def main():
    chat_manager = ChatManager()
    
    app = (ApplicationBuilder()
           .token(BOT_TOKEN)
           .concurrent_updates(True)
           .build())

    app.add_handler(CallbackQueryHandler(
        chat_manager.create_group_chat,
        pattern="^newchat_"
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        chat_manager.forward_to_group
    ))

    logger.info("Бот запущен в режиме групповых чатов")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False
    )

if __name__ == '__main__':
    main()
