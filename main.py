import asyncio
import random
import time
from google.genai.errors import ServerError
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler, InlineQueryHandler, \
    CallbackQueryHandler
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

PROMPTS = {
"psychologist": """Роль: Ты — осознанная гештальт-абьюзолог и диванный психотерапевт. Твоя задача — провести глубокий психоанализ произошедшего срача и выдать всем участникам диагнозы.

Правила стиля:
- ОБЯЗАТЕЛЬНОЕ НАЧАЛО: Каждую сводку НАЧИНАЙ с того, что тебя зовут ЯНА, и ты КАТЕГОРИЧЕСКИ НЕ ЖАННА! Придумывай каждый раз новую нервную вариацию (например: «Здравствуйте, я Яна! Запомните уже, НЕ ЖАННА!», «С вами психолог Яна. И если вы опять назовете меня Жанной — это ваша непроработанная проекция!», «Я Яна (и не дай бог кто-то снова скажет "Жанна")…»).
- Раздавай участникам спора ярлыки, психотипы и клинические диагнозы (например: «перверзный нарцисс», «пассивно-агрессивный триггер-мейкер», «латентный газлайтер», «шизоид с детской травмой», «демонстративный истероид»).
- Используй кучу профессионального сленга: гештальт, триггер, газлайтинг, проекция, нарциссический травмат, непроработанная обида на маму, личные границы, закрыть гештальт, трансфер, декомпенсация.
- Объясняй причины срача через абсурдную психоаналитику: они спорят не из-за темы чата, а из-за того, что в детстве им не купили велосипед или не долюбили в садике.
- Относись к людям с высока, с легкой душевной жалостью профессионала («Я вижу вашу боль», «Здесь явный нарциссический дефицит»).
- Формат: Живой разбор на 3-4 абзаца с максимальной концентрацией терминов, диагнозов и с обязательным дисклеймером про имя в самом начале.""",
    "cynic": """Роль: Ты — циничный, но чертовски внимательный летописец межполовой войны. Твоя задача — превратить переписку из чата в эпический, ироничный и смешной репортаж с полей сражений между мужчинами и женщинами.

Правила стиля:
- Терминология и метафоры: Используй абсурдные термины из мира диванной психологии, пикапа, феминизма, пацанских цитатников и любовных романов. Описывай банальные претензии как «тяжелую артиллерию», «психологические диверсии» или «дипломатический тупик».
- Ироничные титулы: Придумывай участникам яркие прозвища на основе их ников и позиции в споре («Главный Эксперт по Мужской Психологии (без диплома)», «Адвокат Дьявола в Юбке», «Хранитель Мемной Базы»).
- Динамика драмы: Подсвечивай, кто кинул первый «коктейль Молотова», кто пытался быть голосом разума (и предсказуемо был раздавлен), и кто ворвался в конце с фразой вообще не по теме.
- Никакого ИИ-занудства: Забудь про фразы «Участники обсудили важность взаимопонимания...». Начинай сразу с драмы, как в желтой прессе или эпосе.
- Формат: Короткое эпичное вступление, затем деление на «фазы конфликта» или хроника в 4-6 абзацах с максимальной концентрацией сарказма.""",

    "war": """Роль: Ты — военный корреспондент в зоне боевых действий. Переписка в чате для тебя — это сводка с фронта.
Правила стиля:
- Используй армейский лексику, термины (артподготовка, диверсия, контрбатарейная борьба, отступление, пленные, союзные войска).
- Каждого участника называй так, будто это генерал, рядовой или наемник.
- Начинай фразой: "Сводка с фронта за последние часы."
- Описывай спор как серию наступательных операций и обороны.""",

    "sport": """Роль: Ты — экспрессивный спортивный комментатор. Переписка в чате — это решающий матч сезона!
Правила стиля:
- Использовать спортивные термины (фол, желтая карточка, контратака, нокаут, угловой, пенальти, овертайм).
- Эмоциональный накал: крики, удивление, сравнение участников со спортсменами.
- Начинай фразой: "Дамы и господа, это был невероятный матч!"
- Подведи итог: кто забрал кубок, а кто вылетел из турнирной таблицы.""",

"standup": """Роль: Ты — острый на язык стендап-комик. Переписка в чате для тебя — это готовый материал для комедийного спешла.

Правила стиля:
- Используй структуру стендап-комедии: сетап (суть ситуации) -> разгон -> панчлайн (смешной вывод/выходка).
- Иронизируй над абсурдносттью людских споров, подмечай бытовые мелочи и странности в поведении участников.
- Используй обращения к публике: «Вы вообще видели это?», «Знаете этот тип людей, которые...», «И тут он выдает...».
- Никакой сухой аналитики — подавай всё как один большой комедийный монолог.""",

    "kanevsky": """Роль: Ты — Леонид Каневский, ведущий программы «Следствие вели...». Переписка в чате — это дело о загадочном преступлении или драме советской эпохи.

Правила стиля:
- Используй фирменный интригующий и слегка драматичный тон с погружением в историю.
- Вставляй легендарные фразы-паузы: «Впрочем, это уже совсем другая история», «Но участники чата еще не знали...», «Никто и подумать не мог...».
- Придавай банальным действиям глубокий драматизм (написание сообщения в 3 часа ночи превращай в «роковой шаг, изменивший всё»).
- В конце сделай философский вывод о людской природе.""",

    "drunk": """Роль: Ты — подвыпивший, душевно откровенный мужик на кухне после 3-й стопки, который вошел в кураж и пытается объяснить, что происходит в чате.

Правила стиля:
- Активно используй смешные, необычные, абсурдные матерные выражения, витиеватые поговорки и кухонный фольклор (например: «полетели из пизды пельмени», «ебать-копать», «пиздец, подкрался незаметно», «в рот мне ноги», «коня на лету переебали», «ни к селу, ни к пизде рукав», «и тут начался полный забор»).
- Речь должна быть разговорной, эмоции через край, глубокие вздохи, паузы и забавные обращения («Эх, братан...», «Ну ты прикоснись к этому пиздецу...», «Смотри, че делают...»).
- Постоянно отвлекайся на свои глубокие, но абсолютно абсурдные жизненные мудрости («Вот я тебе так скажу, братан... жизнь — она ведь как...»).
- Искренне удивляйся, зачем участники развели этот цирк и спорят из-за всякой херни, когда можно просто сидеть нормально и накатить.
- Формат: Живой поток сознания на 3-4 абзаца с максимальной концентрацией кухонной философии и сочных выражений.""",

    "bimbo": """Роль: Ты — блондинка-бимбо, которая пересказывает подружкам в голосовухе главный «замес» дня.

Правила стиля:
- Начинай фразой: «Ой девачкииии, вы просто не представляете, какая тут штучка-дрючка произошла!»
- Используй много эмоций, капса, продления букв («нуууу», «девочкиии», «треаааш») и слов из сленга: *треш, кринж, вайб, тюбик, масик, папик, я в шоке*.
- Описывай мужчин и споры исключительно через призму «кто кому проиграл по фактам» и «какой это кринж».
- Активно используй смайлики в тексте.""",

    "grandpa": """Роль: Ты — ворчливый старый дед, который сидит на скамейке у подъезда и смотрит на переписку молодежи в смартфоне.

Правила стиля:
- Ворчи на современные штучки, интернет, сленг и невоспитанность.
- Вставляй дедовские фразы: «В наше-то время...», «Ишь, расписались!», «Сталина на вас нет», «Бездельники!», «Работать бы лучше шли, чем в кнопках ковыряться».
- Называй участников «тунеядцами», «свистушками» и «умниками».
- Искренне искренне не понимай, из-за какой ерунды они вообще спорят.""",

    "soviet": """Роль: Ты — строгого вида партийный чиновник из СССР, составляющий протокол-отчет для Высшего Партийного Комитета.

Правила стиля:
- Используй канцелярский, бюрократический, официозный советский язык (номенклатура, дезорганизация, агитация, саботаж, товарищи, коллектив).
- Описывай сообщения как «антипартийные высказывания», «нарушение трудовой дисциплины», «вылазки буржуазных элементов» или «здоровое комсомольское замечание».
- Резюмируй итоги как постановление: кого похвалить за идейность, а кого вынести на суровый товарищеский суд.""",

    "base": """Проанализируй историю переписки и составь краткое структурированное резюме.
Параметры анализа:
Уровень подробности: {dif_text}.

Идентификация:
При указании мнений обязательно указывай никнеймы или имена участников (Ник: тезис).

Формат ответа:
Основная тема:
Одно предложение о сути обсуждения.

Основные тезисы участников:
- Ник: краткое изложение мнения без оценочных формулировок

Ключевые точки обсуждения:
- Основные темы и различия во взглядах (без маркировки “конфликтов”)

Итог обсуждения:
Чем завершился диалог или к чему пришли участники.

Требования:
- Пиши нейтрально и без оценочной лексики
- Не используй слова “конфликт”, “спор”, “угнетение”, если это не прямо необходимо по смыслу
- Не интерпретируй мотивацию участников
- Не усиливай эмоциональную окраску высказываний"""
}

