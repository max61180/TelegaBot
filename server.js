 
const express = require('express');
const axios = require('axios');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());

// Состояние ботов (в реальном проекте используйте БД, например, PostgreSQL)
const bots = [
    { id: 'bot1', token: process.env.BOT1_TOKEN, isFree: true, sessionId: null, lastActivity: null },
    { id: 'bot2', token: process.env.BOT2_TOKEN, isFree: true, sessionId: null, lastActivity: null }
];

// Проверка бездействия (каждые 10 минут)
setInterval(() => {
    const threeHoursAgo = Date.now() - 3 * 60 * 60 * 1000;
    bots.forEach(bot => {
        if (bot.lastActivity && bot.lastActivity < threeHoursAgo) {
            bot.isFree = true;
            bot.sessionId = null;
            console.log(`Бот ${bot.id} освобождён по таймауту.`);
        }
    });
}, 10 * 60 * 1000);

// Маршруты API
app.post('/get-bot', (req, res) => {
    const { sessionId } = req.body;
    const freeBot = bots.find(bot => bot.isFree);

    if (freeBot) {
        freeBot.isFree = false;
        freeBot.sessionId = sessionId;
        freeBot.lastActivity = Date.now();
        res.json({ botToken: freeBot.token });
    } else {
        res.status(503).json({ error: 'Нет свободных ботов' });
    }
});

app.post('/free-bot', (req, res) => {
    const { sessionId } = req.body;
    const bot = bots.find(b => b.sessionId === sessionId);
    
    if (bot) {
        bot.isFree = true;
        bot.sessionId = null;
        console.log(`Бот ${bot.id} освобождён.`);
    }
    res.sendStatus(200);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Сервер запущен на порту ${PORT}`));
