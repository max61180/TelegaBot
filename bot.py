import os
import sqlite3
import asyncio
from telegram import Update, Bot
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

# Инициализация FastAPI
app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "Bot is running"}

# Инициализация БД
def init_db():
    conn = sqlite3.connect('chats.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS user_chats
                 (user_id TEXT PRIMARY KEY, chat_id TEXT)''')
    return conn

conn = init_db()

async def handle_accept_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        # Извлекаем user_id из callback_data (формат: "accept_USER123")
        user_id = query.data.split('_')[1]
        
        # Сохраняем связь user_id и текущего чата (куда нажали кнопку)
        conn.execute("INSERT OR REPLACE INTO user_chats VALUES (?, ?)", 
                    (user_id, str(query.message.chat.id)))
        conn.commit()
        
        # Отправляем подтверждение
        await query.answer()
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=f"✅ Вы приняли чат с {user_id}\nТеперь все сообщения будут приходить сюда."
        )
        
        # Отправляем уведомление пользователю (если реализован механизм обратной связи)
    except Exception as e:
        print(f"❌ Ошибка в handle_accept_callback: {e}")
        await query.answer("Ошибка при принятии чата")

async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
            
        # Игнорируем сообщения от самого бота
        if update.message.from_user.id == context.bot.id:
            return
            
        # Если сообщение содержит метку пользователя (👤 user-123e4567)
        if '👤' in update.message.text:
            user_id = update.message.text.split('👤 ')[1].split(':')[0]
            
            # Ищем chat_id в базе данных
            cursor = conn.execute(
                "SELECT chat_id FROM user_chats WHERE user_id = ?", 
                (user_id,)
            )
            chat_data = cursor.fetchone()
            
            if chat_data:
                # Пересылаем сообщение в сохраненный чат
                await context.bot.send_message(
                    chat_id=int(chat_data[0]),
                    text=update.message.text
                )
            else:
                # Если чат еще не принят, предлагаем принять
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"Новый запрос чата от {user_id}:\n\n{update.message.text}",
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
        print(f"❌ Ошибка в handle_new_message: {e}")

async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
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
    print(f"🤖 Бот запущен. Админ: {ADMIN_ID}")
    
    while True:
        await asyncio.sleep(3600)

async def main():
    # HTTP-сервер для Render
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
        print(f"🚨 FATAL ERROR: {e}")
        exit(1)