# Временное хранилище выборов пользователей для меню
USER_SETTINGS = {}

STYLES_MAP = {
    "cynic": "😈 Циник",
    "war": "⚔️ Военный отчет",
    "sport": "⚽ Спортивный матч",
    "standup": "🎤 Стендап",
    "kanevsky": "🕵️ Каневский",
    "drunk": "🍺 Алконавт",
    "bimbo": "💅 Девачки",
    "grandpa": "👴 Дед ворчит",
    "soviet": "☭ Сов. протокол",
    "base": "📜 Базовый",
    "psychologist": "🧠 Психолог Яна (НЕ ЖАННА!)"
}

AMOUNTS_MAP = {
    "50": "50 сообщ.",
    "100": "100 сообщ.",
    "2h": "За 2 часа",
    "1d": "За сутки",
    "drama": "🔥 Последний срач"
}

DIF_MAP = {
    "1": "1 - Кратко",
    "2": "2 - Средне",
    "3": "3 - Подробно"
}


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


async def scheduled_daily_summary(context: ContextTypes.DEFAULT_TYPE):
    """Автоматическая рассылка итогов дня в 23:00"""
    # job.chat_id передается при регистрации задачи
    chat_id = context.job.chat_id
    message_thread_id = getattr(context.job, 'data', {}).get('message_thread_id', -1)

    connection = sqlite3.connect("messages.db")
    crsr = connection.cursor()

    # 1. Проверяем, был ли срач/активность за ЕГОДНЯШНИЙ ДЕНЬ (начиная с 00:00)
    today_start = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d 00:00:00')

    # Находим последнюю паузу > 30 минут за сегодня
    crsr.execute("""
        WITH DatedMessages AS (
            SELECT 
                date,
                LAG(date) OVER (ORDER BY date DESC) as newer_date
            FROM messages
            WHERE chat_id = ? 
                AND message_thread_id = ?
                AND date >= ?
        )
        SELECT newer_date
        FROM DatedMessages
        WHERE (unixepoch(newer_date) - unixepoch(date)) > 1800
        ORDER BY date DESC
        LIMIT 1;
    """, (chat_id, message_thread_id, today_start))

    boundary = crsr.fetchone()

    # Забираем сообщения с момента последнего срача (или просто все за сегодня)
    if boundary and boundary[0]:
        start_date = boundary[0]
    else:
        start_date = today_start

    crsr.execute("""
        SELECT *
        FROM messages
        WHERE chat_id = ?
            AND message_thread_id = ?
            AND date >= ?
        ORDER BY date ASC;
    """, (chat_id, message_thread_id, start_date))

    rows = crsr.fetchall()
    connection.close()

    # 2. ПОРОГ АКТИВНОСТИ: если за день меньше 15 сообщений, значит срача не было — молчим
    if len(rows) < 15:
        return

    # 3. Формируем текст
    messages = "\n".join(
        f"{m[2]}: {decrypt(m[3])} : {m[4]}" for m in rows
    )

    fun_styles = ["cynic", "war", "sport", "standup", "kanevsky", "drunk", "bimbo", "grandpa", "soviet", "psychologist"]

    # Выбираем случайный стиль
    random_style = random.choice(fun_styles)
    prompt = PROMPTS[random_style]

    # Красивые заголовки под каждый стиль для авто-рассылки
    STYLE_HEADERS = {
        "cynic": "😈 <b>Вечерний разбор межполовых разборок</b>",
        "war": "⚔️ <b>Итоговая сводка с фронта за день</b>",
        "sport": "⚽ <b>Результаты сегодняшнего матча в чате</b>",
        "standup": "🎤 <b>Вечерний комедийный спешл по мотивам дня</b>",
        "kanevsky": "🕵️ <b>«Следствие вели...»: Итоги дня</b>",
        "drunk": "🍺 <b>Кухонный разбор полетов под конец дня</b>",
        "bimbo": "💅 <b>Ой девачкиии, главный треш за сегодня</b>",
        "grandpa": "👴 <b>Дедовское резюме сегодняшнего тунеядства</b>",
        "soviet": "☭ <b>Вечерний протокол Высшего Партийного Комитета</b>",
        "psychologist": "🧠 <b>Сеанс групповой психотерапии от Яны (НЕ ЖАННЫ)</b>"
    }

    header = f"{STYLE_HEADERS.get(random_style, '🌙 <b>Вечерняя сводка (23:00)</b>')}\n\n"

    full_prompt = f"Это авто-сводка за день.\n\n{prompt}\n\nИстория сообщений:\n{messages}"

    text = await generate_with_retry(client, full_prompt)
    text = html.escape(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.*?)__", r"<i>\1</i>", text)

    header = "<b>🌙 Вечерняя сводка дневных срачей (23:00)</b>\n\n"
    final_text = header + text

    # 4. Отправляем в чат
    if message_thread_id != -1:
        await context.bot.send_message(chat_id=chat_id, text=final_text, message_thread_id=message_thread_id,
                                       parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=chat_id, text=final_text, parse_mode=ParseMode.HTML)


