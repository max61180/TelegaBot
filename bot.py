import os
import sqlite3
import asyncio
from fastapi import FastAPI
import uvicorn
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# =============================================
# КОНФИГУРАЦИЯ (ТОЛЬКО ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ)
# =============================================
BOT_TOKEN = os.environ["BOT_TOKEN"]  # Обязательная переменная
ADMIN_ID = int(os.environ["ADMIN_ID"])  # Обязательная переменная
PORT = 8000
# =============================================

# Проверка наличия критических переменных
assert BOT_TOKEN != "", "BOT_TOKEN не задан!"
assert ADMIN_ID != 0, "ADMIN_ID не задан!"

# Инициализация FastAPI
app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "Secure bot active", "admin": ADMIN_ID}

# ... (остальной код обработчиков без изменений) ...

async def run_bot():
    """Запуск Telegram бота"""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await app.initialize()
    await app.start()
    print(f"🔐 Бот запущен. Доступ только для admin_id: {ADMIN_ID}")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyError as e:
        print(f"🚨 Критическая ошибка: Не задана переменная окружения {e}")
        exit(1)
