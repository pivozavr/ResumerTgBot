import asyncio
import random

import ollama
from ollama import chat, ChatResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler, MessageReactionHandler
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

difs = {1: "Кратко (то суть)", 2: "Средне (с аргументами)", 3: "Подробно (с разбором каждой темы)"}
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

USER_SETTINGS = {}

STYLES_CONFIG = {
    "base": {
        "name": "📜 Базовый",
        "desc": "Четкий и структурированный пересказ фактов без воды.",
        "tier": "free"
    },
    "cynic": {
        "name": "😈 Циник",
        "desc": "Едкий, ехидный и беспощадный разбор вашего общения.",
        "tier": "free"
    },
    "war": {
        "name": "⚔️ Военный отчет",
        "desc": "Сводка с фронтов чата в стиле оперативного штаба.",
        "tier": "free"
    },
    "sport": {
        "name": "⚽ Спортивный матч",
        "desc": "Энергичный репортаж с комментариями матча вашей активности.",
        "tier": "free"
    },
    "standup": {
        "name": "🎤 Стендап",
        "desc": "Выступление комика с прожаркой самых ярких сообщений.",
        "tier": "free"
    },
    "kanevsky": {
        "name": "🕵️ Каневский",
        "desc": "Легендарный детективный тон: «Но это уже совсем другая история...»",
        "tier": "free"
    },
    "drunk": {
        "name": "🍺 Алконавт",
        "desc": "Пересказ так, будто историю рассказывают за соседним столом.",
        "tier": "free"
    },
    "bimbo": {
        "name": "💅 Девачки",
        "desc": "Максимально гламурный и поверхностный взгляд на происходящее.",
        "tier": "free"
    },
    "grandpa": {
        "name": "👴 Дед ворчит",
        "desc": "Бормотание про то, «как раньше было лучше», с кучей баек.",
        "tier": "free"
    },
    "soviet": {
        "name": "☭ Сов. протокол",
        "desc": "Строгая партийная сводка достижений пятилетки флуда.",
        "tier": "free"
    },
    "psychologist": {
        "name": "🧠 Психолог Яна (НЕ ЖАННА!)",
        "desc": "Глубокий разбор скрытых травм, мотивов и токсичности чата.",
        "tier": "free"
    }
}

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

HELP_TEXTS = {
    "help_main": (
        "<b>📖 Справочник «Бот-Летописец»</b>\n\n"
        "Я умею анализировать историю вашего чата и собирать крутые выжимки, чтобы вы не читали тысячи пропущенных сообщений.\n\n"
        "<b>Основные команды:</b>\n"
        "• <code>/resume</code> — вызвать меню выбора сводки прямо в чате.\n"
        "• <code>/help</code> — открыть это интерактивное меню.\n"
        "• <code>/auto_summary</code> — включить/выключить авто-сводки (если доступно).\n\n"
        "💡 <i>Просто вызовите команду /resume в группе или топике, выберите стиль, глубину анализа — и наслаждайтесь результатом!</i>"
    ),
    "help_styles": (
        "<b>🎭 Стили общения и рассказчики</b>\n\n"
        "Вы можете выбрать, в каком стиле будет написана выжимка:\n"
        "• 🏙 <b>Базовый / Сухой</b> — классический структурированный пересказ фактов.\n"
        "• 😈 <b>Циник</b> — едкий, ироничный разбор того, чем вы тут занимались.\n"
        "• 🥃 <i>(И другие уникальные персонажи)</i> — от психолога до неформальных рассказчиков.\n\n"
        "✨ Позже здесь появится разделение на бесплатные стили и PRO-персонажи."
    ),
    "help_privacy": (
        "<b>🔒 Безопасность и Анонимность</b>\n\n"
        "• Бот собирает сообщения только для формирования текущих сводок.\n"
        "• Настроено автоматическое удаление старых данных по TTL (через 7 дней).\n"
        "• В разработке находится <b>Анонимный режим через ЛС (Шаг 3)</b>, чтобы делать запросы тихо, без спама в общий чат."
    )
}


def get_help_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 О боте и командах", callback_data="help_main")],
        [InlineKeyboardButton("🎭 Стили и персонажи", callback_data="help_styles")],
        [InlineKeyboardButton("🔒 Приватность и ЛС", callback_data="help_privacy")],
        [InlineKeyboardButton("❌ Закрыть", callback_data="help_close")]
    ])


