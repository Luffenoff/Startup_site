import sqlite3
import bcrypt
from datetime import datetime

DATABASE = 'startup_platform.db'


def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Ошибка подключения к БД {e}")
        return None


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


def create_startup_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS startups(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       description TEXT NOT NULL,
                       image_path TEXT,
                       submission_date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                       user_id INTEGER,
                       FOREIGN KEY (user_id) REFERENCES users(id)
                   )
                ''')
    conn.commit()
    conn.close()
    
    
def create_logs_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS logs (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id INTEGER,
                       action TEXT,
                       details TEXT,
                       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                   )
            ''')
    conn.commit()
    conn.close()


def create_startup_submission_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS startup_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    startup_id INTEGER,
                    user_id INTEGER,
                    moderation_status TEXT DEFAULT 'На модерации',
                    FOREIGN KEY (startup_id) REFERENCES startups(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
    conn.commit()
    conn.close()


def log_action(user_id, action, details):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   INSERT INTO logs (user_id, action, details)
                   VALUES (?, ?, ?)
                   ''', (user_id, action, details))
    conn.commit()
    conn.close()


def add_user(nickname, email, password, role='user'):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users where nickname = ?", (nickname,))
    existing_nickname = cursor.fetchall()
    if existing_nickname:
        print("Пользователь с таким ником уже существует.")
        conn.close()
        return False
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    existing_email = cursor.fetchone()
    if existing_email:
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


def update_user(user_id, new_nickname=None, new_email=None, new_role=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    update_data = []
    query = 'UPDATE users SET'
    if new_nickname:
        query += ' nickname = ?, '
        update_data.append(new_nickname)
    if new_email:
        query += 'email = ?,'
        update_data.append(new_email)
    if new_role:
        query += 'role = ?,'
        update_data.append(new_role)
    query = query.rstrip(',')
    query += ' WHERE id = ?'
    update_data.append(user_id)
    
    cursor.execute(query, tuple(update_data))
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
    conn.close()


def is_admin(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user and user['role'] == 'admin'


def main():
    get_db_connection()
    create_table()
    create_startup_table()
    create_logs_table()
    create_startup_submission_table()


if __name__ == '__main__':
    main()