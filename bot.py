import os
import sqlite3
import asyncio
import threading  # Добавлен этот импорт
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from fastapi import FastAPI
import uvicorn

# Конфигурация из переменных окружения
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
PORT = int(os.environ.get("PORT", 8000))

# Проверка конфигурации
assert BOT_TOKEN, "BOT_TOKEN не задан"
assert ADMIN_ID, "ADMIN_ID не задан"

# Инициализация FastAPI
app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "Bot is running", "admin_id": ADMIN_ID}

# Инициализация БД
def init_db():
    conn = sqlite3.connect('chats.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS user_chats
                 (user_id TEXT PRIMARY KEY, chat_id TEXT)''')
    return conn

conn = init_db()

async def handle_accept_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки принятия чата"""
    query = update.callback_query
    try:
        user_id = query.data.split('_')[1]
        
        # Сохраняем связь user_id → chat_id
        conn.execute("INSERT OR REPLACE INTO user_chats VALUES (?, ?)", 
                    (user_id, str(query.message.chat.id)))
        conn.commit()
        
        await query.answer(f"Чат с {user_id} принят")
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=f"✅ Вы приняли чат с {user_id}\nТеперь все сообщения будут приходить сюда."
        )
    except Exception as e:
        print(f"❌ Ошибка при принятии чата: {e}")
        await query.answer("Произошла ошибка")

async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик входящих сообщений"""
    try:
        if not update.message or not update.message.text:
            return
            
        # Игнорируем сообщения от бота
        if update.message.from_user.id == context.bot.id:
            return
            
        if '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            cursor = conn.execute(
                "SELECT chat_id FROM user_chats WHERE user_id = ?", 
                (user_id,)
            )
            chat_data = cursor.fetchone()
            
            if chat_data:
                # Пересылаем в существующий чат
                await context.bot.send_message(
                    chat_id=int(chat_data[0]),
                    text=update.message.text
                )
            else:
                # Предлагаем администратору принять чат
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🔔 Новый запрос чата от {user_id}:\n\n{update.message.text}",
                    reply_markup={
                        "inline_keyboard": [[
                            {
                                "text": "✅ Принять чат",
                                "callback_data": f"accept_{user_id}"
                            }
                        ]]
                    }
                )
    except Exception as e:
        print(f"❌ Ошибка обработки сообщения: {e}")

async def run_bot():
    """Запуск Telegram бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CallbackQueryHandler(
        handle_accept_callback, 
        pattern="^accept_"
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_new_message
    ))
    
    await application.initialize()
    await application.start()
    print(f"🤖 Бот запущен. Админ ID: {ADMIN_ID}")
    
    while True:
        await asyncio.sleep(3600)

async def main():
    """Запуск всех компонентов"""
    # HTTP-сервер в отдельном потоке
    server = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": app, "host": "0.0.0.0", "port": PORT},
        daemon=True
    )
    server.start()
    
    # Основной бот
    await run_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"🚨 Критическая ошибка: {e}")
        exit(1)