def get_style_selection_keyboard(current_style="base"):
    keyboard = []
    for key, data in STYLES_CONFIG.items():
        is_selected = (key == current_style)
        prefix = "✅ " if is_selected else ""
        tier_icon = "✨" if data["tier"] == "free" else "🔒"
        button_text = f"{prefix}{data['name']} {tier_icon}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"set_style_{key}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад к настройкам", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(keyboard)


def encrypt(text: str) -> str:
    return cipher.encrypt(text.encode()).decode()


def decrypt(text: str) -> str:
    try:
        return cipher.decrypt(text.strip().encode()).decode()
    except:
        return text


async def generate_with_retry(client, prompt, retries=3):
    for attempt in range(retries):
        try:
            response = ollama.generate(model='qwen2.5', prompt=prompt)
            return response.response
        except Exception as e:
            error_text = str(e)
            print(f"[Gemini Error] Попытка {attempt + 1} не удалась: {error_text}")

            if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text:
                return "ОПА! Превышен лимит токенов/квоты API. Запрос временно недоступен."
            if "503" in error_text or "UNAVAILABLE" in error_text:
                return "ОПА! Модель Google сейчас перегружена (ошибка 503). Попробуйте нажать «Погнали!» еще раз через пару секунд."

            if attempt == retries - 1:
                return f"ОПА! Ошибка после всех попыток: {error_text}"

            await asyncio.sleep(2 ** attempt)

    return "ОПА! Не удалось получить ответ от ИИ."


async def scheduled_daily_summary(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    message_thread_id = getattr(context.job, 'data', {}).get('message_thread_id', -1)

    connection = sqlite3.connect("messages.db")
    crsr = connection.cursor()

    today_start = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d 00:00:00')

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

    if len(rows) < 15:
        return

    messages = "\n".join(
        f"{m[2]}: {decrypt(m[3])} : {m[4]}" for m in rows
    )

    fun_styles = ["cynic", "war", "sport", "standup", "kanevsky", "drunk", "bimbo", "grandpa", "soviet", "psychologist"]
    random_style = random.choice(fun_styles)
    prompt = PROMPTS[random_style]

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
    final_text = header + text

    if message_thread_id != -1:
        await context.bot.send_message(chat_id=chat_id, text=final_text, message_thread_id=message_thread_id,
                                       parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=chat_id, text=final_text, parse_mode=ParseMode.HTML)


async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("чето было")
    reaction_update = update.message_reaction
    if not reaction_update:
        return

    chat_id = reaction_update.chat.id
    user_id = reaction_update.user.id if reaction_update.user else None

    # Если реакцию поставил реальный пользователь (а не канал)
    if user_id:
        # Получаем имя пользователя, если оно доступно в обновлении,
        # или берем из контекста/базы, либо ставим дефолтное
        user = reaction_update.user
        username = user.first_name if user else "Аноним"
        chat_title = reaction_update.chat.title if hasattr(reaction_update.chat, 'title') else "Группа"

        # Проверяем, добавили ли новую реакцию (а не убрали её)
        # new_reaction содержит список актуальных реакций пользователя
        if reaction_update.new_reaction:
            connection = sqlite3.connect("messages.db")
            crsr = connection.cursor()

            # Записываем в базу данных участников
            crsr.execute("""
                INSERT OR IGNORE INTO chat_members (chat_id, user_id, username, chat_title)
                VALUES (?, ?, ?, ?)
            """, (chat_id, user_id, username, chat_title))

            connection.commit()
            connection.close()

async def send_split_message(context, chat_id: int, message_thread_id: int, text: str, reply_markup=None):
    MAX_LENGTH = 4000
    thread_id = message_thread_id if message_thread_id and message_thread_id != -1 else None

    if len(text) <= MAX_LENGTH:
        kwargs = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": ParseMode.HTML,
            "reply_markup": reply_markup
        }
        if thread_id is not None:
            kwargs["message_thread_id"] = thread_id
        await context.bot.send_message(**kwargs)
        return

    lines = text.split("\n")
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > MAX_LENGTH:
            chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk)

    for i, chunk in enumerate(chunks):
        is_last = (i == len(chunks) - 1)
        kwargs = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": ParseMode.HTML,
            "reply_markup": reply_markup if is_last else None
        }
        if thread_id is not None:
            kwargs["message_thread_id"] = thread_id
        await context.bot.send_message(**kwargs)


