import sqlite3
import logging


def set_user_locale(user_id: int, locale: str):
    logging.info(f"Добавление/обновление пользователя {user_id} -> {locale}") 
    with sqlite3.connect("birthdays.db") as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_locales (
                user_id INTEGER PRIMARY KEY,
                locale TEXT
            )
        """)
        cur.execute("REPLACE INTO user_locales (user_id, locale) VALUES (?, ?)", (user_id, locale))
        conn.commit()

def get_user_locale(user_id: int) -> str:
    with sqlite3.connect("birthdays.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT locale FROM user_locales WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else None

def init_db():
    with sqlite3.connect("birthdays.db") as conn:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS birthdays
                       (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, date TEXT, note TEXT, contact TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS user_locales
                       (user_id INTEGER PRIMARY KEY, locale TEXT)''')
        conn.commit()

def add_birthday(user_id, name, date, note='', contact=''):
    with sqlite3.connect("birthdays.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO birthdays (user_id, name, date, note, contact) VALUES (?, ?, ?, ?, ?)",
                    (user_id, name, date, note, contact))
        conn.commit()

def get_birthdays(user_id):
    with sqlite3.connect("birthdays.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, date FROM birthdays WHERE user_id = ? ORDER BY date", (user_id,))
        return [dict(name=row[0], date=row[1]) for row in cur.fetchall()]

def delete_birthday(user_id, name):
    with sqlite3.connect("birthdays.db") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM birthdays WHERE user_id = ? AND name = ?", (user_id, name))
        return cur.rowcount > 0

def edit_birthday(user_id, name, new_date):
    with sqlite3.connect("birthdays.db") as conn:
        cur = conn.cursor()
        cur.execute("UPDATE birthdays SET date = ? WHERE user_id = ? AND name = ?", (new_date, user_id, name))
        return cur.rowcount > 0
