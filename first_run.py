import sqlite3

DB_NAME = "messages.db"


def init_database():
    print(f"🔄 Проверка и миграция структуры базы данных ({DB_NAME})...")

    with sqlite3.connect(DB_NAME) as connection:
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

        # 2. Таблица сообщений
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

        # 3. Таблица кэша суммаризаций
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

        # 4. Таблица веток (с поддержкой названия thread_name)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_threads (
                chat_id INTEGER,
                thread_id INTEGER,
                thread_name TEXT,
                PRIMARY KEY (chat_id, thread_id)
            )
        """)

        # --- БЕЗОПАСНЫЕ МИГРАЦИИ (Добавление недостающих колонок в старые таблицы) ---

        # Проверяем колонку user_id в messages
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN user_id INTEGER")
            print("➕ Добавлена колонка user_id в таблицу messages")
        except sqlite3.OperationalError:
            pass  # Колонка уже есть

        # Проверяем колонку message_thread_id в messages
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN message_thread_id INTEGER")
            print("➕ Добавлена колонка message_thread_id в таблицу messages")
        except sqlite3.OperationalError:
            pass

        # Проверяем колонку thread_name в chat_threads
        try:
            cursor.execute("ALTER TABLE chat_threads ADD COLUMN thread_name TEXT")
            print("➕ Добавлена колонка thread_name в таблицу chat_threads")
        except sqlite3.OperationalError:
            pass

        connection.commit()

    print("✅ Структура базы данных успешно проверена и актуализирована!")


if __name__ == "__main__":
    init_database()