async def toggle_auto_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    is_topic = update.message.is_topic_message
    message_thread_id = update.message.message_thread_id if is_topic else -1
    job_name = f"daily_summary_{chat_id}_{message_thread_id}"
    current_jobs = context.job_queue.get_jobs_by_name(job_name)

    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
        msg = "🔕 <b>Ежедневная авто-сводка в 23:00 отключена.</b>"
    else:
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


def build_main_menu_keyboard(style: str, amount_str: str, dif_id: str, private: bool) -> InlineKeyboardMarkup:
    def btn_title(key: str, current: str, label: str) -> str:
        return f"✅ {label}" if key == current else label

    current_style_data = STYLES_CONFIG.get(style, STYLES_CONFIG["base"])
    style_display_name = f"{current_style_data['name']} {'✨' if current_style_data['tier'] == 'free' else '🔒'}"

    keyboard = [
        [
            InlineKeyboardButton(f"🎭 Стиль: {style_display_name}", callback_data="open_styles_menu")
        ],
        [
            InlineKeyboardButton(btn_title("drama", amount_str, AMOUNTS_MAP["drama"]), callback_data="set_amt_drama"),
        ],
        [
            InlineKeyboardButton(btn_title("50", amount_str, AMOUNTS_MAP["50"]), callback_data="set_amt_50"),
            InlineKeyboardButton(btn_title("100", amount_str, AMOUNTS_MAP["100"]), callback_data="set_amt_100"),
            InlineKeyboardButton(btn_title("2h", amount_str, AMOUNTS_MAP["2h"]), callback_data="set_amt_2h"),
            InlineKeyboardButton(btn_title("1d", amount_str, AMOUNTS_MAP["1d"]), callback_data="set_amt_1d"),
        ],
        [
            InlineKeyboardButton(btn_title("1", dif_id, DIF_MAP["1"]), callback_data="set_dif_1"),
            InlineKeyboardButton(btn_title("2", dif_id, DIF_MAP["2"]), callback_data="set_dif_2"),
            InlineKeyboardButton(btn_title("3", dif_id, DIF_MAP["3"]), callback_data="set_dif_3"),
        ],
        [
            InlineKeyboardButton("🔥 Погнали!", callback_data="start_generate")
        ]
    ]
    if(private):
        keyboard.append([InlineKeyboardButton("🔙 Сменить чат", callback_data="back_to_chats")])
    return InlineKeyboardMarkup(keyboard)


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    # 1. ЛИЧНЫЙ ЧАТ
    if chat.type == "private":
        connection = sqlite3.connect("messages.db")
        crsr = connection.cursor()
        crsr.execute("SELECT chat_id, chat_title FROM chat_members WHERE user_id = ?", (user_id,))
        chats = crsr.fetchall()
        connection.close()

        # Если пользователя нигде нет
        if not chats:
            await update.message.reply_text(
                "🔒 **Анонимный режим Сводчика**\n\n"
                "Я пока не вижу вас ни в одном общем чате.\n\n"
                "💡 **Как получить доступ:**\n"
                "Напишите сообщение в группе, где я добавлен, или поставьте реакцию на моё приветственное сообщение!",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Если чат всего один
        if len(chats) == 1:
            chat_id, chat_title = chats[0]

            if user_id not in USER_SETTINGS:
                USER_SETTINGS[user_id] = {"style": "base", "amount": "50", "dif": "1"}

            USER_SETTINGS[user_id]["chat_id"] = chat_id
            USER_SETTINGS[user_id]["chat_title"] = chat_title or f"Чат {chat_id}"
            USER_SETTINGS[user_id]["message_thread_id"] = -1
            USER_SETTINGS[user_id]["is_topic"] = False

            style = USER_SETTINGS[user_id]["style"]
            current_style_data = STYLES_CONFIG.get(style, STYLES_CONFIG["base"])

            menu_text = (
                f"<b>🎙 Панель управления Сводчика</b>\n"
                f"💬 Текущий чат: <b>{chat_title or chat_id}</b>\n\n"
                f"Текущий рассказчик: <b>{current_style_data['name']} ✨</b>\n"
                f"<i>{current_style_data['desc']}</i>\n\n"
                "Выберите глубину анализа или смените персонажа:"
            )

            # Создаем клавиатуру с нуля
            reply_markup = build_main_menu_keyboard(style, "50", "1", chat.type == "private")
            await update.message.reply_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            return

        # Если чатов несколько — шлем список с кнопками выбора
        else:
            keyboard = [[InlineKeyboardButton(f"💬 {title or f'Чат {cid}'}", callback_data=f"select_chat_{cid}")] for
                        cid, title in chats]
            await update.message.reply_text(
                "📁 <b>Выберите чат, для которого хотите получить сводку:</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            return

    # 2. ГРУППОВОЙ ЧАТ
    else:
        is_topic = update.message.is_topic_message if update.message else False
        message_thread_id = update.message.message_thread_id if is_topic else -1

        USER_SETTINGS[user_id] = {
            "style": "base",
            "amount": "50",
            "dif": "1",
            "chat_id": chat.id,
            "message_thread_id": message_thread_id,
            "is_topic": is_topic
        }

        current_style_data = STYLES_CONFIG["base"]
        menu_text = (
            "<b>🎙 Панель управления Летописца</b>\n\n"
            f"Текущий рассказчик: <b>{current_style_data['name']} ✨</b>\n"
            f"<i>{current_style_data['desc']}</i>\n\n"
            "Выберите глубину анализа или смените персонажа в меню ниже:"
        )


        reply_markup = build_main_menu_keyboard("base", "50", "1",chat.type == "private")
        await send_split_message(context, chat.id, message_thread_id, menu_text, reply_markup)


async def unified_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Сразу убираем часики на кнопке

    data = query.data
    private = query.message.chat.type == "private"
    if query.data.startswith("select_chat_"):
        chat_id = int(query.data.split("_")[2])
        user_id = query.from_user.id

        # Достаем название выбранного чата из базы
        connection = sqlite3.connect("messages.db")
        crsr = connection.cursor()
        crsr.execute("SELECT chat_title FROM chat_members WHERE chat_id = ? AND user_id = ? LIMIT 1",
                     (chat_id, user_id))
        row = crsr.fetchone()
        connection.close()

        chat_title = row[0] if row and row[0] else f"Чат {chat_id}"

        # Инициализируем или обновляем настройки пользователя
        if user_id not in USER_SETTINGS:
            USER_SETTINGS[user_id] = {"style": "base", "amount": "50", "dif": "1"}

        USER_SETTINGS[user_id]["chat_id"] = chat_id
        USER_SETTINGS[user_id]["chat_title"] = chat_title
        USER_SETTINGS[user_id]["message_thread_id"] = -1
        USER_SETTINGS[user_id]["is_topic"] = False

        style = USER_SETTINGS[user_id]["style"]
        current_style_data = STYLES_CONFIG.get(style, STYLES_CONFIG["base"])

        menu_text = (
            f"<b>🎙 Панель управления Сводчика</b>\n"
            f"💬 Текущий чат: <b>{chat_title}</b>\n\n"
            f"Текущий рассказчик: <b>{current_style_data['name']} ✨</b>\n"
            f"<i>{current_style_data['desc']}</i>\n\n"
            "Выберите глубину анализа или смените персонажа:"
        )

        reply_markup = build_main_menu_keyboard(style, "50", "1",private)

        await query.answer()
        await query.message.edit_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return

    # Если это нажатие связано с помощью /help
    if data.startswith("help_"):
        if data == "help_close":
            await query.message.delete()
            return
        text = HELP_TEXTS.get(data, HELP_TEXTS["help_main"])
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_help_keyboard()
        )
        return

    # Иначе обрабатываем логику генерации и меню сводок
    user_id = query.from_user.id
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {
            "style": "base", "amount": "50", "dif": "1",
            "chat_id": query.message.chat_id,
            "message_thread_id": query.message.message_thread_id if query.message.is_topic_message else -1,
            "is_topic": query.message.is_topic_message
        }

    cfg = USER_SETTINGS[user_id]

    if data == "open_styles_menu":
        await query.edit_message_text(
            text="<b>🎭 Выберите рассказчика:</b>\n\nСтили с иконкой 🔒 доступны только в PRO-версии чата.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_style_selection_keyboard(cfg["style"])
        )
        return

    if data == "back_to_main_menu":
        current_style_data = STYLES_CONFIG.get(cfg["style"], STYLES_CONFIG["base"])
        menu_text = (
            "<b>🎙 Панель управления Летописца</b>\n\n"
            f"Текущий рассказчик: <b>{current_style_data['name']}</b>\n"
            f"<i>{current_style_data['desc']}</i>\n\n"
            "Выберите глубину анализа или смените персонажа в меню ниже:"
        )
        if(private):
            menu_text = (
                f"<b>🎙 Панель управления Сводчика</b>\n"
                f"💬 Текущий чат: <b>{USER_SETTINGS[user_id]["chat_title"]}</b>\n\n"
                f"Текущий рассказчик: <b>{current_style_data['name']} ✨</b>\n"
                f"<i>{current_style_data['desc']}</i>\n\n"
                "Выберите глубину анализа или смените персонажа:"
            )
        reply_markup = build_main_menu_keyboard(cfg["style"], cfg["amount"], cfg["dif"],private)
        await query.edit_message_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return

    if data.startswith("set_style_"):
        new_style = data.replace("set_style_", "")
        if STYLES_CONFIG[new_style]["tier"] == "pro":
            await query.answer("🔒 Этот персонаж доступен только в PRO-версии чата!", show_alert=True)
            return
        cfg["style"] = new_style

        current_style_data = STYLES_CONFIG[new_style]
        menu_text = (
            "<b>🎙 Панель управления Летописца</b>\n\n"
            f"Текущий рассказчик: <b>{current_style_data['name']}</b>\n"
            f"<i>{current_style_data['desc']}</i>\n\n"
            "Выберите глубину анализа или смените персонажа в меню ниже:"
        )
        if (private):
            menu_text = (
                f"<b>🎙 Панель управления Сводчика</b>\n"
                f"💬 Текущий чат: <b>{USER_SETTINGS[user_id]["chat_title"]}</b>\n\n"
                f"Текущий рассказчик: <b>{current_style_data['name']} ✨</b>\n"
                f"<i>{current_style_data['desc']}</i>\n\n"
                "Выберите глубину анализа или смените персонажа:"
            )
        reply_markup = build_main_menu_keyboard(cfg["style"], cfg["amount"], cfg["dif"],private)
        await query.edit_message_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return


    # 2. НОВЫЙ ХЭНДЛЕР: Возврат к списку чатов («Назад»)
    if query.data == "back_to_chats":
        user_id = query.from_user.id

        connection = sqlite3.connect("messages.db")
        crsr = connection.cursor()
        crsr.execute("SELECT chat_id, chat_title FROM chat_members WHERE user_id = ?", (user_id,))
        chats = crsr.fetchall()
        connection.close()

        if not chats:
            await query.answer("У вас нет доступных чатов.", show_alert=True)
            return

        # Формируем список чатов заново
        keyboard = [[InlineKeyboardButton(f"💬 {title or f'Чат {cid}'}", callback_data=f"select_chat_{cid}")] for
                    cid, title in chats]

        await query.answer()
        await query.message.edit_text(
            "📁 <b>Выберите чат, для которого хотите получить сводку:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
        return

    if data.startswith("set_amt_"):
        cfg["amount"] = data.replace("set_amt_", "")
    elif data.startswith("set_dif_"):
        cfg["dif"] = data.replace("set_dif_", "")
    elif data == "start_generate":
        await query.edit_message_text(text="⏳ <i>Собираю сообщения и генерирую выжимку...</i>",
                                      parse_mode=ParseMode.HTML)
        await execute_resume_generation(query, context, cfg)
        return

    current_style_data = STYLES_CONFIG.get(cfg["style"], STYLES_CONFIG["base"])
    menu_text = (
        "<b>🎙 Панель управления Летописца</b>\n\n"
        f"Текущий рассказчик: <b>{current_style_data['name']}</b>\n"
        f"<i>{current_style_data['desc']}</i>\n\n"
        "Выберите глубину анализа или смените персонажа в меню ниже:"
    )
    if (private):
        menu_text = (
            f"<b>🎙 Панель управления Сводчика</b>\n"
            f"💬 Текущий чат: <b>{USER_SETTINGS[user_id]["chat_title"]}</b>\n\n"
            f"Текущий рассказчик: <b>{current_style_data['name']} ✨</b>\n"
            f"<i>{current_style_data['desc']}</i>\n\n"
            "Выберите глубину анализа или смените персонажа:"
        )

    reply_markup = build_main_menu_keyboard(cfg["style"], cfg["amount"], cfg["dif"],private)
    await query.edit_message_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def execute_resume_generation(query, context: ContextTypes.DEFAULT_TYPE, cfg: dict):
    chat_id = cfg["chat_id"]
    message_thread_id = cfg["message_thread_id"]
    is_topic = cfg["is_topic"]

    connection = sqlite3.connect("messages.db")
    crsr = connection.cursor()

    amount_param = cfg["amount"]

    if amount_param == "drama":
        MIN_MESSAGES_FOR_DRAMA = 50
        MAX_GAP_SECONDS = 900

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
            sessions = []
            current_session = [raw_rows[0]]

            for i in range(len(raw_rows) - 1):
                curr_ts = int(raw_rows[i][-1])
                prev_ts = int(raw_rows[i + 1][-1])

                if (curr_ts - prev_ts) <= MAX_GAP_SECONDS:
                    current_session.append(raw_rows[i + 1])
                else:
                    sessions.append(current_session)
                    current_session = [raw_rows[i + 1]]

            if current_session:
                sessions.append(current_session)

            found_session = None
            for sess in sessions:
                if len(sess) >= MIN_MESSAGES_FOR_DRAMA:
                    found_session = sess
                    break

            target_session = found_session if found_session else sessions[0]
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
        connection.close()
        await query.delete_message()
        if is_topic:
            return await context.bot.send_message(chat_id=chat_id, text="Не было найдено сообщений",
                                                  message_thread_id=message_thread_id, parse_mode=ParseMode.HTML)
        return await context.bot.send_message(chat_id=chat_id, text="Не было найдено сообщений",
                                              parse_mode=ParseMode.HTML)

    selected_style = cfg["style"]
    dif_id = int(cfg["dif"])
    last_msg_date = rows[-1][4]

    crsr.execute("""
        SELECT response_text, created_at 
        FROM summary_cache 
        WHERE chat_id = ? 
          AND message_thread_id = ? 
          AND style = ? 
          AND amount_param = ? 
          AND last_msg_date = ?
    """, (chat_id, message_thread_id, selected_style, f"{amount_param}_{dif_id}", last_msg_date))

    cached_result = crsr.fetchone()

    if cached_result:
        connection.close()
        cached_text = cached_result[0]

        if is_topic:
            return await query.message.edit_text(text=cached_text,
                                                  message_thread_id=message_thread_id, parse_mode=ParseMode.HTML)
        return await query.message.edit_text(text=cached_text, parse_mode=ParseMode.HTML)

    messages = "\n".join(
        f"{m[2]}: {decrypt(m[3])} : {m[4]}" for m in rows
    )

    chosen_prompt = PROMPTS.get(selected_style, PROMPTS["base"])
    if selected_style == "base":
        chosen_prompt = chosen_prompt.format(dif_text=difs[dif_id])

    full_prompt = f"{chosen_prompt}\n\nИстория сообщений:\n{messages}"

    text = await generate_with_retry(client, full_prompt)

    if not text or text.startswith("ОПА!"):
        connection.close()
        try:
            await query.edit_message_text(text=text, parse_mode=ParseMode.HTML)
        except:
            await query.message.reply_text(text=text, parse_mode=ParseMode.HTML)
        return

    text = html.escape(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.*?)__", r"<i>\1</i>", text)

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    crsr.execute("""
            INSERT OR REPLACE INTO summary_cache 
            (chat_id, message_thread_id, style, amount_param, last_msg_date, response_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chat_id, message_thread_id, selected_style, f"{amount_param}_{dif_id}", last_msg_date, text, now_str))

    connection.commit()
    connection.close()


    if is_topic:
        await query.message.edit_text(text=text, message_thread_id=message_thread_id,
                                       parse_mode=ParseMode.HTML)
    else:
        await query.message.edit_text(text=text, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            text=HELP_TEXTS["help_main"],
            parse_mode=ParseMode.HTML,
            reply_markup=get_help_keyboard()
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg_text = """
Привет! Я бот для анализа переписок.

Я могу:
    — сохранять сообщения из чата
    — делать краткие и подробные резюме диалогов
    — выделять ключевые темы и позиции участников

Добавь меня в группу и выдай права администратора, чтобы я мог видеть все сообщения и работать корректно.

Команды:
    /resume — получить резюме переписки
    /help — гайд по использованию команд"""

    if update.message.is_topic_message:
        await context.bot.send_message(chat_id=chat_id, message_thread_id=update.message.message_thread_id,
                                       text=msg_text)
    else:
        await context.bot.send_message(chat_id=chat_id, text=msg_text)


async def on_bot_added_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, добавили ли именно нашего бота
    bot_id = context.bot.id
    new_members = update.message.new_chat_members

    if any(member.id == bot_id for member in new_members):
        # Вызываем вашу функцию приветствия/реакции
        await send_welcome_reaction_message(update, context)

async def send_welcome_reaction_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.message.chat

    # Текст инструкции для анонимного режима
    text = (
        "🤖 <b>Привет! Я Сводчик.</b>\n\n"
        "Хотите использовать мои функции **анонимно** в личных сообщениях?\n"
        "👉 Просто поставьте **любую реакцию** (👍, 🔥 и т.д.) на это сообщение, и я запомню, что вы участник этого чата!"
    )

    sent_message = await context.bot.send_message(
        chat_id=chat.id,
        text=text,
        parse_mode=ParseMode.HTML
    )

    # Опционально: можно закрепить сообщение, чтобы участники его видели
    try:
        await context.bot.pin_chat_message(chat_id=chat.id, message_id=sent_message.message_id)
    except Exception:
        pass  # Если у бота нет прав на закрепление, просто пропустим

async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message and message.text:
        chat = message.chat
        # Сохраняем только из групп и супергрупп
        if chat.type in ["group", "supergroup"]:
            user = message.from_user
            user_id = user.id if user else 0
            username = user.first_name if user else "Anonymous"
            chat_title = chat.title

            message_thread_id = message.message_thread_id if message.is_topic_message else -1
            text = message.text  # Если у вас используется шифрование, оставьте encrypt(message.text)
            chat_id = chat.id
            date = message.date.strftime('%Y-%m-%d %H:%M:%S')

            connection = sqlite3.connect("messages.db")
            crsr = connection.cursor()

            # 1. Сохраняем сообщение с user_id
            crsr.execute("""
                INSERT INTO messages (chat_id, message_thread_id, user_id, username, text, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chat_id, message_thread_id, user_id, username, text, date))

            # 2. Фиксируем связку юзера и чата (с названием чата для ЛС)
            crsr.execute("""
                INSERT OR IGNORE INTO chat_members (chat_id, user_id, username, chat_title)
                VALUES (?, ?, ?, ?)
            """, (chat_id, user_id, username, chat_title))

            connection.commit()
            connection.close()


async def cleanup_old_messages(context: ContextTypes.DEFAULT_TYPE):
    try:
        cutoff_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).strftime(
            '%Y-%m-%d %H:%M:%S')
        connection = sqlite3.connect("messages.db")
        crsr = connection.cursor()
        crsr.execute("""
            DELETE FROM messages 
            WHERE date < ?;
        """, (cutoff_date,))
        deleted_count = crsr.rowcount
        connection.commit()
        connection.close()
        print(f"[TTL Cleanup] Удалено сообщений: {deleted_count}")
    except Exception as e:
        print(f"[TTL Cleanup Error] {e}")


def main():
    try:
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_bot_added_to_chat))
        app.add_handler(MessageReactionHandler(handle_reaction))
        app.add_handler(CommandHandler("resume", resume_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("auto_summary", toggle_auto_summary))
        app.add_handler(MessageHandler(filters.ALL, save_message))
        app.add_handler(CallbackQueryHandler(unified_callback_handler))


        if app.job_queue:
            cleanup_time = datetime.time(hour=4, minute=0, second=0,
                                         tzinfo=datetime.timezone(datetime.timedelta(hours=3)))
            app.job_queue.run_daily(
                cleanup_old_messages,
                time=cleanup_time,
                name="daily_db_cleanup"
            )

        print("Bot is running...")
        app.run_polling(allowed_updates=[
    Update.MESSAGE,
    Update.MESSAGE_REACTION,
    Update.CHAT_MEMBER,
    Update.MY_CHAT_MEMBER,
    Update.CALLBACK_QUERY
])
    except Exception as e:
        print(f"[Fatal Error] {e}")


if __name__ == "__main__":
    main()