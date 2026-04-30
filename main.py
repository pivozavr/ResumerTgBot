import time
from google.genai.errors import ServerError
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
import sqlite3
from google import genai
import datetime
from dotenv import load_dotenv
import re
import os
from cryptography.fernet import Fernet





load_dotenv()

api_key = os.getenv("API_KEY")
bot_token = os.getenv("BOT_TOKEN")
key = os.getenv("ENC_CODE").encode()
cipher = Fernet(key)

client = genai.Client(api_key=api_key)
app = ApplicationBuilder().token(bot_token).build()

difs = {1: "Кратко (только суть)", 2: "Средне (с аргументами)", 3: "Подробно (с разбором каждой темы)"}
curencys = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}

def encrypt(text: str) -> str:
    return cipher.encrypt(text.encode()).decode()

def decrypt(text: str) -> str:
    return cipher.decrypt(text.encode()).decode()

def generate_with_retry(client, prompt, retries=5):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )
            return response.text

        except ServerError as e:
            if attempt == retries - 1:
                raise e

            wait = 2 ** attempt  # экспоненциальная задержка
            time.sleep(wait)

    return None


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id, "Ожидайте")

    connection = sqlite3.connect("messages.db")
    crsr = connection.cursor()

    dif_id = 1

    # 🔹 ЛОГИКА ПАРСИНГА
    if len(context.args) == 2:
        # /resume 100 2
        dif_id = int(context.args[0])
        amount = int(context.args[1])

        crsr.execute("""
            SELECT * FROM (
                SELECT *
                FROM messages
                WHERE chat_id = ?
                ORDER BY date DESC
                LIMIT ?
            )
            ORDER BY date ASC;
        """, (chat_id, amount))

    elif len(context.args) == 3:
        # /resume 2 1 h
        dif_id = int(context.args[0])
        amount = int(context.args[1])
        curency = context.args[2]

        dt = datetime.datetime.now() - datetime.timedelta(
            seconds=amount * curencys[curency]
        )

        crsr.execute("""
            SELECT *
            FROM messages
            WHERE chat_id = ?
              AND date >= ?
            ORDER BY date ASC
        """, (chat_id, dt.strftime('%Y-%m-%d %H:%M:%S')))

    else:
        # дефолт
        crsr.execute("""
            SELECT * FROM (
                SELECT *
                FROM messages
                WHERE chat_id = ?
                ORDER BY date DESC
                LIMIT 50
            )
            ORDER BY date ASC;
        """, (chat_id,))

    rows = crsr.fetchall()
    connection.close()

    messages = "\n".join(
        f"{m[1]}: {decrypt(m[2])} : {m[3]}" for m in rows
    )

    text = generate_with_retry(client, f""" 
    Проанализируй историю нашей переписки и составь резюме (summary). 

    Параметры анализа: Уровень подробности: {difs[dif_id]}. 

    Идентификация: Обязательно указывай никнеймы или имена участников, когда приписываешь им конкретные тезисы или позиции. 

    Формат отчета: 

    Основная тема: Суть дискуссии в одном предложении. 

    Позиции участников: Кто что утверждал? Оформи списком (например, Ник: краткая позиция). 

    Точки соприкосновения и конфликты: В чем мнения совпали, а в чем возник спор? 

    Итоги и решения: Чем закончился диалог или к чему пришли. 

    Пиши объективно, сохраняй контекст и избегай лишних вводных фраз. {messages} """)

    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.*?)__", r"<i>\1</i>", text)

    await context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, """
Формат использования команды:
/resume <уровень> <количество> — по последним сообщениям
/resume <уровень> <время> <единица> — за период
Уровень - уровень сложности выжимки, от 1 до 3, где 1 - самая краткая и 3 - самая подробная
Единицы времени - s - секунды, m - минуты, h - часы, d - дни, w - недели 
Примеры:
/resume 3 100 — последние 100 сообщений очень подробно
/resume 1 2 h — за последние 2 часа очень кратко""")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, """
Привет! Я бот для анализа переписок.

Я могу:
— сохранять сообщения из чата
— делать краткие и подробные резюме диалогов
— выделять ключевые темы и позиции участников

Добавь меня в группу и выдай права администратора, чтобы я мог видеть все сообщения и работать корректно.

Команда:
/resume — получить резюме переписки
/help — гайд по использованию команд""")


async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message:
        origin = message.forward_origin

        if origin:
            if origin.type == "user":
                username = origin.sender_user.username or origin.sender_user.first_name

            elif origin.type == "hidden_user":
                username = origin.sender_name  # только строка

            elif origin.type in ["chat", "channel"]:
                username = origin.chat.title
            else:
                username = "Anonim"
        else:
            username = message.from_user.full_name.split(" ")[0]

        print(username)

        text = encrypt(message.text)
        chat_id = message.chat.id
        date = message.date.strftime('%Y-%m-%d %H:%M:%S')

        connection = sqlite3.connect("messages.db")
        crsr = connection.cursor()
        sql_command = f"""INSERT INTO messages VALUES ({chat_id}, "{username}","{text}","{date}");"""
        crsr.execute(sql_command)
        connection.commit()
        connection.close()


def main():
    app.add_handler(CommandHandler("resume", resume_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.ALL, save_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()