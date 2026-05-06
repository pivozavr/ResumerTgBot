import sqlite3

connection = sqlite3.connect("messages.db")
crsr = connection.cursor()
sql_command = """CREATE TABLE messages (
                chat_id INTEGER,
                message_thread_id INTEGER,
                username VARCHAR(20),
                text VARCHAR(65535),
                date VARCHAR(65535));"""
crsr.execute(sql_command)
connection.commit()
connection.close()