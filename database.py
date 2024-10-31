import sqlite3
import bcrypt
from datetime import datetime

DATABASE = 'startup_platform.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            role TEXT DEFAULT 'user',
            last_active DATETIME,
            ip_address TEXT,
            city TEXT,
            country TEXT,
            provider TEXT    
        )
    ''')
    conn.commit()
    conn.close()


def add_user(nickname, email, password, role='user'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        print("Пользователь с таким адресом электронной почты уже существует.")
        conn.close()
        return False
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('''
        INSERT INTO users (nickname, email, password, role) VALUES (?, ?, ?, ?)
    ''', (nickname, email, hashed_password.decode('utf-8'), role))
    conn.commit()
    conn.close()
    return True


def get_user(nickname, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users WHERE nickname = ?
    ''', (nickname,))
    user = cursor.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return user
    return None


def update_user(user_id, new_nickname):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET nickname = ?
        WHERE id = ?
    ''', (new_nickname, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        print("Ошибка: user_id должен быть целым числом.")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM users
        WHERE id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()
