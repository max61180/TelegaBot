import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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

# Конфигурация (убедитесь, что эти значения верные!)
BOT_TOKEN = os.getenv('BOT_TOKEN', '7768583912:AAEJ51jQ5ayuC3yuclzpSbFEbnfM4gz5rr8')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1642268174'))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Обработка кнопки "Ответить"
    if query.data == 'test':
        await query.edit_message_text(
            text=f"✅ Вы нажали кнопку!\nЧат активирован.\nОтправьте ответное сообщение:",
            reply_markup=None
        )
        
        # Можно сохранить состояние чата
        context.user_data['active_chat'] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id == ADMIN_ID:
        # Если это ответ администратора
        if 'active_chat' in context.user_data:
            await update.message.reply_text(
                "Ваше сообщение будет отправлено пользователю",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Закрыть чат", callback_data="close_chat")
                ]])
            )

if __name__ == '__main__':
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        app.add_handler(CallbackQueryHandler(handle_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Бот запущен и готов к работе!")
        app.run_polling()
        
    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")
