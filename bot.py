from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)
import sqlite3
import os
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Настройка БД (с асинхронной поддержкой)
conn = sqlite3.connect('chats.db', check_same_thread=False)
conn.execute('''CREATE TABLE IF NOT EXISTS user_chats
             (user_id TEXT PRIMARY KEY, chat_id TEXT)''')

async def create_user_chat(bot, user_id: str):
    chat = await bot.create_chat(
        title=f"Клиент {user_id}",
        user_ids=[ADMIN_ID]  # Приглашаем админа сразу
    )
    conn.execute("INSERT OR REPLACE INTO user_chats VALUES (?, ?)", (user_id, chat.id))
    conn.commit()
    return chat.id

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        if '👤' in text:
            user_id = text.split('👤 ')[1].split(':')[0]
            cursor = conn.execute("SELECT chat_id FROM user_chats WHERE user_id = ?", (user_id,))
            chat_id = cursor.fetchone()
            
            if not chat_id:
                chat_id = await create_user_chat(context.bot, user_id)
            else:
                chat_id = chat_id[0]
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=text
            )
    except Exception as e:
        print(f"Ошибка: {e}")

async def main():
    # Создаем Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # Запускаем бота
    await application.initialize()
    await application.start()
    print("✅ Бот успешно запущен!")
    
    # Бесконечный цикл
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