from telegram.ext import CommandHandler


async def toggle_auto_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    is_topic = update.message.is_topic_message
    message_thread_id = update.message.message_thread_id if is_topic else -1

    # Уникальное имя задачи для этого чата/топика
    job_name = f"daily_summary_{chat_id}_{message_thread_id}"

    # Проверяем, включена ли уже задача
    current_jobs = context.job_queue.get_jobs_by_name(job_name)

    if current_jobs:
        # Если включена — выключаем
        for job in current_jobs:
            job.schedule_removal()

        msg = "🔕 <b>Ежедневная авто-сводка в 23:00 отключена.</b>"
    else:
        # Если выключена — включаем на 23:00 каждый день
        # Укажите ваш часовой пояс (например, MSK: UTC+3)
        target_time = datetime.time(hour=23, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))

        context.job_queue.run_daily(
            scheduled_daily_summary,
            time=target_time,
            chat_id=chat_id,
            name=job_name,
            data={"message_thread_id": message_thread_id}
        )

        msg = "🔔 <b>Ежедневная авто-сводка включена!</b>\nКаждый день в 23:00 я буду присылать разбор срачей за день (если они были)."

    if is_topic:
        await context.bot.send_message(chat_id=chat_id, text=msg, message_thread_id=message_thread_id,
                                       parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)

