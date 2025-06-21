import sqlite3
import asyncio
import threading
from fastapi import FastAPI
import uvicorn
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# =============================================
# КОНФИГУРАЦИЯ (ВАШИ ДАННЫЕ)
# =============================================
BOT_TOKEN = "7768583912:AAEdz3fxwRAEE2IXW2lNdx5gwa1PDIKQa0o"  # Ваш токен из @BotFather
ADMIN_ID = 1642268174  # Ваш ID из @userinfobot
PORT = 8000  # Порт для Render
# =============================================

# Инициализация БД
conn = sqlite3.connect('chats.db', check_same_thread=False)
conn.execute('''CREATE TABLE IF NOT EXISTS user_chats
             (user_id TEXT PRIMARY KEY, chat_id TEXT)''')

# FastAPI для проверки порта
app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "Bot is alive", "bot": "@your_bot_username"}

async def create_user_chat(bot, user_id: str):
    """Создает приватный чат с админом"""
    chat = await bot.create_chat(
        title=f"Клиент {user_id[:6]}...",
        user_ids=[ADMIN_ID]
    )
    conn.execute("INSERT OR REPLACE INTO user_chats VALUES (?, ?)", (user_id, chat.id))
    conn.commit()
    return chat.id

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений"""
    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text
        if '👤' in text:
            user_id = text.split('👤 ')[1].split(':')[0]
            chat_id = conn.execute(
                "SELECT chat_id FROM user_chats WHERE user_id = ?", 
                (user_id,)
            ).fetchone()

            if not chat_id:
                chat_id = await create_user_chat(context.bot, user_id)
            else:
                chat_id = chat_id[0]

            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"🚨 Ошибка: {e}")

async def run_bot():
    """Запуск Telegram бота"""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await app.initialize()
    await app.start()
    print(f"🤖 Бот @your_bot_username запущен! Admin ID: {ADMIN_ID}")
    
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
    asyncio.run(main())
