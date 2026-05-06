import asyncio
import time
from google.genai.errors import ServerError
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler, InlineQueryHandler
import sqlite3
from google import genai
import datetime
from dotenv import load_dotenv
import re
import os
from cryptography.fernet import Fernet
import html




load_dotenv()

api_key = os.getenv("API_KEY")
bot_token = os.getenv("BOT_TOKEN")
key = os.getenv("ENC_CODE").encode()
cipher = Fernet(key)

client = genai.Client(api_key=api_key)
app = ApplicationBuilder().token(bot_token).build()

difs = {1: "Кратко (только суть)", 2: "Средне (с аргументами)", 3: "Подробно (с разбором каждой темы)"}
currencies = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}





def encrypt(text: str) -> str:
    return cipher.encrypt(text.encode()).decode()

def decrypt(text: str) -> str:
    try:
        return cipher.decrypt(text.strip().encode()).decode()
    except:
        return text

async def generate_with_retry(client, prompt, retries=5):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )
            return response.text


        except Exception as e:

            error_text = str(e)

            if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text or "quota" in error_text.lower():
                return "ОПА! Превышен лимит токенов/квоты API. Запрос временно недоступен."


            if attempt == retries - 1:
                return "ОПА! Ошибка после всех попыток. Запрос не выполнен."

            wait = 2 ** attempt  # экспоненциальная задержка
            await asyncio.sleep(wait)

    return None


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message_thread_id = -1
    if update.message.is_topic_message:
        message_thread_id = update.message.message_thread_id

    connection = sqlite3.connect("messages.db")
    crsr = connection.cursor()

    dif_id = 1

    # 🔹 ЛОГИКА ПАРСИНГА
    if len(context.args) == 2:
        if context.args[0].isdigit():
            if not (3 >= int(context.args[0]) >= 1):
                text = "Неправильный формат сложности"
                if update.message.is_topic_message:
                    return await context.bot.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id)
                else:
                    return await context.bot.send_message(chat_id=chat_id, text=text)
        else:
            text = "Неправильный формат сложности"
            if update.message.is_topic_message:
                return await context.bot.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id)
            else:
                return await context.bot.send_message(chat_id=chat_id, text=text)
        dif_id = int(context.args[0])
        if context.args[1].isdigit():
            if int(context.args[1])<=0:
                text = "Неправильно задано количество сообщений"
                if update.message.is_topic_message:
                    return await context.bot.send_message(chat_id=chat_id, text=text,
                                                          message_thread_id=message_thread_id)
                else:
                    return await context.bot.send_message(chat_id=chat_id, text=text)
        else:
            text = "Неправильно задано количество сообщений"
            if update.message.is_topic_message:
                return await context.bot.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id)
            else:
                return await context.bot.send_message(chat_id=chat_id, text=text)
        amount = int(context.args[1])

        crsr.execute("""
            SELECT * FROM (
                SELECT *
                FROM messages
                WHERE chat_id = ?
                    AND message_thread_id = ?
                ORDER BY date DESC
                LIMIT ?
            )
            ORDER BY date ASC;
        """, (chat_id ,message_thread_id, amount))

    elif len(context.args) == 3:
        # /resume 2 1 h
        if context.args[0].isdigit():
            if not (3 >= int(context.args[0]) >= 1):
                text = "Неправильный формат сложности"
                if update.message.is_topic_message:
                    return await context.bot.send_message(chat_id=chat_id, text=text,
                                                          message_thread_id=message_thread_id)
                else:
                    return await context.bot.send_message(chat_id=chat_id, text=text)
        else:
            text = "Неправильный формат сложности"
            if update.message.is_topic_message:
                return await context.bot.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id)
            else:
                return await context.bot.send_message(chat_id=chat_id, text=text)
        dif_id = int(context.args[0])
        if context.args[1].isdigit():
            if int(context.args[1]) <= 0:
                text = "Неправильно задано время"
                if update.message.is_topic_message:
                    return await context.bot.send_message(chat_id=chat_id, text=text,
                                                          message_thread_id=message_thread_id)
                else:
                    return await context.bot.send_message(chat_id=chat_id, text=text)
        else:
            text = "Неправильно задано время"
            if update.message.is_topic_message:
                return await context.bot.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id)
            else:
                return await context.bot.send_message(chat_id=chat_id, text=text)
        amount = int(context.args[1])
        curency = context.args[2]
        if curency not in currencies:
            return await context.bot.send_message(chat_id, "Неверная единица времени")

        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=amount * currencies[curency]
        )

        crsr.execute("""
            SELECT *
            FROM messages
            WHERE chat_id = ?
                AND message_thread_id = ?
                  AND date >= ?
            ORDER BY date ASC
        """, (chat_id, message_thread_id, dt.strftime('%Y-%m-%d %H:%M:%S')))

    else:
        # дефолт
        crsr.execute("""
            SELECT * FROM (
                SELECT *
                FROM messages
                WHERE chat_id = ?
                    AND message_thread_id = ?
                ORDER BY date DESC
                LIMIT 50
            )
            ORDER BY date ASC;
        """, (chat_id,message_thread_id))

    if update.message.is_topic_message:
        temp_msg = await context.bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text="Ожидайте")
    else:
        temp_msg = await context.bot.send_message(chat_id=chat_id, text="Ожидайте")

    rows = crsr.fetchall()

    if rows == []:
        text = "Не было найдено сообщений"
        if update.message.is_topic_message:
            await context.bot.delete_message(chat_id=chat_id, message_thread_id=message_thread_id, message_id=temp_msg.message_id)
            return await context.bot.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id,
                                           parse_mode=ParseMode.HTML)
        else:
            await context.bot.delete_message(chat_id=chat_id, message_id=temp_msg.message_id)
            return await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

    connection.close()

    messages = "\n".join(
        f"{m[2]}: {decrypt(m[3])} : {m[4]}" for m in rows
    )

    text = await generate_with_retry(client, f""" 
    Проанализируй историю нашей переписки и составь резюме (summary). 

    Параметры анализа: Уровень подробности: {difs[dif_id]}. 

    Идентификация: Обязательно указывай никнеймы или имена участников, когда приписываешь им конкретные тезисы или позиции. 

    Формат отчета: 

    Основная тема: Суть дискуссии в одном предложении. 

    Позиции участников: Кто что утверждал? Оформи списком (например, Ник: краткая позиция). 

    Точки соприкосновения и конфликты: В чем мнения совпали, а в чем возник спор? 

    Итоги и решения: Чем закончился диалог или к чему пришли. 

    Пиши объективно, сохраняй контекст и избегай лишних вводных фраз. {messages} """)
    text = html.escape(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.*?)__", r"<i>\1</i>", text)

    if update.message.is_topic_message:
        await context.bot.delete_message(chat_id=chat_id, message_thread_id=message_thread_id, message_id=temp_msg.message_id)
        await context.bot.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id, parse_mode=ParseMode.HTML)
    else:
        await context.bot.delete_message(chat_id=chat_id,message_id=temp_msg.message_id)
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.message.is_topic_message:
        message_thread_id = update.message.message_thread_id
        await context.bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id,text="""
Формат использования команды:
    /resume <уровень> <количество> — по последним сообщениям
    /resume <уровень> <время> <единица> — за период
    
Уровень - уровень сложности выжимки, от 1 до 3, где 1 - самая краткая и 3 - самая подробная
Единицы времени - s - секунды, m - минуты, h - часы, d - дни, w - недели 

Примеры:
    /resume 3 100 — последние 100 сообщений очень подробно
    /resume 1 2 h — за последние 2 часа очень кратко""")
    else:
        await context.bot.send_message(chat_id=chat_id, text="""
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
    if update.message.is_topic_message:
        message_thread_id = update.message.message_thread_id
        await context.bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text= """
Привет! Я бот для анализа переписок.

Я могу:
    — сохранять сообщения из чата
    — делать краткие и подробные резюме диалогов
    — выделять ключевые темы и позиции участников

Добавь меня в группу и выдай права администратора, чтобы я мог видеть все сообщения и работать корректно.

Команды:
    /resume — получить резюме переписки
    /help — гайд по использованию команд""")
    else:
        await context.bot.send_message(chat_id=chat_id,text="""
Привет! Я бот для анализа переписок.

Я могу:
    — сохранять сообщения из чата
    — делать краткие и подробные резюме диалогов
    — выделять ключевые темы и позиции участников

Добавь меня в группу и выдай права администратора, чтобы я мог видеть все сообщения и работать корректно.

Команды:
    /resume — получить резюме переписки
    /help — гайд по использованию команд""")


async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message:
        if message.text:
            origin = message.forward_origin
            if origin:
                if origin.type == "user":
                    username = origin.sender_user.first_name
                elif origin.type == "hidden_user":
                    username = origin.sender_user_name  # только строка
                elif origin.type in ["chat", "channel"]:
                    username = origin.chat.title
                else:
                    username = "Anonymous"
            else:
                username = message.from_user.first_name
            message_thread_id = -1
            if update.message.is_topic_message:
                message_thread_id = message.message_thread_id

            text = encrypt(message.text)
            chat_id = message.chat.id
            date = message.date.strftime('%Y-%m-%d %H:%M:%S')

            connection = sqlite3.connect("messages.db")
            crsr = connection.cursor()
            crsr.execute("""
                INSERT INTO messages VALUES (?, ?, ?, ?, ?)
            """, (chat_id, message_thread_id, username, text, date))
            connection.commit()
            connection.close()

async def inline_handler(update, context):
    results = [
        InlineQueryResultArticle(
            id="1",
            title="📊 Резюме последних сообщений",
            description="Например: сделать краткое резюме последних 50 сообщений",
            input_message_content=InputTextMessageContent(
                f"/resume 1 50"
            )
        ),
        InlineQueryResultArticle(
            id="2",
            title="⏱ Резюме за время",
            description="Например: подробная сводка за последние 2 часа",
            input_message_content=InputTextMessageContent(
                f"/resume 3 2 h"
            )
        )
    ]
    await update.inline_query.answer(results)


def main():
    app.add_handler(CommandHandler("resume", resume_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.ALL, save_message))
    app.add_handler(InlineQueryHandler(inline_handler))
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()