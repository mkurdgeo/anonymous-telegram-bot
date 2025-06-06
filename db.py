import sqlite3

conn = sqlite3.connect("chatbot.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    blocked INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS chats (
    user1 INTEGER,
    user2 INTEGER,
    active INTEGER DEFAULT 1
)
''')

conn.commit()
conn.close()
