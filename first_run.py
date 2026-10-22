import sqlite3
import os

DB_NAME = "messages.db"


def init_database():
    print(1)  # Заглушка визуальная или можно убрать, но для ясности:
    print(f"🔄 Проверка и инициализация базы данных ({DB_NAME})...")

    # Открываем соединение (если файла нет, SQLite создаст его автоматически)
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # 1. Таблица для хранения сообщений чата (нужна для суммаризации «Контекстом»)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Таблица участников чата (заполняется через реакции и события)
    # Использование PRIMARY KEY (chat_id, user_id) гарантирует уникальность и позволяет
    # использовать INSERT OR IGNORE без риска затереть данные.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_members (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT,
            chat_title TEXT,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

    # 3. Таблица для сохранения пользовательских настроек/конфигураций (опционально)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            target_chat_id INTEGER,
            chat_type TEXT,
            is_topic BOOLEAN DEFAULT 0,
            message_thread_id INTEGER
        )
    """)

    # Создаем индексы для ускорения поиска по чатам (безопасно для существующих индексов)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_time ON messages(chat_id, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_members_lookup ON chat_members(chat_id, user_id)")

    connection.commit()
    connection.close()

    print("✅ База данных успешно инициализирована!")
    print("🛡 Старые данные и таблицы остались в полной безопасности (ничего не удалено).")


init_database()