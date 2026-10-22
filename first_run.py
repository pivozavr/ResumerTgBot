import sqlite3

connection = sqlite3.connect("messages.db")
crsr = connection.cursor()

# Забираем абсолютно всех уникальных пользователей из истории сообщений для каждого чата
crsr.execute("""
    INSERT OR IGNORE INTO chat_members (chat_id, user_id, username, chat_title)
    SELECT DISTINCT chat_id, user_id, username, 'Группа ' || chat_id 
    FROM messages 
    WHERE user_id IS NOT NULL AND username IS NOT NULL;
""")

connection.commit()

# Посмотрим, сколько всего записей связей «чат-участник» теперь в базе
crsr.execute("SELECT COUNT(*) FROM chat_members;")
total_members = crsr.fetchone()[0]

connection.close()

print(f"✅ Успешно! Собрано и записано уникальных связей участников с чатами: {total_members}")