import os
import sqlite3
import asyncio
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from fastapi import FastAPI
import uvicorn

# Конфигурация
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
PORT = int(os.environ.get("PORT", 8000))

# Инициализация
app = FastAPI()
conn = sqlite3.connect('chats.db', check_same_thread=False)
conn.execute('''CREATE TABLE IF NOT EXISTS chats
             (user_id TEXT PRIMARY KEY, chat_id TEXT, status TEXT)''')

async def accept_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.data.split('_')[1]
    admin_chat_id = str(query.message.chat.id)
    
    try:
        # Создаем новый чат (в реальности используем текущий чат с админом)
        conn.execute("INSERT OR REPLACE INTO chats VALUES (?, ?, ?)",
                    (user_id, admin_chat_id, "active"))
        conn.commit()
        
        # Удаляем кнопку "Принять"
        await query.edit_message_reply_markup(reply_markup=None)
        
        # Отправляем подтверждение
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=f"✅ Чат с {user_id} активирован\nОтправьте сообщение:"
        )
        
    except Exception as e:
        print(f"Error accepting chat: {e}")
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text="❌ Ошибка при активации чата"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
            
        # Сообщения от пользователей (формат "👤 user-123: текст")
        if '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            
            # Проверяем статус чата
            cursor = conn.execute("SELECT status FROM chats WHERE user_id = ?", (user_id,))
            chat_status = cursor.fetchone()
            
            if not chat_status:
                # Если чат не принят, предлагаем кнопку
                keyboard = [[InlineKeyboardButton("✅ Принять чат", callback_data=f"accept_{user_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"Новый запрос от {user_id}:\n{update.message.text}",
                    reply_markup=reply_markup
                )
            elif chat_status[0] == "active":
                # Если чат активен, пересылаем сообщение
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=update.message.text
                )
                
    except Exception as e:
        print(f"Message handling error: {e}")

async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(accept_chat, pattern="^accept_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await application.initialize()
    await application.start()
    print("🤖 Бот запущен и готов к работе")

async def main():
    server = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": app, "host": "0.0.0.0", "port": PORT},
        daemon=True
    )
    server.start()
    await run_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"🚨 Ошибка: {e}")
        exit(1)
