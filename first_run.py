import sqlite3

DB_NAME = "messages.db"


def init_database():
    print(f"🔄 Проверка и создание структуры базы данных ({DB_NAME})...")

    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # 1. Таблица участников чата
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_members (
            chat_id INTEGER,
            user_id INTEGER,
            username TEXT,
            chat_title TEXT
        )
    """)

    # 2. Таблица сообщений (с поддержкой топиков/веток и дат)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            chat_id INTEGER,
            message_thread_id INTEGER,
            username VARCHAR,
            text VARCHAR,
            date VARCHAR,
            user_id INTEGER
        )
    """)

    # 3. Таблица кэша суммаризаций (соответствует вашему формату)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summary_cache (
            chat_id INTEGER,
            message_thread_id INTEGER,
            style TEXT,
            amount_param TEXT,
            last_msg_date TEXT,
            response_text TEXT,
            created_at TEXT
        )
    """)

    connection.commit()
    connection.close()

    print("✅ Структура базы данных успешно проверена/создана!")
    print("🛡 Все существующие таблицы и старые данные не затронуты.")


init_database()