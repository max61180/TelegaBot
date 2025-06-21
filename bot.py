import os
import sqlite3
import asyncio
import threading
from telegram import Update, Bot
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
conn.execute('''CREATE TABLE IF NOT EXISTS user_chats
             (user_id TEXT PRIMARY KEY, chat_id TEXT, admin_chat_id TEXT)''')

@app.get("/")
def health_check():
    return {"status": "Bot is running"}

async def accept_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        user_id = query.data.split('_')[1]
        
        # Создаем новый чат между ботом и администратором
        chat = await context.bot.create_chat_invite_link(
            chat_id=ADMIN_ID,
            name=f"Чат с {user_id}"
        )
        
        # Сохраняем данные
        conn.execute("INSERT OR REPLACE INTO user_chats VALUES (?, ?, ?)",
                    (user_id, str(chat.chat.id), str(query.message.chat.id)))
        conn.commit()
        
        # Отправляем подтверждение
        await query.answer("Чат создан!")
        await context.bot.send_message(
            chat_id=chat.chat.id,
            text=f"🔹 Чат с пользователем {user_id} создан\n\n"
                 "Отправьте сюда сообщение для пользователя:"
        )
        
        # Уведомляем пользователя
        await context.bot.send_message(
            chat_id=int(ADMIN_ID),
            text=f"👤 Пользователь {user_id} ожидает ответа в новом чате"
        )
        
    except Exception as e:
        print(f"Error in accept_chat: {e}")
        await query.answer("Ошибка создания чата")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
            
        # Сообщения от пользователя
        if '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            data = conn.execute(
                "SELECT chat_id, admin_chat_id FROM user_chats WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            if data:
                # Пересылаем в созданный чат
                await context.bot.send_message(
                    chat_id=int(data[0]),
                    text=update.message.text
                )
            else:
                # Предлагаем создать чат
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"Новый запрос от {user_id}:\n{update.message.text}",
                    reply_markup={
                        "inline_keyboard": [[
                            {"text": "✅ Создать чат", "callback_data": f"accept_{user_id}"}
                        ]]
                    }
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
