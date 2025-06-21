import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
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
        # Хранилище: user_id -> group_id
        self.active_chats = {}
        self.lock = asyncio.Lock()

    async def handle_start_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки 'Создать групповой чат'"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.data.split('_')[1]
        
        try:
            # Информируем администратора
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔹 Пользователь {user_id} запросил создание группового чата.\n\n"
                     "1. Создайте новую группу в Telegram\n"
                     "2. Добавьте этого бота в группу\n"
                     "3. Получите ID группы с помощью @RawDataBot\n"
                     "4. Отправьте команду: /setgroup_{user_id} [ID_группы]\n"
                     f"Пример: <code>/setgroup_{user_id} -1001234567890</code>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Создать группу", url="tg://create")
                ]])
            )
            
            # Подтверждаем пользователю
            await query.edit_message_text(
                text="✅ Запрос отправлен администратору. Вы получите приглашение в группу после её создания.",
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}")
            await query.edit_message_text("❌ Ошибка обработки запроса. Попробуйте позже.")

    async def handle_set_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /setgroup_user123"""
        if update.message.from_user.id != ADMIN_ID:
            return
            
        text = update.message.text
        if not text.startswith('/setgroup_'):
            return
            
        try:
            # Извлекаем user_id и group_id из команды
            parts = text.split('_', 2)
            user_id = parts[1]
            group_id = parts[2].strip()
            
            # Проверяем валидность group_id
            if not group_id.startswith('-100'):
                raise ValueError("Некорректный ID группы")
            
            # Сохраняем в словарь (с блокировкой)
            async with self.lock:
                self.active_chats[user_id] = group_id
                
            # Отправляем подтверждение
            await update.message.reply_text(
                f"✅ Группа настроена для пользователя {user_id}\n"
                f"ID группы: {group_id}\n\n"
                "Теперь все сообщения будут пересылаться в эту группу."
            )
            
            # Отправляем приглашение пользователю (если бы у нас был его chat_id, но у нас нет)
            # Вместо этого отправляем сообщение в веб-чат через другой механизм (не реализовано)
            
        except (IndexError, ValueError) as e:
            logger.error(f"Ошибка формата команды: {e}")
            await update.message.reply_text(
                "❌ Неверный формат команды. Используйте:\n"
                "<code>/setgroup_&lt;user_id&gt; &lt;group_id&gt;</code>\n"
                "Пример: <code>/setgroup_user-abc123 -1001234567890</code>",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Общая ошибка при обработке команды: {e}")
            await update.message.reply_text("❌ Произошла непредвиденная ошибка")

    async def forward_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пересылка сообщений в группу"""
        if not update.message or not update.message.text:
            return
            
        text = update.message.text
        if '👤' not in text:
            return
            
        try:
            # Извлекаем user_id из сообщения
            user_id = text.split('👤 ')[1].split(':')[0]
            
            # Ищем группу для этого пользователя
            async with self.lock:
                group_id = self.active_chats.get(user_id)
            
            if group_id:
                await context.bot.send_message(
                    chat_id=group_id,
                    text=text
                )
        except Exception as e:
            logger.error(f"Ошибка пересылки: {e}")

    async def handle_new_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений из групп (не реализовано)"""
        # Здесь можно добавить логику для ответа пользователю через веб-чат
        pass

def main():
    chat_manager = ChatManager()
    
    # Создаем приложение с поддержкой конкурентных обновлений
    app = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()
    
    # Регистрируем обработчики
    app.add_handler(CallbackQueryHandler(chat_manager.handle_start_chat, pattern="^newchat_"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^/setgroup_'), chat_manager.handle_set_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_manager.forward_to_group))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, chat_manager.handle_new_group_message))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        stop_signals=[],
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
