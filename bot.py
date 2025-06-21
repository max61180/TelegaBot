import os
import sqlite3
import asyncio
import threading
from fastapi import FastAPI
import uvicorn
from telegram import Update, Bot
from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Конфигурация из переменных окружения
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
PORT = int(os.environ.get("PORT", 8000))

# Проверка наличия обязательных переменных
assert BOT_TOKEN, "BOT_TOKEN не задан"
assert ADMIN_ID, "ADMIN_ID не задан"

# Инициализация FastAPI
app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "Bot is running", "admin_id": ADMIN_ID}

async def handle_accept_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик принятия чата администратором"""
    query = update.callback_query
    try:
        user_id = query.data.replace('accept_', '')
        
        # Сохраняем связь user_id и chat_id в БД
        conn.execute("INSERT OR REPLACE INTO user_chats VALUES (?, ?)", 
                    (user_id, str(query.message.chat.id)))
        conn.commit()
        
        await query.answer(f"Чат с {user_id} принят")
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=f"Вы приняли чат с {user_id}. Теперь все сообщения будут приходить сюда."
        )
    except Exception as e:
        print(f"Ошибка обработки callback: {e}")
        await query.answer("Ошибка принятия чата")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик входящих сообщений"""
    try:
        if not update.message or not update.message.text:
            return
            
        # Игнорируем сообщения от самого бота
        if update.message.from_user.id == context.bot.id:
            return
            
        # Проверяем, относится ли сообщение к какому-либо чату
        if '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            cursor = conn.execute(
                "SELECT chat_id FROM user_chats WHERE user_id = ?", 
                (user_id,)
            )
            chat_data = cursor.fetchone()
            
            if chat_data:
                await context.bot.send_message(
                    chat_id=int(chat_data[0]),
                    text=update.message.text
                )
    except Exception as e:
        print(f"Ошибка обработки сообщения: {e}")

async def run_bot():
    """Запуск Telegram бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CallbackQueryHandler(
        handle_accept_callback, 
        pattern="^accept_"
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    await application.initialize()
    await application.start()
    print(f"🔐 Бот запущен. Администратор: {ADMIN_ID}")
    
    # Бесконечный цикл
    while True:
        await asyncio.sleep(3600)

async def main():
    """Запуск всех компонентов"""
    # HTTP-сервер для Render
    server = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": app, "host": "0.0.0.0", "port": PORT},
        daemon=True
    )
    server.start()
    
    # Основной бот
    await run_bot()

if __name__ == "__main__":
    # Инициализация БД
    conn = sqlite3.connect('chats.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS user_chats
                 (user_id TEXT PRIMARY KEY, chat_id TEXT)''')
    
    try:
        asyncio.run(main())
    except KeyError as e:
        print(f"🚨 Критическая ошибка: Не задана переменная окружения {e}")
        exit(1)
    except Exception as e:
        print(f"🚨 Ошибка запуска: {e}")
        exit(1)
