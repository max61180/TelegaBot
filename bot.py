from telegram import Update, Bot, Chat
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext.filters import TEXT
import sqlite3
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Настройка БД
conn = sqlite3.connect('chats.db')
conn.execute('''CREATE TABLE IF NOT EXISTS user_chats
             (user_id TEXT PRIMARY KEY, chat_id TEXT)''')

async def create_user_chat(bot: Bot, user_id: str):
    chat = await bot.create_chat(title=f"Клиент {user_id}", type=Chat.PRIVATE)
    await bot.add_chat_members(chat.id, [ADMIN_ID])
    conn.execute("INSERT INTO user_chats VALUES (?, ?)", (user_id, chat.id))
    conn.commit()
    return chat.id

async def handle_message(update: Update, context):
    try:
        text = update.message.text
        if '👤' in text:
            user_id = text.split('👤 ')[1].split(':')[0]
            chat_id = conn.execute("SELECT chat_id FROM user_chats WHERE user_id = ?", (user_id,)).fetchone()
            
            if not chat_id:
                chat_id = await create_user_chat(context.bot, user_id)
            else:
                chat_id = chat_id[0]
            
            await context.bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print("Ошибка:", e)

updater = Updater(BOT_TOKEN)
updater.dispatcher.add_handler(MessageHandler(TEXT, handle_message))
updater.start_polling()
print("Бот запущен!")