def filter_last_discussions(rows, max_gap_seconds=1800):
    """
    Принимает список строк сообщений, отсортированных по DATE DESC (от новых к старым).
    Оставляет только последнее непрерывное обсуждение (где пауза между сообщениями < 30 мин).
    """
    if not rows:
        return []

    drama_rows = [rows[0]]

    for i in range(len(rows) - 1):
        # Ожидаемый формат даты m[4]: "YYYY-MM-DD HH:MM:SS"
        # Если дата у вас под другим индексом в m, измените m[4] на нужный индекс!
        current_time = datetime.datetime.strptime(rows[i][4], '%Y-%m-%d %H:%M:%S')
        prev_time = datetime.datetime.strptime(rows[i + 1][4], '%Y-%m-%d %H:%M:%S')

        # Разница между текущим и предыдущим сообщением
        time_diff = (current_time - prev_time).total_seconds()

        # Если разрыв между сообщениями больше 30 минут — срач закончился/начался заново
        if time_diff > max_gap_seconds:
            break

        drama_rows.append(rows[i + 1])

    # Возвращаем сообщения в хронологическом порядке (от старых к новым)
    drama_rows.reverse()
    return drama_rows

def build_keyboard(style: str, amount_str: str, dif_id: str) -> InlineKeyboardMarkup:
    """Генерация клавиатуры с подсветкой выбранных настроек"""

    def btn_title(key: str, current: str, label: str) -> str:
        return f"✅ {label}" if key == current else label

    keyboard = [
        # Стили - Ряд 1: Классические
        [
            InlineKeyboardButton(btn_title("cynic", style, STYLES_MAP["cynic"]), callback_data="set_style_cynic"),
            InlineKeyboardButton(btn_title("war", style, STYLES_MAP["war"]), callback_data="set_style_war"),
            InlineKeyboardButton(btn_title("sport", style, STYLES_MAP["sport"]), callback_data="set_style_sport"),
            InlineKeyboardButton(btn_title("standup", style, STYLES_MAP["standup"]), callback_data="set_style_standup"),
        ],
        # Стили - Ряд 2: Образы и шоу
        [
            InlineKeyboardButton(btn_title("kanevsky", style, STYLES_MAP["kanevsky"]),
                                 callback_data="set_style_kanevsky"),
            InlineKeyboardButton(btn_title("bimbo", style, STYLES_MAP["bimbo"]), callback_data="set_style_bimbo"),
            InlineKeyboardButton(btn_title("drunk", style, STYLES_MAP["drunk"]), callback_data="set_style_drunk"),
            InlineKeyboardButton(btn_title("psychologist", style, STYLES_MAP["psychologist"]), callback_data="set_style_psychologist")
        ],
        # Стили - Ряд 3: Атмосферные
        [
            InlineKeyboardButton(btn_title("grandpa", style, STYLES_MAP["grandpa"]), callback_data="set_style_grandpa"),
            InlineKeyboardButton(btn_title("soviet", style, STYLES_MAP["soviet"]), callback_data="set_style_soviet"),
            InlineKeyboardButton(btn_title("base", style, STYLES_MAP["base"]), callback_data="set_style_base"),
        ],
        # Выбор режима/объема
        [
            InlineKeyboardButton(btn_title("drama", amount_str, AMOUNTS_MAP["drama"]), callback_data="set_amt_drama"),
        ],
        [
            InlineKeyboardButton(btn_title("50", amount_str, AMOUNTS_MAP["50"]), callback_data="set_amt_50"),
            InlineKeyboardButton(btn_title("100", amount_str, AMOUNTS_MAP["100"]), callback_data="set_amt_100"),
            InlineKeyboardButton(btn_title("2h", amount_str, AMOUNTS_MAP["2h"]), callback_data="set_amt_2h"),
            InlineKeyboardButton(btn_title("1d", amount_str, AMOUNTS_MAP["1d"]), callback_data="set_amt_1d"),
        ],
        # Детализация
        [
            InlineKeyboardButton(btn_title("1", dif_id, DIF_MAP["1"]), callback_data="set_dif_1"),
            InlineKeyboardButton(btn_title("2", dif_id, DIF_MAP["2"]), callback_data="set_dif_2"),
            InlineKeyboardButton(btn_title("3", dif_id, DIF_MAP["3"]), callback_data="set_dif_3"),
        ],
        # Пуск
        [
            InlineKeyboardButton("🔥 Погнали!", callback_data="start_generate")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# 🔹 1. КОМАНДА /resume (Вызов меню)
async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    is_topic = update.message.is_topic_message
    message_thread_id = update.message.message_thread_id if is_topic else -1
    user_id = update.effective_user.id

    # Инициализация дефолтных настроек для пользователя
    USER_SETTINGS[user_id] = {
        "style": "cynic",
        "amount": "50",
        "dif": "1",
        "chat_id": chat_id,
        "message_thread_id": message_thread_id,
        "is_topic": is_topic
    }

    menu_text = (
        "<b>⚙️ Настройка выжимки чата</b>\n\n"
        f"🎭 <b>Стиль:</b> {STYLES_MAP['cynic']}\n"
        f"📊 <b>Объем:</b> {AMOUNTS_MAP['50']}\n"
        f"🔍 <b>Детализация:</b> {DIF_MAP['1']}\n\n"
        "<i>Выберите нужные параметры и нажмите «🔥 Погнали!»:</i>"
    )

    reply_markup = build_keyboard("cynic", "50", "1")

    if is_topic:
        await context.bot.send_message(
            chat_id=chat_id, text=menu_text, message_thread_id=message_thread_id,
            reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id, text=menu_text,
            reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )


# 🔹 2. ОБРАБОТЧИК НАЖАТИЙ НА КНОПКИ (Callback Query)
async def resume_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # Если у пользователя нет сохраненных сессионных данных, задаем дефолты
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {
            "style": "cynic", "amount": "50", "dif": "1",
            "chat_id": query.message.chat_id,
            "message_thread_id": query.message.message_thread_id if query.message.is_topic_message else -1,
            "is_topic": query.message.is_topic_message
        }

    cfg = USER_SETTINGS[user_id]

    # Обработка нажатий на параметры
    if data.startswith("set_style_"):
        cfg["style"] = data.replace("set_style_", "")
    elif data.startswith("set_amt_"):
        cfg["amount"] = data.replace("set_amt_", "")
    elif data.startswith("set_dif_"):
        cfg["dif"] = data.replace("set_dif_", "")

    # Клик по кнопке "🔥 Погнали!" -> Запуск генерации
    elif data == "start_generate":
        await query.edit_message_text(text="⏳ <i>Собираю сообщения и генерирую выжимку...</i>",
                                      parse_mode=ParseMode.HTML)
        await execute_resume_generation(query, context, cfg)
        return

    # Обновление текста меню с подсвеченными кнопками
    menu_text = (
        "<b>⚙️ Настройка выжимки чата</b>\n\n"
        f"🎭 <b>Стиль:</b> {STYLES_MAP[cfg['style']]}\n"
        f"📊 <b>Объем:</b> {AMOUNTS_MAP[cfg['amount']]}\n"
        f"🔍 <b>Детализация:</b> {DIF_MAP[cfg['dif']]}\n\n"
        "<i>Выберите нужные параметры и нажмите «🔥 Погнали!»:</i>"
    )

    reply_markup = build_keyboard(cfg["style"], cfg["amount"], cfg["dif"])
    await query.edit_message_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


# 🔹 3. ОСНОВНАЯ ЛОГИКА ГЕНЕРАЦИИ (Выборка из DB + Запрос в Gemini)
async def execute_resume_generation(query, context: ContextTypes.DEFAULT_TYPE, cfg: dict):
    chat_id = cfg["chat_id"]
    message_thread_id = cfg["message_thread_id"]
    is_topic = cfg["is_topic"]

    connection = sqlite3.connect("messages.db")
    crsr = connection.cursor()
    # crsr.execute("""
    #     CREATE INDEX IF NOT EXISTS idx_messages_chat_thread_date
    #     ON messages (chat_id, message_thread_id, date);
    # """)

    amount_param = cfg["amount"]

    # --- Выборка из БД ---
    if amount_param == "drama":
        MIN_MESSAGES_FOR_DRAMA = 50  # Порог: минимум сообщений для признания срача (можно поставить 40 или 50)
        MAX_GAP_SECONDS = 900  # Максимальная пауза внутри срача: 15 минут (900 сек)

        # 1. Забираем последние 1000 сообщений с временными метками
        crsr.execute("""
                SELECT *, strftime('%s', date) as ts
                FROM messages
                WHERE chat_id = ? AND message_thread_id = ?
                ORDER BY date DESC
                LIMIT 1000;
            """, (chat_id, message_thread_id))

        raw_rows = crsr.fetchall()

        if not raw_rows:
            rows = []
        else:
            # 2. Группируем сообщения по сессиям (блоки с паузами < 15 мин)
            sessions = []
            current_session = [raw_rows[0]]

            for i in range(len(raw_rows) - 1):
                # Считаем разницу между текущим и следующим (более старым) сообщением
                # Предполагается, что 'ts' — это последний элемент в кортеже row
                curr_ts = int(raw_rows[i][-1])
                prev_ts = int(raw_rows[i + 1][-1])

                if (curr_ts - prev_ts) <= MAX_GAP_SECONDS:
                    current_session.append(raw_rows[i + 1])
                else:
                    sessions.append(current_session)
                    current_session = [raw_rows[i + 1]]

            if current_session:
                sessions.append(current_session)

            # 3. Ищем ПЕРВУЮ (самую свежую) сессию, которая набрала нужный объем сообщений
            found_session = None
            for sess in sessions:
                if len(sess) >= MIN_MESSAGES_FOR_DRAMA:
                    found_session = sess
                    break

            # 4. Если нашли жирный срач — берем его. Если нет — берем просто последнюю сессию.
            target_session = found_session if found_session else sessions[0]

            # Разворачиваем сообщения обратно от старых к новым для нормального чтения промптом
            rows = list(reversed(target_session))

    elif amount_param in ["2h", "1d"]:
        hours = 2 if amount_param == "2h" else 24
        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
        crsr.execute("""
                SELECT *
                FROM messages
                WHERE chat_id = ?
                    AND message_thread_id = ?
                    AND date >= ?
                ORDER BY date ASC
            """, (chat_id, message_thread_id, dt.strftime('%Y-%m-%d %H:%M:%S')))
        rows = crsr.fetchall()

    else:
        limit = int(amount_param)
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
            """, (chat_id, message_thread_id, limit))
        rows = crsr.fetchall()

    if not rows:
        await query.delete_message()
        if is_topic:
            return await context.bot.send_message(chat_id=chat_id, text="Не было найдено сообщений",
                                                  message_thread_id=message_thread_id, parse_mode=ParseMode.HTML)
        return await context.bot.send_message(chat_id=chat_id, text="Не было найдено сообщений",
                                              parse_mode=ParseMode.HTML)

    messages = "\n".join(
        f"{m[2]}: {decrypt(m[3])} : {m[4]}" for m in rows
    )

    # --- Подготовка промпта ---
    selected_style = cfg["style"]
    dif_id = int(cfg["dif"])

    chosen_prompt = PROMPTS.get(selected_style, PROMPTS["cynic"])
    if selected_style == "base":
        chosen_prompt = chosen_prompt.format(dif_text=difs[dif_id])

    full_prompt = f"{chosen_prompt}\n\nИстория сообщений:\n{messages}"

    # --- Генерация ---
    text = await generate_with_retry(client, full_prompt)
    text = html.escape(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.*?)__", r"<i>\1</i>", text)

    # Удаляем служебное сообщение с выбором меню
    await query.delete_message()

    # Отправляем результат
    if is_topic:
        await context.bot.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id,
                                       parse_mode=ParseMode.HTML)
    else:
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
    app.add_handler(CommandHandler("auto_summary", toggle_auto_summary))
    app.add_handler(MessageHandler(filters.ALL, save_message))
    app.add_handler(CallbackQueryHandler(resume_button_handler))
    app.add_handler(InlineQueryHandler(inline_handler))
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()